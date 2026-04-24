from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class DatabaseType(str, Enum):
    mysql = "mysql"
    clickhouse = "clickhouse"
    starrocks = "starrocks"


class ConnectionPayload(BaseModel):
    name: str = Field(..., min_length=2, max_length=60)
    db_type: DatabaseType
    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(..., ge=1, le=65535)
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1, max_length=255)
    database: str | None = Field(default=None, max_length=255)
    secure: bool = False

    @field_validator("host", "username", "database", mode="before")
    @classmethod
    def strip_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class ConnectionProfile(ConnectionPayload):
    id: str
    owner_user_id: int
    created_at: datetime
    updated_at: datetime


class ConnectionSummary(BaseModel):
    id: str
    name: str
    db_type: DatabaseType
    host: str
    port: int
    username: str
    database: str | None = None
    secure: bool = False
    created_at: datetime
    updated_at: datetime


class UserPublic(BaseModel):
    id: int
    username: str
    display_name: str
    created_at: datetime
    updated_at: datetime


class UserAuthRecord(UserPublic):
    password_hash: str
    password_salt: str


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_.@-]+$")
    display_name: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("username", "display_name")
    @classmethod
    def trim_auth_strings(cls, value: str) -> str:
        return value.strip()


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_.@-]+$")
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def trim_username(cls, value: str) -> str:
        return value.strip()


class AuthResponse(BaseModel):
    user: UserPublic


class DatabaseTypeInfo(BaseModel):
    code: DatabaseType
    label: str
    default_port: int
    notes: str


class QueryRequest(BaseModel):
    connection_id: str
    sql: str = Field(..., min_length=1)
    database: str | None = Field(default=None, max_length=255)
    limit: int | None = Field(default=None, ge=1, le=10000)

    @field_validator("sql")
    @classmethod
    def normalize_sql(cls, value: str) -> str:
        sql = value.strip()
        if not sql:
            raise ValueError("SQL cannot be empty")
        return sql


class QueryResponse(BaseModel):
    columns: list[str]
    rows: list[dict[str, object | None]]
    row_count: int
    truncated: bool
    elapsed_ms: float


class DatabasesResponse(BaseModel):
    items: list[str]


class TablesResponse(BaseModel):
    items: list[str]
