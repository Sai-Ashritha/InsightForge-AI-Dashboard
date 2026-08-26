"""
Email service for InsightForge AI.
Sends OTP codes via Gmail SMTP.
"""
import logging
import os
import random
import smtplib
import string
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"


def _get_smtp_config():
    if ENV_PATH.exists():
        load_dotenv(dotenv_path=ENV_PATH, override=True)

    host     = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port     = int(os.getenv("SMTP_PORT", "587"))
    user     = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    # Strip spaces from 16-char app password if user pasted with spaces (e.g. 'abcd efgh ijkl mnop')
    if " " in password and len(password.replace(" ", "")) == 16:
        password = password.replace(" ", "")

    from_addr = os.getenv("SMTP_FROM", f"InsightForge AI <{user}>")
    exp_mins  = int(os.getenv("OTP_EXPIRE_MINUTES", "10"))

    is_ready = bool(
        user
        and password
        and "@" in user
        and "your-" not in user.lower()
        and "your-" not in password.lower()
    )

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "from_addr": from_addr,
        "exp_mins": exp_mins,
        "is_ready": is_ready,
    }


def generate_otp(length: int = 6) -> str:
    """Generate a secure numeric OTP."""
    return "".join(random.choices(string.digits, k=length))


def otp_expiry() -> datetime:
    cfg = _get_smtp_config()
    return datetime.now(timezone.utc) + timedelta(minutes=cfg["exp_mins"])


def is_smtp_configured() -> bool:
    return _get_smtp_config()["is_ready"]


def _build_html(otp: str, purpose: str, email: str, exp_mins: int) -> str:
    verb = "verify your email address" if purpose == "verify" else "reset your password"
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Segoe UI',Arial,sans-serif;background:#0f172a;padding:24px}}
  .w{{max-width:520px;margin:0 auto;background:#1e293b;border-radius:20px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,0.5)}}
  .h{{background:linear-gradient(135deg,#6366f1 0%,#818cf8 100%);padding:36px 32px;text-align:center}}
  .h .logo{{font-size:32px;margin-bottom:8px}}
  .h h1{{color:#fff;font-size:22px;font-weight:700;letter-spacing:-0.5px}}
  .h p{{color:rgba(255,255,255,0.75);font-size:13px;margin-top:6px}}
  .b{{padding:36px 32px}}
  .b p{{color:#94a3b8;font-size:14px;line-height:1.7;margin-bottom:16px}}
  .otp{{background:#0f172a;border:2px solid #6366f1;border-radius:16px;text-align:center;padding:28px 24px;margin:24px 0}}
  .otp .digits{{font-size:46px;letter-spacing:14px;font-weight:800;color:#818cf8;font-family:'Courier New',monospace;display:block}}
  .otp .exp{{font-size:12px;color:#64748b;margin-top:10px}}
  .note{{background:#0f172a;border-radius:10px;padding:14px 16px;font-size:12px;color:#475569;border-left:3px solid #334155}}
  .f{{padding:20px 32px;border-top:1px solid #334155;font-size:11px;color:#475569;text-align:center}}
</style></head>
<body>
<div class="w">
  <div class="h">
    <div class="logo">🏭</div>
    <h1>InsightForge AI</h1>
    <p>Predictive Manufacturing Intelligence Platform</p>
  </div>
  <div class="b">
    <p>Hello,</p>
    <p>You requested to <strong style="color:#e2e8f0">{verb}</strong> for the account associated with:</p>
    <p style="color:#6366f1;font-weight:600">{email}</p>
    <p>Enter this 6-digit code in the app:</p>
    <div class="otp">
      <span class="digits">{otp}</span>
      <div class="exp">⏱ This code expires in <strong>{exp_mins} minutes</strong></div>
    </div>
    <div class="note">🔒 If you didn't request this code, you can safely ignore this email. Your account is not at risk.</div>
  </div>
  <div class="f">&copy; 2026 InsightForge AI &mdash; Secure Manufacturing Intelligence</div>
</div>
</body></html>"""


def send_otp_email(to_email: str, otp: str, purpose: str = "verify") -> tuple[bool, bool]:
    """
    Send an OTP email via SMTP.
    Returns tuple: (success: bool, is_real_smtp: bool)
    """
    cfg = _get_smtp_config()
    subjects = {
        "verify": "InsightForge AI — Your Email Verification Code",
        "reset":  "InsightForge AI — Your Password Reset Code",
    }
    subject = subjects.get(purpose, "InsightForge AI — Your Verification Code")

    if not cfg["is_ready"]:
        bar = "=" * 62
        msg = (
            f"\n{bar}\n"
            f"  📧  INSIGHTFORGE OTP  [{purpose.upper()}]\n"
            f"  To:      {to_email}\n"
            f"  Code:    {otp}\n"
            f"  Expires: {cfg['exp_mins']} minutes\n"
            f"  [Notice: SMTP_USER / SMTP_PASSWORD in .env still placeholder]\n"
            f"{bar}\n"
        )
        print(msg)
        logger.warning(msg)
        return False, False

    # ── Real SMTP send ───────────────────────────────────────────────────────
    try:
        html_body  = _build_html(otp, purpose, to_email, cfg["exp_mins"])
        plain_body = (
            f"Your InsightForge AI code: {otp}\n"
            f"Purpose: {purpose}\n"
            f"Expires in: {cfg['exp_mins']} minutes\n\n"
            "If you didn't request this, ignore this email."
        )

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = cfg["from_addr"] if cfg["from_addr"] != f"InsightForge AI <>" else f"InsightForge AI <{cfg['user']}>"
        msg["To"]      = to_email
        msg.attach(MIMEText(plain_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(cfg["user"], cfg["password"])
            server.sendmail(cfg["user"], to_email, msg.as_string())

        logger.info(f"OTP email sent successfully ✓ to={to_email}, purpose={purpose}")
        print(f"\n✓ OTP Email successfully sent to {to_email}\n")
        return True, True

    except smtplib.SMTPAuthenticationError as auth_err:
        logger.error(f"SMTP authentication failed for {cfg['user']}: {auth_err}")
        print(f"\n[SMTP AUTH ERROR] Failed to authenticate with {cfg['user']}. Check SMTP_USER & SMTP_PASSWORD in .env\n")
        return False, False
    except Exception as exc:
        logger.error(f"Failed to send OTP to {to_email}: {exc}")
        print(f"\n[SMTP ERROR] Failed to send email to {to_email}: {exc}\n")
        return False, False


