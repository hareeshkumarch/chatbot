import asyncio
import json

from app.connectors.base import BaseConnector, ConnectorContent, ConnectorResource


class GCSConnector(BaseConnector):
    connector_type = "gcs"

    def _client(self):
        from google.cloud import storage
        from google.oauth2 import service_account
        info = json.loads(self.credentials["service_account_json"])
        creds = service_account.Credentials.from_service_account_info(info)
        return storage.Client(credentials=creds, project=info.get("project_id"))

    async def test_connection(self) -> bool:
        loop = asyncio.get_event_loop()
        bucket_name = self.config.get("bucket")

        def _check():
            client = self._client()
            return client.bucket(bucket_name).exists()

        return await loop.run_in_executor(None, _check)

    async def list_resources(self) -> list[ConnectorResource]:
        loop = asyncio.get_event_loop()
        bucket_name = self.config.get("bucket")
        prefix = self.config.get("prefix")

        def _list():
            client = self._client()
            blobs = client.list_blobs(bucket_name, prefix=prefix)
            return [ConnectorResource(resource_id=b.name, name=b.name, kind="object", size_bytes=b.size) for b in blobs if not b.name.endswith("/")]

        return await loop.run_in_executor(None, _list)

    async def fetch_content(self, resource_id: str) -> ConnectorContent:
        loop = asyncio.get_event_loop()
        bucket_name = self.config.get("bucket")

        def _fetch():
            client = self._client()
            blob = client.bucket(bucket_name).blob(resource_id)
            return blob.download_as_bytes()

        raw_bytes = await loop.run_in_executor(None, _fetch)
        extension = resource_id.rsplit(".", 1)[-1] if "." in resource_id else "txt"
        return ConnectorContent(
            resource_id=resource_id,
            title=resource_id.rsplit("/", 1)[-1],
            file_extension=extension,
            raw_bytes=raw_bytes,
            source_uri=f"gs://{bucket_name}/{resource_id}",
        )
