import os
import urllib.parse
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


def _database_url() -> str:
    value = os.getenv("DATABASE_URL")
    if value:
        return value.replace("postgresql+psycopg://", "postgresql+psycopg2://", 1)

    user = urllib.parse.quote_plus(os.getenv("POSTGRES_USER", "postgres"))
    password = urllib.parse.quote_plus(os.getenv("POSTGRES_PASSWORD", "Project@123"))
    host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "insightforge")

    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}"


engine = create_engine(_database_url(), pool_pre_ping=True, pool_recycle=300)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="analyst")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class OTPCode(Base):
    """Stores one-time password codes for email verification and password reset."""
    __tablename__ = "otp_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    code: Mapped[str] = mapped_column(String(10))
    purpose: Mapped[str] = mapped_column(String(20))  # 'verify' | 'reset'
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


def initialize_orm() -> None:
    Base.metadata.create_all(bind=engine)
    # Safe schema migration for existing PostgreSQL users table
    with engine.begin() as conn:
        from sqlalchemy import text
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(255);"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE;"))



def orm_get_user_by_email(email: str):
    with SessionLocal() as session:
        return session.query(User).filter(User.email == email.lower().strip()).first()


def orm_create_user(
    email: str,
    hashed_password: str,
    role: str = "analyst",
    full_name: Optional[str] = None,
    is_verified: bool = False,
):
    with SessionLocal() as session:
        user = User(
            email=email.lower().strip(),
            hashed_password=hashed_password,
            role=role,
            full_name=full_name,
            is_verified=is_verified,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def orm_activate_user(email: str) -> None:
    """Mark user as verified and active after OTP confirmation."""
    with SessionLocal() as session:
        user = session.query(User).filter(User.email == email.lower().strip()).first()
        if user:
            user.is_verified = True
            user.is_active = True
            session.commit()


def orm_update_password(email: str, hashed_password: str) -> None:
    """Update user's hashed password."""
    with SessionLocal() as session:
        user = session.query(User).filter(User.email == email.lower().strip()).first()
        if user:
            user.hashed_password = hashed_password
            session.commit()


# ── OTP helpers ──────────────────────────────────────────────────────────────

def orm_save_otp(email: str, code: str, purpose: str, expires_at: datetime) -> None:
    """Invalidate previous codes for same email+purpose and save new one."""
    with SessionLocal() as session:
        # Mark all previous codes for this email+purpose as used
        session.query(OTPCode).filter(
            OTPCode.email == email.lower().strip(),
            OTPCode.purpose == purpose,
            OTPCode.used == False,  # noqa: E712
        ).update({"used": True})
        otp = OTPCode(
            email=email.lower().strip(),
            code=code,
            purpose=purpose,
            expires_at=expires_at,
        )
        session.add(otp)
        session.commit()


def orm_verify_otp(email: str, code: str, purpose: str) -> bool:
    """Validate an OTP code. Returns True if valid and not expired. Marks it used."""
    from datetime import timezone
    with SessionLocal() as session:
        otp = (
            session.query(OTPCode)
            .filter(
                OTPCode.email == email.lower().strip(),
                OTPCode.code == code,
                OTPCode.purpose == purpose,
                OTPCode.used == False,  # noqa: E712
            )
            .order_by(OTPCode.created_at.desc())
            .first()
        )
        if not otp:
            return False
        # Compare timezone-aware datetimes
        now = datetime.now(timezone.utc)
        expires = otp.expires_at
        if expires.tzinfo is None:
            from datetime import timezone as tz
            expires = expires.replace(tzinfo=tz.utc)
        if now > expires:
            return False
        otp.used = True
        session.commit()
        return True

