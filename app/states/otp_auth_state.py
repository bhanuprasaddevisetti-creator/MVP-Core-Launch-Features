import datetime as dt
import hashlib
import os
import random
import re

import reflex as rx
from sqlalchemy import select

from app.db import get_session
from app.models import OtpCode, User, UserRole

OTP_TTL_MINUTES = 10
OTP_LENGTH = 6

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?[0-9]{10,15}$")


ADMIN_IDENTIFIERS = {
    x.strip().lower()
    for x in os.environ.get("ADMIN_IDENTIFIERS", "").split(",")
    if x.strip()
}




def _hash_code(code: str, identifier: str) -> str:
    return hashlib.sha256(f"{identifier}:{code}".encode()).hexdigest()


def _generate_code() -> str:
    return f"{random.randint(0, 10 ** OTP_LENGTH - 1):0{OTP_LENGTH}d}"


def _send_otp(identifier: str, code: str) -> None:
    """Wire a real email/SMS provider here. Falls back to logging."""
    if "@" in identifier:
        _send_email_otp(identifier, code)
    else:
        _send_sms_otp(identifier, code)


def _send_email_otp(email: str, code: str) -> None:
    smtp_host = os.environ.get("SMTP_HOST")
    if not smtp_host:
        print(f"[DEV OTP] {email}: {code}")
        return
    import smtplib
    from email.mime.text import MIMEText

    msg = MIMEText(
        f"Your Rythu Mithra sign-in code is {code}. "
        f"It expires in {OTP_TTL_MINUTES} minutes."
    )
    msg["Subject"] = "Your sign-in code"
    msg["From"] = os.environ.get("SMTP_FROM", "no-reply@rythumithra.app")
    msg["To"] = email
    with smtplib.SMTP(smtp_host, int(os.environ.get("SMTP_PORT", "587"))) as server:
        server.starttls()
        server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        server.send_message(msg)


def _send_sms_otp(phone: str, code: str) -> None:
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    if not account_sid:
        print(f"[DEV OTP] {phone}: {code}")
        return
    from twilio.rest import Client

    client = Client(account_sid, os.environ["TWILIO_AUTH_TOKEN"])
    client.messages.create(
        body=f"Your Rythu Mithra sign-in code is {code}.",
        from_=os.environ["TWILIO_FROM_NUMBER"],
        to=phone,
    )


class OtpAuthState(rx.State):
    identifier: str = ""
    otp_input: str = ""
    step: str = "identifier"
    error: str = ""

    session_user_id: int = rx.Cookie(0, name="rm_uid")
    session_role: str = rx.Cookie("", name="rm_role")

    @rx.var
    def is_authenticated(self) -> bool:
        return self.session_user_id > 0

    @rx.var
    def is_admin(self) -> bool:
        return self.session_role == UserRole.ADMIN.value

    def set_identifier(self, value: str):
        self.identifier = value.strip()

    def set_otp_input(self, value: str):
        self.otp_input = value.strip()

    def go_back(self):
        self.step = "identifier"
        self.error = ""
        self.otp_input = ""

    def request_otp(self):
        identifier = self.identifier.strip().lower()
        if not (EMAIL_RE.match(identifier) or PHONE_RE.match(identifier)):
            self.error = "Enter a valid email or 10-digit mobile number."
            return
        self.error = ""
        code = _generate_code()
        expires_at = dt.datetime.now(dt.timezone.utc) + dt.timedelta(
            minutes=OTP_TTL_MINUTES
        )
        with get_session() as session:
            session.add(
                OtpCode(
                    identifier=identifier,
                    code_hash=_hash_code(code, identifier),
                    purpose="login",
                    expires_at=expires_at,
                )
            )
            session.commit()
        _send_otp(identifier, code)
        self.identifier = identifier
        self.step = "otp"

    def verify_otp(self):
        identifier = self.identifier
        code = self.otp_input.strip()
        if not code:
            self.error = "Enter the code we sent you."
            return

        with get_session() as session:
            stmt = (
                select(OtpCode)
                .where(OtpCode.identifier == identifier)
                .where(OtpCode.consumed_at.is_(None))
                .order_by(OtpCode.created_at.desc())
            )
            otp = session.execute(stmt).scalars().first()

            if otp is None or otp.expires_at < dt.datetime.now(dt.timezone.utc):
                self.error = "Code expired. Request a new one."
                return
            if otp.attempts >= 5:
                self.error = "Too many attempts. Request a new code."
                return
            if _hash_code(code, identifier) != otp.code_hash:
                otp.attempts += 1
                session.commit()
                self.error = "Incorrect code."
                return

            otp.consumed_at = dt.datetime.now(dt.timezone.utc)
            session.commit()

            is_email = "@" in identifier
            user_stmt = select(User).where(
                User.email == identifier if is_email else User.phone == identifier
            )
            user = session.execute(user_stmt).scalars().first()

            if user is None:
                placeholder_email = (
                    identifier if is_email else f"{identifier}@otp.rythumithra.app"
                )
                user = User(
                    email=placeholder_email,
                    password_hash=_hash_code(os.urandom(16).hex(), identifier).ljust(
                        32, "0"
                    ),
                    phone="" if is_email else identifier,
                    role=UserRole.CUSTOMER,
                )
                session.add(user)
                session.commit()
                session.refresh(user)

            user.last_login_at = dt.datetime.now(dt.timezone.utc)
            session.commit()

            self.session_user_id = user.id
            self.session_role = user.role.value

        self.error = ""
        self.otp_input = ""
        self.step = "identifier"
        return rx.redirect("/")

    def logout(self):
        self.session_user_id = 0
        self.session_role = ""
        return rx.redirect("/login")

    def guard_admin(self):
        if not self.is_admin:
            return rx.redirect("/login")
