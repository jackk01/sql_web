import time

import pymysql

from app.services.db.base import BaseDatabaseClient, validate_readonly_sql


class MySQLClient(BaseDatabaseClient):
    driver_label = "MySQL"

    def _connect(self, database: str | None = None):
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.username,
            password=self.password,
            database=database or self.database,
            connect_timeout=8,
            read_timeout=30,
            write_timeout=30,
            cursorclass=pymysql.cursors.Cursor,
            autocommit=True,
        )

    def test_connection(self) -> dict:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()
        return {"driver": self.driver_label, "version": version[0] if version else "unknown"}

    def list_databases(self) -> list[str]:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SHOW DATABASES")
                return [row[0] for row in cursor.fetchall()]

    def list_tables(self, database: str) -> list[str]:
        with self._connect(database=database) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                return [row[0] for row in cursor.fetchall()]

    def execute_query(self, sql: str, limit: int, database: str | None = None) -> dict:
        readonly_sql = validate_readonly_sql(sql)
        started = time.perf_counter()
        with self._connect(database=database) as conn:
            with conn.cursor() as cursor:
                cursor.execute(readonly_sql)
                rows = cursor.fetchmany(limit + 1)
                columns = [column[0] for column in cursor.description or []]
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        truncated = len(rows) > limit
        visible_rows = rows[:limit]

        return {
            "columns": columns,
            "rows": [dict(zip(columns, row)) for row in visible_rows],
            "row_count": len(visible_rows),
            "truncated": truncated,
            "elapsed_ms": elapsed_ms,
        }

