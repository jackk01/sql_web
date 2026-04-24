import time

import clickhouse_connect

from app.services.db.base import BaseDatabaseClient, validate_readonly_sql


class ClickHouseClient(BaseDatabaseClient):
    driver_label = "ClickHouse"

    def _connect(self, database: str | None = None):
        return clickhouse_connect.get_client(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            database=database or self.database or "default",
            secure=self.secure,
            connect_timeout=8,
            send_receive_timeout=30,
        )

    def test_connection(self) -> dict:
        client = self._connect()
        try:
            version = client.command("SELECT version()")
            return {"driver": self.driver_label, "version": str(version)}
        finally:
            client.close()

    def list_databases(self) -> list[str]:
        client = self._connect()
        try:
            result = client.query("SHOW DATABASES")
            return [str(row[0]) for row in result.result_rows]
        finally:
            client.close()

    def list_tables(self, database: str) -> list[str]:
        client = self._connect(database=database)
        try:
            result = client.query("SHOW TABLES")
            return [str(row[0]) for row in result.result_rows]
        finally:
            client.close()

    def execute_query(self, sql: str, limit: int, database: str | None = None) -> dict:
        readonly_sql = validate_readonly_sql(sql)
        started = time.perf_counter()
        client = self._connect(database=database)
        try:
            result = client.query(readonly_sql)
        finally:
            client.close()

        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        rows = result.result_rows[:limit]

        return {
            "columns": list(result.column_names),
            "rows": [dict(zip(result.column_names, row)) for row in rows],
            "row_count": len(rows),
            "truncated": len(result.result_rows) > limit,
            "elapsed_ms": elapsed_ms,
        }

