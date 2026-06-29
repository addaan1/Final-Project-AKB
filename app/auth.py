"""Authentication module: user model, session, OAuth, demo login."""
from __future__ import annotations

import json
import os
import secrets
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Optional

from flask import (
    current_app,
    flash,
    g,
    jsonify,
    redirect,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash


# =================================================================
# USER MODEL
# =================================================================
def _default_user_usage() -> dict:
    """Module-level default for User.usage (used by dataclass field & _user_from_dict)."""
    return {
        "chat_count": 0,
        "chat_reset_date": "",
        "dc_attempts": 0,
        "dc_reset_date": "",
        "saved_items": [],
    }


@dataclass
class User:
    """User model: id, email, name, avatar, package, source, created_at."""
    id: str
    email: str
    name: str
    avatar_url: str = ""
    package: str = "free"  # 'free' | 'premium'
    source: str = "demo"  # 'demo' | 'google' | 'register'
    password_hash: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat() + "Z")
    # Round 13/17: usage tracking for free tier limits
    usage: dict = field(default_factory=_default_user_usage)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "avatar_url": self.avatar_url,
            "package": self.package,
            "source": self.source,
            "created_at": self.created_at,
            "usage": self.usage,
        }

    @property
    def is_premium(self) -> bool:
        return self.package == "premium"

    @property
    def is_free(self) -> bool:
        return self.package == "free"

    @property
    def initial(self) -> str:
        if not self.name:
            return self.email[0].upper() if self.email else "?"
        return self.name[0].upper()


# =================================================================
# USER STORAGE (JSON file)
# =================================================================
USERS_FILE = Path("data/users.json")


