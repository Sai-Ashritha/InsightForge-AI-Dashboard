import os
import urllib.parse
from datetime import datetime

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
    role: Mapped[str] = mapped_column(String(20), default="analyst")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


def initialize_orm() -> None:
    Base.metadata.create_all(bind=engine)


def orm_get_user_by_email(email: str):
    with SessionLocal() as session:
        return session.query(User).filter(User.email == email.lower().strip()).first()


def orm_create_user(email: str, hashed_password: str, role: str = "analyst"):
    with SessionLocal() as session:
        user = User(email=email.lower().strip(), hashed_password=hashed_password, role=role)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

