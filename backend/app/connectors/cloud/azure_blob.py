from app.connectors.base import BaseConnector, ConnectorContent, ConnectorResource


class AzureBlobConnector(BaseConnector):
    connector_type = "azure_blob"

    def _client(self):
        from azure.storage.blob.aio import BlobServiceClient
        return BlobServiceClient.from_connection_string(self.credentials["connection_string"])

    async def test_connection(self) -> bool:
        container_name = self.config.get("container")
        async with self._client() as client:
            container = client.get_container_client(container_name)
            return await container.exists()

    async def list_resources(self) -> list[ConnectorResource]:
        container_name = self.config.get("container")
        prefix = self.config.get("prefix")
        resources = []
        async with self._client() as client:
            container = client.get_container_client(container_name)
            async for blob in container.list_blobs(name_starts_with=prefix):
                resources.append(ConnectorResource(resource_id=blob.name, name=blob.name, kind="blob", size_bytes=blob.size))
        return resources

    async def fetch_content(self, resource_id: str) -> ConnectorContent:
        container_name = self.config.get("container")
        async with self._client() as client:
            container = client.get_container_client(container_name)
            blob_client = container.get_blob_client(resource_id)
            stream = await blob_client.download_blob()
            raw_bytes = await stream.readall()
        extension = resource_id.rsplit(".", 1)[-1] if "." in resource_id else "txt"
        return ConnectorContent(
            resource_id=resource_id,
            title=resource_id.rsplit("/", 1)[-1],
            file_extension=extension,
            raw_bytes=raw_bytes,
            source_uri=f"azure://{container_name}/{resource_id}",
        )