def _load_users() -> list:
    """Load users from JSON file."""
    if not USERS_FILE.exists():
        return []
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _save_users(users: list) -> None:
    """Save users to JSON file."""
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    USERS_FILE.write_text(
        json.dumps(users, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _user_from_dict(d: dict) -> User:
    """Build User from dict, ignoring unknown fields.

    Round 17 fix: now correctly passes `usage` field to User constructor.
    Previously `usage` was silently dropped, causing rate-limit counter to
    reset to default on every request (free users could chat unlimited).
    """
    return User(
        id=d.get("id", str(uuid.uuid4())),
        email=d.get("email", ""),
        name=d.get("name", ""),
        avatar_url=d.get("avatar_url", ""),
        package=d.get("package", "free"),
        source=d.get("source", "demo"),
        password_hash=d.get("password_hash", ""),
        created_at=d.get("created_at", datetime.now().isoformat() + "Z"),
        usage=d.get("usage") or _default_user_usage(),
    )


def find_user_by_email(email: str) -> Optional[User]:
    """Find user by email (case-insensitive)."""
    if not email:
        return None
    email_lower = email.lower().strip()
    for u in _load_users():
        if u.get("email", "").lower() == email_lower:
            return _user_from_dict(u)
    return None


def find_user_by_id(user_id: str) -> Optional[User]:
    """Find user by ID."""
    if not user_id:
        return None
    for u in _load_users():
        if u.get("id") == user_id:
            return _user_from_dict(u)
    return None


def create_user(email: str, name: str, package: str = "free", source: str = "demo",
                password_hash: str = "", avatar_url: str = "") -> User:
    """Create new user (or return existing)."""
    existing = find_user_by_email(email)
    if existing:
        return existing
    user = User(
        id=str(uuid.uuid4()),
        email=email.lower().strip(),
        name=name or email.split("@")[0],
        avatar_url=avatar_url,
        package=package,
        source=source,
        password_hash=password_hash,
    )
    users = _load_users()
    users.append(asdict(user))
    _save_users(users)
    return user


def update_user_package(user_id: str, new_package: str) -> Optional[User]:
    """Update user package (free -> premium)."""
    users = _load_users()
    for i, u in enumerate(users):
        if u.get("id") == user_id:
            u["package"] = new_package
            users[i] = u
            _save_users(users)
            return _user_from_dict(u)
    return None


def update_user_data(user_id: str, data_updates: dict) -> Optional[User]:
    """Update arbitrary user fields (e.g. usage tracking)."""
    users = _load_users()
    for i, u in enumerate(users):
        if u.get("id") == user_id:
            for k, v in data_updates.items():
                u[k] = v
            users[i] = u
            _save_users(users)
            return _user_from_dict(u)
    return None


def verify_password(user: User, password: str) -> bool:
    """Verify user password (only for demo/register accounts)."""
    if not user.password_hash:
        return False
    return check_password_hash(user.password_hash, password)


# =================================================================
# DEMO SEEDING
# =================================================================
def seed_demo_users() -> None:
    """Seed demo users on first run. Idempotent."""
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing = _load_users()
    existing_emails = {u.get("email", "").lower() for u in existing}

    seed = [
        {
            "email": "demo@galbay.id",
            "name": "Demo User",
            "package": "free",
            "password": "demo123",
        },
        {
            "email": "premium@galbay.id",
            "name": "Premium Demo",
            "package": "premium",
            "password": "demo123",
        },
    ]
    changed = False
    for s in seed:
        if s["email"].lower() not in existing_emails:
            create_user(
                email=s["email"],
                name=s["name"],
                package=s["package"],
                source="demo",
                password_hash=generate_password_hash(s["password"]),
            )
            changed = True


# =================================================================
# SESSION HELPERS
# =================================================================
SESSION_KEY = "user_id"
SESSION_DURATION_DAYS = 7


def login_user(user: User) -> None:
    """Store user in session."""
    session.clear()
    session.permanent = True
    session[SESSION_KEY] = user.id
    current_app.permanent_session_lifetime = timedelta(days=SESSION_DURATION_DAYS)


def logout_user() -> None:
    """Clear user from session."""
    session.pop(SESSION_KEY, None)
    session.clear()


def get_current_user() -> Optional[User]:
    """Get current user from session (cached per request via g)."""
    if "current_user" in g.__dict__:
        return g.current_user
    user_id = session.get(SESSION_KEY)
    if not user_id:
        g.current_user = None
        return None
    user = find_user_by_id(user_id)
    g.current_user = user
    return user


# =================================================================
# DECORATORS
# =================================================================
def login_required(view):
    """Decorator: require login. Redirects to /login with ?next=..."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if get_current_user() is None:
            flash("Silakan login dulu untuk akses halaman ini.", "warning")
            return redirect(url_for("main.login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def premium_required(view):
    """Decorator: require premium package. Returns 403 JSON or redirect."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = get_current_user()
        if user is None:
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"valid": False, "error": "Login required"}), 401
            flash("Silakan login dulu.", "warning")
            return redirect(url_for("main.login", next=request.path))
        if not user.is_premium:
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({
                    "valid": False,
                    "error": "Premium feature",
                    "package_required": "premium",
                    "current_package": "free",
                }), 403
            flash("Fitur ini khusus user Premium. Upgrade untuk akses.", "warning")
            return redirect(f"{url_for('main.produk')}#pricing")
        return view(*args, **kwargs)
    return wrapped


# =================================================================
# OAUTH (Google via authlib)
# =================================================================
def is_oauth_configured() -> bool:
    """Check if Google OAuth credentials are present in env."""
    return bool(
        os.environ.get("GOOGLE_CLIENT_ID")
        and os.environ.get("GOOGLE_CLIENT_SECRET")
    )


def init_oauth(app):
    """Initialize authlib OAuth client. Idempotent."""
    from authlib.integrations.flask_client import OAuth
    oauth = OAuth(app)
    if is_oauth_configured():
        oauth.register(
            name="google",
            client_id=os.environ["GOOGLE_CLIENT_ID"],
            client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
    app.extensions["oauth"] = oauth
    return oauth
