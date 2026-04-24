from app.models.schemas import ConnectionPayload, DatabaseType
from app.services.db.clickhouse import ClickHouseClient
from app.services.db.mysql import MySQLClient
from app.services.db.starrocks import StarRocksClient


def create_client(payload: ConnectionPayload):
    params = payload.model_dump(exclude={"name", "db_type"})
    if payload.db_type == DatabaseType.mysql:
        return MySQLClient(**params)
    if payload.db_type == DatabaseType.clickhouse:
        return ClickHouseClient(**params)
    if payload.db_type == DatabaseType.starrocks:
        return StarRocksClient(**params)
    raise ValueError(f"Unsupported database type: {payload.db_type}")
