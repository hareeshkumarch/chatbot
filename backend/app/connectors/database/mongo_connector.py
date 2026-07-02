import json

from bson import json_util
from motor.motor_asyncio import AsyncIOMotorClient

from app.connectors.base import BaseConnector, ConnectorContent, ConnectorResource


class MongoConnector(BaseConnector):
    connector_type = "mongodb"

    def _client(self) -> AsyncIOMotorClient:
        return AsyncIOMotorClient(self.credentials["connection_url"])

    async def test_connection(self) -> bool:
        client = self._client()
        try:
            await client.admin.command("ping")
            return True
        finally:
            client.close()

    async def list_resources(self) -> list[ConnectorResource]:
        client = self._client()
        try:
            db = client[self.config["database"]]
            collections = await db.list_collection_names()
            return [ConnectorResource(resource_id=c, name=c, kind="collection") for c in collections]
        finally:
            client.close()

    async def fetch_content(self, resource_id: str) -> ConnectorContent:
        client = self._client()
        try:
            db = client[self.config["database"]]
            documents = await db[resource_id].find().limit(200).to_list(length=200)
            combined = json.dumps(json.loads(json_util.dumps(documents)), indent=None)
            return ConnectorContent(
                resource_id=resource_id,
                title=f"Collection {resource_id}",
                file_extension="txt",
                raw_bytes=combined.encode("utf-8"),
                source_uri=f"mongodb://{self.config['database']}/{resource_id}",
            )
        finally:
            client.close()

    async def run_find(self, collection: str, filter_query: dict, limit: int = 100) -> list[dict]:
        client = self._client()
        try:
            db = client[self.config["database"]]
            documents = await db[collection].find(filter_query).limit(limit).to_list(length=limit)
            return json.loads(json_util.dumps(documents))
        finally:
            client.close()
