from io import BytesIO
from re import sub

from fastapi import HTTPException, status
from openpyxl import Workbook

from app.core.config import get_settings
from app.models.schemas import (
    ConnectionPayload,
    ConnectionProfile,
    ConnectionSummary,
    DatabaseType,
    DatabaseTypeInfo,
    QueryRequest,
    QueryResponse,
)
from app.services.db.factory import create_client
from app.storage.profile_store import ProfileStore


class QueryService:
    def __init__(self, store: ProfileStore):
        self.store = store
        self.settings = get_settings()

    def list_database_types(self) -> list[DatabaseTypeInfo]:
        return [
            DatabaseTypeInfo(
                code=DatabaseType.mysql,
                label="MySQL",
                default_port=3306,
                notes="适合 OLTP 场景，常见于业务数据库",
            ),
            DatabaseTypeInfo(
                code=DatabaseType.clickhouse,
                label="ClickHouse",
                default_port=8123,
                notes="适合分析型查询，建议通过 HTTP 接口访问",
            ),
            DatabaseTypeInfo(
                code=DatabaseType.starrocks,
                label="StarRocks",
                default_port=9030,
                notes="兼容 MySQL 协议，适合实时数仓查询",
            ),
        ]

    def list_connections(self, user_id: int) -> list[ConnectionSummary]:
        return self.store.list_profiles(user_id)

    def get_connection(self, connection_id: str, user_id: int) -> ConnectionProfile:
        profile = self.store.get_profile(connection_id, user_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
        return profile

    def create_connection(self, payload: ConnectionPayload, user_id: int) -> ConnectionSummary:
        client = create_client(payload)
        client.test_connection()
        return self.store.create_profile(payload, user_id)

    def update_connection(self, connection_id: str, payload: ConnectionPayload, user_id: int) -> ConnectionSummary:
        client = create_client(payload)
        client.test_connection()
        updated = self.store.update_profile(connection_id, payload, user_id)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
        return updated

    def delete_connection(self, connection_id: str, user_id: int) -> None:
        deleted = self.store.delete_profile(connection_id, user_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")

    def test_connection(self, payload: ConnectionPayload) -> dict:
        client = create_client(payload)
        return client.test_connection()

    def list_databases(self, connection_id: str, user_id: int) -> list[str]:
        client = self._client_from_profile(connection_id, user_id)
        return client.list_databases()

    def list_tables(self, connection_id: str, database: str, user_id: int) -> list[str]:
        if not database:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Database is required")
        client = self._client_from_profile(connection_id, user_id)
        return client.list_tables(database)

    def execute_query(self, payload: QueryRequest, user_id: int) -> QueryResponse:
        client = self._client_from_profile(payload.connection_id, user_id)
        limit = min(payload.limit or self.settings.default_query_limit, self.settings.max_query_limit)
        result = client.execute_query(payload.sql, limit=limit, database=payload.database)
        return QueryResponse(**result)

    def export_query(self, payload: QueryRequest, user_id: int) -> tuple[bytes, str]:
        client = self._client_from_profile(payload.connection_id, user_id)
        limit = min(payload.limit or self.settings.default_query_limit, self.settings.max_export_limit)
        result = client.execute_query(payload.sql, limit=limit, database=payload.database)

        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Query Result"

        columns = result["columns"]
        if columns:
            worksheet.append(columns)
            for cell in worksheet[1]:
                cell.style = "Headline 1"

        for row in result["rows"]:
            worksheet.append([self._normalize_excel_value(row.get(column)) for column in columns])

        worksheet.freeze_panes = "A2"
        worksheet.sheet_view.showGridLines = True

        output = BytesIO()
        workbook.save(output)
        workbook.close()

        filename = self._build_export_filename(payload.database)
        return output.getvalue(), filename

    def _client_from_profile(self, connection_id: str, user_id: int):
        payload = self.store.get_connection_payload(connection_id, user_id)
        if not payload:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
        return create_client(payload)

    def _build_export_filename(self, database: str | None) -> str:
        name = database or "query_result"
        safe_name = sub(r"[^a-zA-Z0-9_.-]+", "_", name).strip("._") or "query_result"
        return f"{safe_name}.xlsx"

    def _normalize_excel_value(self, value):
        if isinstance(value, (list, dict, set, tuple)):
            return str(value)
        return value
