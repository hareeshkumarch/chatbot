from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ConnectorResource:
    resource_id: str
    name: str
    kind: str
    size_bytes: int | None = None
    extra: dict | None = None


@dataclass
class ConnectorContent:
    resource_id: str
    title: str
    file_extension: str
    raw_bytes: bytes
    source_uri: str


class BaseConnector(ABC):
    connector_type: str

    def __init__(self, credentials: dict, config: dict | None = None):
        self.credentials = credentials
        self.config = config or {}

    @abstractmethod
    async def test_connection(self) -> bool: ...

    @abstractmethod
    async def list_resources(self) -> list[ConnectorResource]: ...

    @abstractmethod
    async def fetch_content(self, resource_id: str) -> ConnectorContent: ...

    async def sync(self) -> list[ConnectorContent]:
        resources = await self.list_resources()
        contents = []
        for resource in resources:
            try:
                contents.append(await self.fetch_content(resource.resource_id))
            except Exception:
                continue
        return contents
