"""
Authentication Manager
=======================
Simple local auth with hashed passwords (PBKDF2-SHA256) and JSON storage.
No external dependencies — uses Python stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path


# Avatar color palette
_AVATAR_COLORS = [
    "#6C63FF", "#FF6B9D", "#00D9FF", "#48BB78",
    "#F6AD55", "#9F7AEA", "#FC8181", "#4FD1C5",
    "#F687B3", "#63B3ED", "#68D391", "#FBD38D",
]


class AuthManager:
    """Manages user registration, login, and profile storage."""

    def __init__(self, users_file: str | None = None):
        if users_file is None:
            self.users_file = Path(__file__).resolve().parent / "users.json"
        else:
            self.users_file = Path(users_file)
        self._ensure_file()

    # ── Internal helpers ──────────────────────────────────────

    def _ensure_file(self):
        self.users_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.users_file.exists():
            self.users_file.write_text("{}", encoding="utf-8")

    def _load(self) -> dict:
        return json.loads(self.users_file.read_text(encoding="utf-8"))

    def _save(self, users: dict):
        self.users_file.write_text(
            json.dumps(users, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    @staticmethod
    def _hash_pw(password: str, salt: bytes | None = None) -> str:
        if salt is None:
            salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
        return salt.hex() + ":" + key.hex()

    @staticmethod
    def _verify_pw(password: str, stored: str) -> bool:
        salt_hex, key_hex = stored.split(":")
        salt = bytes.fromhex(salt_hex)
        key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
        return key.hex() == key_hex

    # ── Public API ────────────────────────────────────────────

    def register(
        self,
        username: str,
        password: str,
        display_name: str | None = None,
    ) -> dict:
        """Register a new user. Returns ``{success, message}``."""
        if not username or not password:
            return {"success": False, "message": "Username and password are required."}
        if len(username) < 3:
            return {"success": False, "message": "Username must be ≥ 3 characters."}
        if len(password) < 4:
            return {"success": False, "message": "Password must be ≥ 4 characters."}

        users = self._load()
        key = username.lower().strip()
        if key in users:
            return {"success": False, "message": "Username already exists."}

        color = _AVATAR_COLORS[len(users) % len(_AVATAR_COLORS)]
        users[key] = {
            "password_hash": self._hash_pw(password),
            "display_name": (display_name or username).strip(),
            "avatar_color": color,
            "created_at": datetime.now().isoformat(),
        }
        self._save(users)
        return {"success": True, "message": "Account created successfully!"}

    def login(self, username: str, password: str) -> dict:
        """Validate credentials. Returns ``{success, message, user?}``."""
        users = self._load()
        key = username.lower().strip()
        user = users.get(key)
        if not user or not self._verify_pw(password, user["password_hash"]):
            return {"success": False, "message": "Invalid username or password."}
        return {
            "success": True,
            "message": "Welcome back!",
            "user": {
                "username": key,
                "display_name": user["display_name"],
                "avatar_color": user["avatar_color"],
                "created_at": user["created_at"],
            },
        }

    def get_user(self, username: str) -> dict | None:
        """Return a user profile dict (without password), or None."""
        users = self._load()
        user = users.get(username.lower().strip())
        if not user:
            return None
        return {
            "username": username.lower().strip(),
            "display_name": user["display_name"],
            "avatar_color": user["avatar_color"],
            "created_at": user["created_at"],
        }
