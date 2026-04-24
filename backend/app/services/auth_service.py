from dataclasses import dataclass
from datetime import datetime

from fastapi import HTTPException, status
from sqlite3 import IntegrityError

from app.core.config import get_settings
from app.core.security import verify_password
from app.models.schemas import LoginRequest, RegisterRequest, UserPublic
from app.storage.auth_store import AuthStore


@dataclass
class AuthSession:
    user: UserPublic
    session_token: str
    expires_at: datetime


class AuthService:
    def __init__(self, store: AuthStore):
        self.store = store
        self.settings = get_settings()

    def register(self, payload: RegisterRequest) -> AuthSession:
        if not self.settings.open_registration and self.store.count_users() > 0:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Registration is disabled")

        try:
            user = self.store.create_user(payload)
        except IntegrityError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists") from exc

        return self._create_session_for_user(user)

    def login(self, payload: LoginRequest) -> AuthSession:
        user_record = self.store.get_user_auth_by_username(payload.username)
        if not user_record or not verify_password(payload.password, user_record.password_hash, user_record.password_salt):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

        user = UserPublic(
            id=user_record.id,
            username=user_record.username,
            display_name=user_record.display_name,
            created_at=user_record.created_at,
            updated_at=user_record.updated_at,
        )
        return self._create_session_for_user(user)

    def logout(self, session_token: str | None) -> None:
        if session_token:
            self.store.delete_session(session_token)

    def get_current_user(self, session_token: str | None) -> UserPublic:
        if not session_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

        self.store.cleanup_expired_sessions()
        user = self.store.get_user_by_session(session_token)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or invalid")
        return user

    def _create_session_for_user(self, user: UserPublic) -> AuthSession:
        token, expires_at = self.store.create_session(user.id)
        return AuthSession(user=user, session_token=token, expires_at=expires_at)

