import re

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import get_settings
from app.connectors.base import BaseConnector, ConnectorContent, ConnectorResource

FORBIDDEN_KEYWORDS = re.compile(r"\b(insert|update|delete|drop|alter|truncate|grant|revoke|create|attach|exec)\b", re.IGNORECASE)


class SQLConnector(BaseConnector):
    connector_type = "sql"

    def _engine(self):
        return create_async_engine(self.credentials["connection_url"], pool_pre_ping=True)

    async def test_connection(self) -> bool:
        engine = self._engine()
        try:
            async with engine.connect() as conn:
                await conn.execute(sa.text("SELECT 1"))
            return True
        finally:
            await engine.dispose()

    async def list_resources(self) -> list[ConnectorResource]:
        engine = self._engine()
        try:
            async with engine.connect() as conn:
                def _reflect(sync_conn):
                    inspector = sa.inspect(sync_conn)
                    return inspector.get_table_names()
                tables = await conn.run_sync(_reflect)
            return [ConnectorResource(resource_id=t, name=t, kind="table") for t in tables]
        finally:
            await engine.dispose()

    async def fetch_content(self, resource_id: str) -> ConnectorContent:
        engine = self._engine()
        try:
            async with engine.connect() as conn:
                result = await conn.execute(sa.text(f"SELECT * FROM {resource_id} LIMIT 200"))
                rows = result.fetchall()
                columns = result.keys()
            lines = [" | ".join(columns)]
            for row in rows:
                lines.append(" | ".join(str(v) for v in row))
            combined = "\n".join(lines)
            return ConnectorContent(
                resource_id=resource_id,
                title=f"Table {resource_id}",
                file_extension="txt",
                raw_bytes=combined.encode("utf-8"),
                source_uri=f"sql://{resource_id}",
            )
        finally:
            await engine.dispose()

    async def get_schema(self) -> dict[str, list[str]]:
        engine = self._engine()
        try:
            async with engine.connect() as conn:
                def _reflect(sync_conn):
                    inspector = sa.inspect(sync_conn)
                    schema = {}
                    for table in inspector.get_table_names():
                        schema[table] = [col["name"] for col in inspector.get_columns(table)]
                    return schema
                return await conn.run_sync(_reflect)
        finally:
            await engine.dispose()

    async def run_readonly_query(self, sql: str) -> list[dict]:
        settings = get_settings()
        stripped = sql.strip().rstrip(";")
        if not stripped.lower().startswith("select"):
            raise ValueError("only SELECT statements are permitted")
        if FORBIDDEN_KEYWORDS.search(stripped):
            raise ValueError("query contains a forbidden keyword")
        if "limit" not in stripped.lower():
            stripped = f"{stripped} LIMIT {settings.sql_agent_row_limit}"
        engine = self._engine()
        try:
            async with engine.connect() as conn:
                await conn.execute(sa.text(f"SET statement_timeout = {settings.sql_agent_timeout_seconds * 1000}")) if "postgresql" in str(engine.url) else None
                result = await conn.execute(sa.text(stripped))
                columns = result.keys()
                rows = result.fetchall()
            return [dict(zip(columns, row, strict=True)) for row in rows]
        finally:
            await engine.dispose()
