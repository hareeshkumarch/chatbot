import httpx

from app.connectors.base import BaseConnector, ConnectorContent, ConnectorResource

GOOGLE_NATIVE_EXPORT_MIME = "text/plain"
GOOGLE_NATIVE_MIME_PREFIX = "application/vnd.google-apps."


class GoogleDriveConnector(BaseConnector):
    connector_type = "google_drive"
    base_url = "https://www.googleapis.com/drive/v3"

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.credentials['access_token']}"}

    async def test_connection(self) -> bool:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{self.base_url}/about", headers=self._headers(), params={"fields": "user"})
        return resp.status_code == 200

    async def list_resources(self) -> list[ConnectorResource]:
        resources = []
        page_token = None
        async with httpx.AsyncClient(timeout=20.0) as client:
            while True:
                params = {
                    "pageSize": 100,
                    "fields": "nextPageToken, files(id, name, mimeType, size)",
                    "q": "trashed = false",
                }
                if page_token:
                    params["pageToken"] = page_token
                resp = await client.get(f"{self.base_url}/files", headers=self._headers(), params=params)
                resp.raise_for_status()
                data = resp.json()
                for f in data.get("files", []):
                    size = int(f["size"]) if f.get("size") else None
                    resources.append(
                        ConnectorResource(resource_id=f["id"], name=f.get("name", f["id"]), kind=f.get("mimeType", "file"), size_bytes=size)
                    )
                page_token = data.get("nextPageToken")
                if not page_token:
                    break
        return resources

    async def fetch_content(self, resource_id: str) -> ConnectorContent:
        async with httpx.AsyncClient(timeout=30.0) as client:
            meta_resp = await client.get(f"{self.base_url}/files/{resource_id}", headers=self._headers(), params={"fields": "name, mimeType"})
            meta_resp.raise_for_status()
            meta = meta_resp.json()
            mime_type = meta.get("mimeType", "")
            title = meta.get("name", resource_id)

            if mime_type.startswith(GOOGLE_NATIVE_MIME_PREFIX):
                content_resp = await client.get(
                    f"{self.base_url}/files/{resource_id}/export", headers=self._headers(), params={"mimeType": GOOGLE_NATIVE_EXPORT_MIME}
                )
                extension = "txt"
            else:
                content_resp = await client.get(f"{self.base_url}/files/{resource_id}", headers=self._headers(), params={"alt": "media"})
                extension = title.rsplit(".", 1)[-1].lower() if "." in title else "bin"
            content_resp.raise_for_status()

        return ConnectorContent(
            resource_id=resource_id,
            title=title,
            file_extension=extension,
            raw_bytes=content_resp.content,
            source_uri=f"googledrive://file/{resource_id}",
        )

    async def search(self, query: str) -> list[dict]:
        escaped = query.replace("'", "\\'")
        params = {"q": f"fullText contains '{escaped}' and trashed = false", "pageSize": 20, "fields": "files(id, name, mimeType)"}
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(f"{self.base_url}/files", headers=self._headers(), params=params)
        if resp.status_code != 200:
            return []
        return resp.json().get("files", [])

    @staticmethod
    def authorize_url(client_id: str, redirect_uri: str, state: str) -> str:
        scopes = "https://www.googleapis.com/auth/drive.readonly"
        return (
            "https://accounts.google.com/o/oauth2/v2/auth"
            f"?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"
            f"&scope={scopes}&access_type=offline&prompt=consent&state={state}"
        )

    @staticmethod
    async def exchange_code(client_id: str, client_secret: str, code: str, redirect_uri: str) -> dict:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
        return resp.json()
