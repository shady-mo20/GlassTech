"""
Flask configuration.

This project is intentionally "Windows-friendly":
- SQLite database in a local `instance/` folder (created automatically).
- No external services required.

Environment variables you may set:
- FLASK_SECRET_KEY: override secret key for production.
- FLASK_DB_PATH: override DB file path.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    # Security
    SECRET_KEY: str = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

    # Database
    DB_PATH: str = os.environ.get("FLASK_DB_PATH", os.path.join("instance", "app.sqlite3"))

    # App behavior
    DEFAULT_LANG: str = "en"
    SUPPORTED_LANGS: tuple[str, ...] = ("en", "ar")

    # Session hardening (safe defaults for local dev, improve for production)
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"


class DevConfig(Config):
    DEBUG: bool = True


class ProdConfig(Config):
    DEBUG: bool = False
    # In production you should set:
    # - SECRET_KEY (random)
    # - SESSION_COOKIE_SECURE = True (HTTPS)
    SESSION_COOKIE_SECURE: bool = bool(os.environ.get("SESSION_COOKIE_SECURE", "0") == "1")

