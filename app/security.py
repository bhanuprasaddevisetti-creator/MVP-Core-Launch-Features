"""Password hashing helpers. No plaintext credential is ever stored or logged."""

from __future__ import annotations

import hashlib
import hmac
import secrets

import logging

ALGO = "pbkdf2_sha256"
ITERATIONS = 260_000
SALT_BYTES = 16


def hash_password(password: str, *, iterations: int = ITERATIONS) -> str:
    """Return a self-describing `pbkdf2_sha256$iterations$salt$hash` string."""
    if not password:
        raise ValueError("password must not be empty")
    salt = secrets.token_hex(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
    ).hex()
    return f"{ALGO}${iterations}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    """Constant-time verification of a password against a stored hash."""
    try:
        algo, raw_iterations, salt, digest = stored.split("$", 3)
        if algo != ALGO:
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(raw_iterations),
        ).hex()
    except (ValueError, AttributeError):
        logging.exception("Unexpected error")
        return False
    return hmac.compare_digest(candidate, digest)


def generate_unusable_password() -> str:
    """A random, never-disclosed secret for demo records.

    Demo accounts exist so the marketplace view is not empty; nobody can sign
    in as them because the random source password is discarded immediately.
    """
    return hash_password(secrets.token_urlsafe(32))
