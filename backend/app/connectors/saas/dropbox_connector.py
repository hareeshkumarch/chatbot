import json

import httpx

from app.connectors.base import BaseConnector, ConnectorContent, ConnectorResource


class DropboxConnector(BaseConnector):
    connector_type = "dropbox"
    api_url = "https://api.dropboxapi.com/2"
    content_url = "https://content.dropboxapi.com/2"

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.credentials['access_token']}"}

    async def test_connection(self) -> bool:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(f"{self.api_url}/users/get_current_account", headers=self._headers())
        return resp.status_code == 200

    async def list_resources(self) -> list[ConnectorResource]:
        resources = []
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{self.api_url}/files/list_folder",
                headers=self._headers(),
                json={"path": "", "recursive": True, "limit": 200},
            )
            resp.raise_for_status()
            data = resp.json()
            cursor = data.get("cursor")
            has_more = data.get("has_more", False)
            self._collect_entries(data.get("entries", []), resources)

            while has_more:
                cont_resp = await client.post(f"{self.api_url}/files/list_folder/continue", headers=self._headers(), json={"cursor": cursor})
                if cont_resp.status_code != 200:
                    break
                cont_data = cont_resp.json()
                self._collect_entries(cont_data.get("entries", []), resources)
                cursor = cont_data.get("cursor")
                has_more = cont_data.get("has_more", False)
        return resources

    @staticmethod
    def _collect_entries(entries: list[dict], resources: list[ConnectorResource]) -> None:
        for entry in entries:
            if entry.get(".tag") != "file":
                continue
            resources.append(
                ConnectorResource(
                    resource_id=entry["path_lower"],
                    name=entry.get("name", entry["path_lower"]),
                    kind="file",
                    size_bytes=entry.get("size"),
                )
            )

    async def fetch_content(self, resource_id: str) -> ConnectorContent:
        headers = {**self._headers(), "Dropbox-API-Arg": _json_arg({"path": resource_id})}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{self.content_url}/files/download", headers=headers)
        resp.raise_for_status()
        title = resource_id.rsplit("/", 1)[-1]
        extension = title.rsplit(".", 1)[-1].lower() if "." in title else "bin"
        return ConnectorContent(
            resource_id=resource_id,
            title=title,
            file_extension=extension,
            raw_bytes=resp.content,
            source_uri=f"dropbox://{resource_id}",
        )

    async def search(self, query: str) -> list[dict]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{self.api_url}/files/search_v2",
                headers=self._headers(),
                json={"query": query, "options": {"max_results": 20}},
            )
        if resp.status_code != 200:
            return []
        return resp.json().get("matches", [])

    @staticmethod
    def authorize_url(client_id: str, redirect_uri: str, state: str) -> str:
        return (
            "https://www.dropbox.com/oauth2/authorize"
            f"?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"
            f"&token_access_type=offline&state={state}"
        )

    @staticmethod
    async def exchange_code(client_id: str, client_secret: str, code: str, redirect_uri: str) -> dict:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.dropboxapi.com/oauth2/token",
                data={
                    "code": code,
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                },
            )
        return resp.json()


def _json_arg(payload: dict) -> str:
    return json.dumps(payload)
