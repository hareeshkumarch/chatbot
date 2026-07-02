import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.loader import instantiate_connector
from app.connectors.registry import CONNECTOR_CLASSES, CREDENTIAL_CONNECTOR_TYPES, OAUTH_CONNECTOR_TYPES
from app.core.encryption import encrypt_payload
from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.metrics import active_connectors
from app.db.models import Connector, ConnectorCredential, Document
from app.vectorstore.qdrant_client import delete_by_document

REQUIRED_CREDENTIAL_FIELDS: dict[str, list[str]] = {
    "s3": ["access_key_id", "secret_access_key"],
    "azure_blob": ["connection_string"],
    "gcs": ["service_account_json"],
    "sql": ["connection_url"],
    "mongodb": ["connection_url"],
    "linear": ["api_key"],
}

REQUIRED_CONFIG_FIELDS: dict[str, list[str]] = {
    "s3": ["bucket"],
    "azure_blob": ["container"],
    "gcs": ["bucket"],
    "mongodb": ["database"],
    "web": ["urls"],
    "zendesk": ["subdomain"],
}


def auth_mode_for(connector_type: str) -> str:
    if connector_type in OAUTH_CONNECTOR_TYPES:
        return "oauth"
    if connector_type in CREDENTIAL_CONNECTOR_TYPES:
        return "credentials"
    return "config_only"


def _missing_fields(required: dict[str, list[str]], connector_type: str, values: dict) -> list[str]:
    return [f for f in required.get(connector_type, []) if not values.get(f)]


class ConnectorService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_connectors(self, tenant_id: str) -> list[Connector]:
        result = await self.session.execute(select(Connector).where(Connector.tenant_id == tenant_id).order_by(Connector.created_at.desc()))
        return list(result.scalars().all())

    async def get_owned_connector(self, connector_id: str, tenant_id: str) -> Connector:
        result = await self.session.execute(select(Connector).where(Connector.id == connector_id, Connector.tenant_id == tenant_id))
        connector = result.scalar_one_or_none()
        if connector is None:
            raise NotFoundError("connector not found")
        return connector

    async def create_connector(self, tenant_id: str, connector_type: str, name: str, config: dict, credentials: dict) -> Connector:
        if connector_type not in CONNECTOR_CLASSES:
            raise ValidationAppError(f"unknown connector type: {connector_type}")

        mode = auth_mode_for(connector_type)

        if mode == "oauth":
            missing_config = _missing_fields(REQUIRED_CONFIG_FIELDS, connector_type, config)
            if missing_config:
                raise ValidationAppError(f"missing required config fields: {missing_config}")
            connector = Connector(tenant_id=tenant_id, type=connector_type, name=name, config=config, status="pending_auth")
            self.session.add(connector)
            await self.session.commit()
            return connector

        missing_config = _missing_fields(REQUIRED_CONFIG_FIELDS, connector_type, config)
        if missing_config:
            raise ValidationAppError(f"missing required config fields: {missing_config}")

        if mode == "credentials":
            missing_credentials = _missing_fields(REQUIRED_CREDENTIAL_FIELDS, connector_type, credentials)
            if missing_credentials:
                raise ValidationAppError(f"missing required credential fields: {missing_credentials}")
            connector = Connector(tenant_id=tenant_id, type=connector_type, name=name, config=config, status="connected")
            self.session.add(connector)
            await self.session.flush()
            self.session.add(ConnectorCredential(connector_id=connector.id, encrypted_payload=encrypt_payload(json.dumps(credentials))))
            await self.session.commit()
            return connector

        connector = Connector(tenant_id=tenant_id, type=connector_type, name=name, config=config, status="connected")
        self.session.add(connector)
        await self.session.commit()
        return connector

    async def update_connector(self, connector: Connector, name: str | None, config: dict | None) -> Connector:
        if name is not None:
            connector.name = name
        if config is not None:
            connector.config = config
        await self.session.commit()
        return connector

    async def update_credentials(self, connector: Connector, credentials: dict) -> Connector:
        if connector.type not in CREDENTIAL_CONNECTOR_TYPES:
            raise ValidationAppError("this connector type does not accept manual credentials")
        missing = _missing_fields(REQUIRED_CREDENTIAL_FIELDS, connector.type, credentials)
        if missing:
            raise ValidationAppError(f"missing required credential fields: {missing}")

        result = await self.session.execute(select(ConnectorCredential).where(ConnectorCredential.connector_id == connector.id))
        existing = result.scalar_one_or_none()
        encrypted = encrypt_payload(json.dumps(credentials))
        if existing is None:
            self.session.add(ConnectorCredential(connector_id=connector.id, encrypted_payload=encrypted))
        else:
            existing.encrypted_payload = encrypted
        connector.status = "connected"
        await self.session.commit()
        return connector

    async def test_connection(self, connector: Connector) -> tuple[bool, str | None]:
        try:
            instance = await instantiate_connector(self.session, connector)
            connected = await instance.test_connection()
        except Exception as exc:
            return False, str(exc)[:500]
        connector.status = "connected" if connected else "error"
        await self.session.commit()
        return connected, None if connected else "connection test returned false"

    async def mark_syncing(self, connector: Connector) -> None:
        connector.status = "syncing"
        await self.session.commit()

    async def mark_sync_failed(self, connector: Connector) -> None:
        connector.status = "error"
        await self.session.commit()

    async def refresh_active_gauge(self, tenant_id: str, connectors: list[Connector]) -> None:
        active_connectors.labels(tenant_id=tenant_id).set(sum(1 for c in connectors if c.status == "connected"))

    async def delete_connector(self, tenant_id: str, connector: Connector) -> None:
        doc_result = await self.session.execute(select(Document).where(Document.connector_id == connector.id))
        for document in doc_result.scalars().all():
            await delete_by_document(tenant_id, document.id)
            await self.session.delete(document)

        cred_result = await self.session.execute(select(ConnectorCredential).where(ConnectorCredential.connector_id == connector.id))
        credential = cred_result.scalar_one_or_none()
        if credential is not None:
            await self.session.delete(credential)

        await self.session.delete(connector)
        await self.session.commit()
