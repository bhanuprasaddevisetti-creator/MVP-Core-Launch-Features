import datetime as dt
import logging
from typing import Any

import reflex as rx
from sqlalchemy import select
from app.models import User, UserRole, FarmerProfile
from app.security import hash_password, verify_password


class AuthState(rx.State):
    email: str = ""
    password: str = ""
    full_name: str = ""
    selected_role: str = "customer"
    user_id: int = 0
    role: str = ""
    language: str = "en"
    mode: str = "login"
    loading: bool = False
    error: str = ""
    message: str = ""

    @rx.event
    def set_email(self, value: str):
        self.email = value.strip().lower()

    @rx.event
    def set_password(self, value: str):
        self.password = value

    @rx.event
    def set_name(self, value: str):
        self.full_name = value.strip()

    @rx.event
    def set_role(self, value: str):
        self.selected_role = value

    @rx.event
    def set_language(self, value: str):
        self.language = value

    @rx.event
    def toggle_mode(self):
        self.mode = "signup" if self.mode == "login" else "login"
        self.error = ""
        self.message = ""

    @rx.event
    def submit_form(self, form_data: dict[str, Any]):
        """Bind the submitted credentials, then authenticate and navigate."""
        self.email = str(form_data.get("email", "")).strip().lower()
        self.password = str(form_data.get("password", ""))
        name = str(form_data.get("full_name", "")).strip()
        if name:
            self.full_name = name
        role = str(form_data.get("role", "")).strip()
        if role in {"customer", "farmer"}:
            self.selected_role = role
        yield AuthState.submit
        yield AuthState.after_auth

    @rx.event
    def after_auth(self):
        """Route the signed-in account to the surface it belongs on."""
        if self.user_id == 0 or self.error:
            return
        self.password = ""
        if self.role == "farmer":
            return rx.redirect("/farmer/listings")
        return rx.redirect("/marketplace")

    @rx.event
    async def submit(self):
        self.loading = True
        self.error = ""
        self.message = ""
        try:
            if (
                not self.email
                or "@" not in self.email
                or len(self.password) < 8
            ):
                self.error = "Enter a valid email and a password of at least 8 characters."
                return
            async with rx.asession() as session:
                user = await session.scalar(
                    select(User).where(User.email == self.email)
                )
                if self.mode == "login":
                    if user is None or not verify_password(
                        self.password, user.password_hash
                    ):
                        self.error = "Email or password was not recognised."
                        return
                    user.last_login_at = dt.datetime.now(dt.timezone.utc)
                else:
                    if user is not None:
                        self.error = (
                            "An account with this email already exists."
                        )
                        return
                    existing = await session.scalar(select(User.id).limit(1))
                    role = (
                        UserRole.ADMIN
                        if existing is None
                        else UserRole(self.selected_role)
                    )
                    user = User(
                        email=self.email,
                        password_hash=hash_password(self.password),
                        full_name=self.full_name,
                        role=role,
                        language_pref=self.language,
                    )
                    session.add(user)
                    await session.flush()
                    if role is UserRole.FARMER:
                        session.add(
                            FarmerProfile(
                                user_id=user.id,
                                display_name=self.full_name,
                                display_name_te=self.full_name,
                                verification_note="Profile awaiting verification.",
                            )
                        )
                await session.commit()
                self.user_id = int(user.id)
                self.role = user.role.value
                self.message = (
                    "Welcome back."
                    if self.mode == "login"
                    else "Account created successfully."
                )
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.error = "We could not complete that request. Please try again."
        finally:
            self.loading = False

    @rx.event
    def logout(self):
        self.user_id = 0
        self.role = ""
        self.password = ""
        self.mode = "login"
        self.message = "You have been signed out."
        return rx.redirect("/login")
