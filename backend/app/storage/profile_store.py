from datetime import UTC, datetime
from uuid import uuid4

from app.core.database import get_connection
from app.core.security import decrypt_secret, encrypt_secret
from app.models.schemas import ConnectionPayload, ConnectionProfile, ConnectionSummary


class ProfileStore:
    def list_profiles(self, user_id: int) -> list[ConnectionSummary]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT id, name, db_type, host, port, username, database_name, secure, created_at, updated_at
                FROM connection_profiles
                WHERE owner_user_id = ?
                ORDER BY updated_at DESC
                """,
                (user_id,),
            ).fetchall()
        return [self._to_summary(row) for row in rows]

    def get_profile(self, connection_id: str, user_id: int) -> ConnectionProfile | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT id, owner_user_id, name, db_type, host, port, username, password_encrypted, database_name,
                       secure, created_at, updated_at
                FROM connection_profiles
                WHERE id = ? AND owner_user_id = ?
                """,
                (connection_id, user_id),
            ).fetchone()
        if not row:
            return None
        return self._to_profile(row)

    def get_connection_payload(self, connection_id: str, user_id: int) -> ConnectionPayload | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT name, db_type, host, port, username, password_encrypted, database_name, secure
                FROM connection_profiles
                WHERE id = ? AND owner_user_id = ?
                """,
                (connection_id, user_id),
            ).fetchone()
        if not row:
            return None
        return ConnectionPayload(
            name=row["name"],
            db_type=row["db_type"],
            host=row["host"],
            port=int(row["port"]),
            username=row["username"],
            password=decrypt_secret(row["password_encrypted"]),
            database=row["database_name"],
            secure=bool(row["secure"]),
        )

    def create_profile(self, payload: ConnectionPayload, user_id: int) -> ConnectionSummary:
        now = datetime.now(UTC)
        profile_id = str(uuid4())
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO connection_profiles (
                    id, owner_user_id, name, db_type, host, port, username, password_encrypted,
                    database_name, secure, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    profile_id,
                    user_id,
                    payload.name,
                    payload.db_type.value,
                    payload.host,
                    payload.port,
                    payload.username,
                    encrypt_secret(payload.password),
                    payload.database,
                    int(payload.secure),
                    now.isoformat(),
                    now.isoformat(),
                ),
            )
            row = connection.execute(
                """
                SELECT id, name, db_type, host, port, username, database_name, secure, created_at, updated_at
                FROM connection_profiles
                WHERE id = ? AND owner_user_id = ?
                """,
                (profile_id, user_id),
            ).fetchone()
        return self._to_summary(row)

    def delete_profile(self, connection_id: str, user_id: int) -> bool:
        with get_connection() as connection:
            cursor = connection.execute(
                "DELETE FROM connection_profiles WHERE id = ? AND owner_user_id = ?",
                (connection_id, user_id),
            )
        return cursor.rowcount > 0

    def _to_summary(self, row) -> ConnectionSummary:
        return ConnectionSummary(
            id=row["id"],
            name=row["name"],
            db_type=row["db_type"],
            host=row["host"],
            port=int(row["port"]),
            username=row["username"],
            database=row["database_name"],
            secure=bool(row["secure"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _to_profile(self, row) -> ConnectionProfile:
        return ConnectionProfile(
            id=row["id"],
            owner_user_id=int(row["owner_user_id"]),
            name=row["name"],
            db_type=row["db_type"],
            host=row["host"],
            port=int(row["port"]),
            username=row["username"],
            password=decrypt_secret(row["password_encrypted"]),
            database=row["database_name"],
            secure=bool(row["secure"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
