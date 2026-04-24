import re
from abc import ABC, abstractmethod


READONLY_PREFIXES = ("select", "show", "describe", "desc", "explain", "with")
FORBIDDEN_SQL = (
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "truncate",
    "create",
    "replace",
    "grant",
    "revoke",
)


def validate_readonly_sql(sql: str) -> str:
    normalized = strip_sql_comments(sql).strip().rstrip(";").strip()
    lowered = normalized.lower()
    if not normalized:
        raise ValueError("SQL cannot be empty")
    if not lowered.startswith(READONLY_PREFIXES):
        raise ValueError("Only read-only statements are allowed")
    if ";" in normalized:
        raise ValueError("Multiple statements are not allowed")

    for keyword in FORBIDDEN_SQL:
        if re.search(rf"\b{keyword}\b", lowered):
            raise ValueError(f"Forbidden keyword detected: {keyword}")
    return normalized


def strip_sql_comments(sql: str) -> str:
    result: list[str] = []
    index = 0
    length = len(sql)
    in_single = False
    in_double = False
    in_backtick = False
    in_line_comment = False
    in_block_comment = False

    while index < length:
        current = sql[index]
        next_char = sql[index + 1] if index + 1 < length else ""

        if in_line_comment:
            if current == "\n":
                in_line_comment = False
                result.append(current)
            index += 1
            continue

        if in_block_comment:
            if current == "*" and next_char == "/":
                in_block_comment = False
                index += 2
            else:
                index += 1
            continue

        if not in_single and not in_double and not in_backtick:
            if current == "-" and next_char == "-":
                in_line_comment = True
                index += 2
                continue
            if current == "#":
                in_line_comment = True
                index += 1
                continue
            if current == "/" and next_char == "*":
                in_block_comment = True
                index += 2
                continue

        if current == "'" and not in_double and not in_backtick:
            escaped = index > 0 and sql[index - 1] == "\\"
            if not escaped:
                in_single = not in_single
        elif current == '"' and not in_single and not in_backtick:
            escaped = index > 0 and sql[index - 1] == "\\"
            if not escaped:
                in_double = not in_double
        elif current == "`" and not in_single and not in_double:
            in_backtick = not in_backtick

        result.append(current)
        index += 1

    return "".join(result)


class BaseDatabaseClient(ABC):
    def __init__(self, *, host: str, port: int, username: str, password: str, database: str | None, secure: bool):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.secure = secure

    @abstractmethod
    def test_connection(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def list_databases(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def list_tables(self, database: str) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def execute_query(self, sql: str, limit: int, database: str | None = None) -> dict:
        raise NotImplementedError
