import asyncio

from app.connectors.base import BaseConnector, ConnectorContent, ConnectorResource


class S3Connector(BaseConnector):
    connector_type = "s3"

    def _client(self):
        import boto3
        return boto3.client(
            "s3",
            aws_access_key_id=self.credentials.get("access_key_id"),
            aws_secret_access_key=self.credentials.get("secret_access_key"),
            region_name=self.credentials.get("region", "us-east-1"),
        )

    async def test_connection(self) -> bool:
        loop = asyncio.get_event_loop()
        bucket = self.config.get("bucket")

        def _check():
            client = self._client()
            client.head_bucket(Bucket=bucket)
            return True

        return await loop.run_in_executor(None, _check)

    async def list_resources(self) -> list[ConnectorResource]:
        loop = asyncio.get_event_loop()
        bucket = self.config.get("bucket")
        prefix = self.config.get("prefix", "")

        def _list():
            client = self._client()
            paginator = client.get_paginator("list_objects_v2")
            resources = []
            for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    if obj["Key"].endswith("/"):
                        continue
                    resources.append(ConnectorResource(resource_id=obj["Key"], name=obj["Key"], kind="object", size_bytes=obj["Size"]))
            return resources

        return await loop.run_in_executor(None, _list)

    async def fetch_content(self, resource_id: str) -> ConnectorContent:
        loop = asyncio.get_event_loop()
        bucket = self.config.get("bucket")

        def _fetch():
            client = self._client()
            obj = client.get_object(Bucket=bucket, Key=resource_id)
            return obj["Body"].read()

        raw_bytes = await loop.run_in_executor(None, _fetch)
        extension = resource_id.rsplit(".", 1)[-1] if "." in resource_id else "txt"
        return ConnectorContent(
            resource_id=resource_id,
            title=resource_id.rsplit("/", 1)[-1],
            file_extension=extension,
            raw_bytes=raw_bytes,
            source_uri=f"s3://{bucket}/{resource_id}",
        )
