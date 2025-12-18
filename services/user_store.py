import os
import uuid
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, EmailStr, Field, ValidationError, field_validator
from werkzeug.security import check_password_hash, generate_password_hash

from config import USERS_JSON_PATH
from services.atomic_storage import AtomicJSONStorage

DEFAULT_ADMIN_EMAIL = "admin@tracklistify.com"
DEFAULT_ADMIN_PASSWORD = "123456"

# Load environment variables (.env) immediately
load_dotenv()

class User(BaseModel):
    id: str
    email: EmailStr
    hashed_password: str
    name: str | None = None
    dj_name: str | None = None
    avatar_url: str | None = None
    soundcloud_url: str | None = None
    is_admin: bool = False
    favorites: List[str] = Field(default_factory=list)

    model_config = {
        "extra": "ignore",
    }


class LoginPayload(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Password erforderlich")
        return value


class RegisterPayload(LoginPayload):
    name: str | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        if len(value.strip()) < 6:
            raise ValueError("Passwort muss mindestens 6 Zeichen haben")
        return value


class ProfileUpdatePayload(BaseModel):
    name: str | None = None
    dj_name: str | None = None
    avatar_url: str | None = None
    soundcloud_url: str | None = None


class InvitePayload(BaseModel):
    email: EmailStr
    name: str | None = None
    is_admin: bool = False


class FavoriteTogglePayload(BaseModel):
    item_id: str

    @field_validator("item_id")
    @classmethod
    def validate_item(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("item_id erforderlich")
        return value


class UserStore:
    def __init__(self, storage_path: str = USERS_JSON_PATH):
        self._storage = AtomicJSONStorage(storage_path)
        self._storage.ensure_file([])

    def _load_users(self) -> List[User]:
        data = self._storage.read(default=[])
        users: List[User] = []
        for raw in data:
            try:
                users.append(User.model_validate(raw))
            except ValidationError:
                continue
        return users

    def _save_users(self, users: List[User]) -> None:
        self._storage.write([user.model_dump() for user in users])

    def list_users(self) -> List[User]:
        return self._load_users()

    def _find_index_by_id(self, users: List[User], user_id: str) -> Optional[int]:
        for idx, user in enumerate(users):
            if user.id == user_id:
                return idx
        return None

    def get_by_email(self, email: str) -> Optional[User]:
        normalized = email.lower().strip()
        for user in self._load_users():
            if user.email.lower() == normalized:
                return user
        return None

    def get_by_id(self, user_id: str) -> Optional[User]:
        for user in self._load_users():
            if user.id == user_id:
                return user
        return None

    def add_user(
        self,
        email: str,
        password: str,
        name: str | None = None,
        dj_name: str | None = None,
        avatar_url: str | None = None,
        soundcloud_url: str | None = None,
        is_admin: bool = False,
    ) -> User:
        existing = self.get_by_email(email)
        if existing:
            raise ValueError("User existiert bereits")

        user = User(
            id=str(uuid.uuid4()),
            email=email.strip(),
            hashed_password=generate_password_hash(password.strip()),
            name=name,
            dj_name=dj_name,
            avatar_url=avatar_url,
            soundcloud_url=soundcloud_url,
            is_admin=is_admin,
            favorites=[],
        )
        users = self._load_users()
        users.append(user)
        self._save_users(users)
        return user

    def authenticate(self, email: str, password: str) -> Optional[User]:
        user = self.get_by_email(email)
        if user and check_password_hash(user.hashed_password, password):
            return user
        return None

    def update_user(self, user_id: str, updates: dict) -> Optional[User]:
        users = self._load_users()
        idx = self._find_index_by_id(users, user_id)
        if idx is None:
            return None

        user = users[idx]
        for key in ["name", "dj_name", "avatar_url", "soundcloud_url"]:
            if key in updates:
                setattr(user, key, updates.get(key))

        if "password" in updates and updates["password"]:
            user.hashed_password = generate_password_hash(str(updates["password"]))

        if "is_admin" in updates:
            user.is_admin = bool(updates.get("is_admin"))

        users[idx] = user
        self._save_users(users)
        return user

    def toggle_favorite(self, user_id: str, item_id: str) -> Optional[bool]:
        users = self._load_users()
        idx = self._find_index_by_id(users, user_id)
        if idx is None:
            return None

        user = users[idx]
        favorites = set(user.favorites or [])
        if item_id in favorites:
            favorites.remove(item_id)
            changed = False
        else:
            favorites.add(item_id)
            changed = True

        user.favorites = list(favorites)
        users[idx] = user
        self._save_users(users)
        return changed

    def delete_user(self, user_id: str) -> bool:
        users = self._load_users()
        idx = self._find_index_by_id(users, user_id)
        if idx is None:
            return False
        users.pop(idx)
        self._save_users(users)
        return True

    def _ensure_admin_account(self, email: str, password: str) -> Optional[User]:
        existing = self.get_by_email(email)

        if existing:
            requires_save = False

            if password and not check_password_hash(existing.hashed_password, password):
                existing.hashed_password = generate_password_hash(password.strip())
                requires_save = True

            if not existing.is_admin:
                existing.is_admin = True
                requires_save = True

            if requires_save:
                users = self._load_users()
                idx = self._find_index_by_id(users, existing.id)
                if idx is not None:
                    users[idx] = existing
                    self._save_users(users)
            return existing

        try:
            return self.add_user(email, password, name="Admin", is_admin=True)
        except ValueError:
            return self.get_by_email(email)

    def ensure_default_admin(self) -> User:
        # Lade Credentials aus .env oder nutze Fallback (nur lokal sicher)
        raw_email = os.getenv("ADMIN_EMAIL")
        raw_password = os.getenv("ADMIN_PASSWORD")

        class _AdminEmailModel(BaseModel):
            email: EmailStr

        try:
            env_email = _AdminEmailModel(email=raw_email).email if raw_email else None
        except ValidationError:
            env_email = None

        env_password = raw_password.strip() if raw_password and raw_password.strip() else None

        admin_targets = []
        if env_email:
            admin_targets.append((env_email, env_password or DEFAULT_ADMIN_PASSWORD))
        admin_targets.append((DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD))

        ensured_admin: Optional[User] = None
        seen = set()

        for email, password in admin_targets:
            if not email or email in seen:
                continue
            seen.add(email)
            candidate = self._ensure_admin_account(email, password)
            if ensured_admin is None and candidate is not None:
                ensured_admin = candidate

        # Fallback: Wenn nichts angelegt werden konnte, versuche den Default
        if ensured_admin:
            return ensured_admin
        return self._ensure_admin_account(DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD)
