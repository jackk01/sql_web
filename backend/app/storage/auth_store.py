from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.core.config import get_settings
from app.core.database import get_connection
from app.core.security import hash_password
from app.models.schemas import RegisterRequest, UserAuthRecord, UserPublic


def _now() -> datetime:
    return datetime.now(UTC)


def _from_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


class AuthStore:
    def __init__(self):
        self.settings = get_settings()

    def count_users(self) -> int:
        with get_connection() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM users").fetchone()
            return int(row["total"])

    def create_user(self, payload: RegisterRequest) -> UserPublic:
        password_hash, password_salt = hash_password(payload.password)
        now = _now().isoformat()
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO users (username, display_name, password_hash, password_salt, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (payload.username, payload.display_name, password_hash, password_salt, now, now),
            )
            user_id = int(cursor.lastrowid)
            row = connection.execute(
                """
                SELECT id, username, display_name, created_at, updated_at
                FROM users
                WHERE id = ?
                """,
                (user_id,),
            ).fetchone()
        return self._to_user_public(row)

    def get_user_auth_by_username(self, username: str) -> UserAuthRecord | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT id, username, display_name, password_hash, password_salt, created_at, updated_at
                FROM users
                WHERE username = ?
                """,
                (username,),
            ).fetchone()
        if not row:
            return None
        return UserAuthRecord(
            id=int(row["id"]),
            username=row["username"],
            display_name=row["display_name"],
            password_hash=row["password_hash"],
            password_salt=row["password_salt"],
            created_at=_from_iso(row["created_at"]),
            updated_at=_from_iso(row["updated_at"]),
        )

    def get_user_by_id(self, user_id: int) -> UserPublic | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT id, username, display_name, created_at, updated_at
                FROM users
                WHERE id = ?
                """,
                (user_id,),
            ).fetchone()
        if not row:
            return None
        return self._to_user_public(row)

    def create_session(self, user_id: int) -> tuple[str, datetime]:
        token = uuid4().hex
        now = _now()
        expires_at = now + timedelta(hours=self.settings.session_ttl_hours)
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO sessions (id, user_id, created_at, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (token, user_id, now.isoformat(), expires_at.isoformat()),
            )
        return token, expires_at

    def get_user_by_session(self, session_id: str) -> UserPublic | None:
        now = _now().isoformat()
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT u.id, u.username, u.display_name, u.created_at, u.updated_at, s.expires_at
                FROM sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.id = ?
                """,
                (session_id,),
            ).fetchone()
            if not row:
                return None

            if row["expires_at"] <= now:
                connection.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
                return None

        return UserPublic(
            id=int(row["id"]),
            username=row["username"],
            display_name=row["display_name"],
            created_at=_from_iso(row["created_at"]),
            updated_at=_from_iso(row["updated_at"]),
        )

    def delete_session(self, session_id: str) -> None:
        with get_connection() as connection:
            connection.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

    def cleanup_expired_sessions(self) -> None:
        now = _now().isoformat()
        with get_connection() as connection:
            connection.execute("DELETE FROM sessions WHERE expires_at <= ?", (now,))

    def _to_user_public(self, row) -> UserPublic:
        return UserPublic(
            id=int(row["id"]),
            username=row["username"],
            display_name=row["display_name"],
            created_at=_from_iso(row["created_at"]),
            updated_at=_from_iso(row["updated_at"]),
        )
