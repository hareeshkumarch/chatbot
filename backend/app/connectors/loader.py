import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.base import BaseConnector
from app.connectors.database.sql_connector import SQLConnector
from app.connectors.registry import build_connector
from app.core.encryption import decrypt_payload
from app.core.logging import get_logger
from app.db.models import Connector, ConnectorCredential

logger = get_logger(__name__)


async def load_connector_credentials(session: AsyncSession, connector_id: str) -> dict:
    result = await session.execute(select(ConnectorCredential).where(ConnectorCredential.connector_id == connector_id))
    row = result.scalar_one_or_none()
    if row is None:
        return {}
    return json.loads(decrypt_payload(row.encrypted_payload))


async def load_credentials_for_connectors(session: AsyncSession, connector_ids: list[str]) -> dict[str, dict]:
    if not connector_ids:
        return {}
    result = await session.execute(select(ConnectorCredential).where(ConnectorCredential.connector_id.in_(connector_ids)))
    credentials: dict[str, dict] = {}
    for row in result.scalars().all():
        credentials[row.connector_id] = json.loads(decrypt_payload(row.encrypted_payload))
    return credentials


async def instantiate_connector(session: AsyncSession, connector: Connector) -> BaseConnector:
    credentials = await load_connector_credentials(session, connector.id)
    return build_connector(connector.type, credentials, connector.config)


async def load_tenant_connectors(session: AsyncSession, tenant_id: str, connector_ids: list[str] | None = None) -> list[Connector]:
    stmt = select(Connector).where(Connector.tenant_id == tenant_id, Connector.status == "connected")
    if connector_ids is not None:
        stmt = stmt.where(Connector.id.in_(connector_ids))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def build_active_connectors(
    session: AsyncSession, tenant_id: str, connector_ids: list[str] | None = None
) -> tuple[SQLConnector | None, list[BaseConnector]]:
    rows = await load_tenant_connectors(session, tenant_id, connector_ids)
    credentials_by_id = await load_credentials_for_connectors(session, [row.id for row in rows])
    sql_connector: SQLConnector | None = None
    active: list[BaseConnector] = []
    for row in rows:
        try:
            instance = build_connector(row.type, credentials_by_id.get(row.id, {}), row.config)
        except Exception as exc:
            logger.warning(f"failed to instantiate connector {row.id} ({row.type}): {exc}")
            continue
        if row.type == "sql":
            sql_connector = instance
        else:
            active.append(instance)
    return sql_connector, active
