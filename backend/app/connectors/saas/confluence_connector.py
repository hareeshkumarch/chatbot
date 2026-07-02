import json

import httpx

from app.connectors.base import BaseConnector, ConnectorContent, ConnectorResource
from app.connectors.saas._atlassian import extract_adf_text


class ConfluenceConnector(BaseConnector):
    connector_type = "confluence"

    def _base_url(self) -> str:
        return f"https://api.atlassian.com/ex/confluence/{self.credentials['cloud_id']}/wiki"

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.credentials['access_token']}", "Accept": "application/json"}

    async def test_connection(self) -> bool:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{self._base_url()}/api/v2/spaces", headers=self._headers(), params={"limit": 1})
        return resp.status_code == 200

    async def list_resources(self) -> list[ConnectorResource]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(f"{self._base_url()}/api/v2/spaces", headers=self._headers(), params={"limit": 100})
        resp.raise_for_status()
        return [ConnectorResource(resource_id=s["id"], name=s.get("name", s["id"]), kind="space") for s in resp.json().get("results", [])]

    async def fetch_content(self, resource_id: str) -> ConnectorContent:
        lines: list[str] = []
        cursor_params = {"space-id": resource_id, "limit": 50, "body-format": "atlas_doc_format"}
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(f"{self._base_url()}/api/v2/pages", headers=self._headers(), params=cursor_params)
            resp.raise_for_status()
            for page in resp.json().get("results", []):
                body = page.get("body", {}).get("atlas_doc_format", {}).get("value")
                text = extract_adf_text(_safe_json(body))
                lines.append(f"{page.get('title', page['id'])}\n{text}")
        combined = "\n\n".join(lines)
        return ConnectorContent(
            resource_id=resource_id,
            title=f"Confluence space {resource_id}",
            file_extension="txt",
            raw_bytes=combined.encode("utf-8"),
            source_uri=f"confluence://space/{resource_id}",
        )

    async def search(self, query: str) -> list[dict]:
        cql = f'text ~ "{query}"'
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(f"{self._base_url()}/rest/api/search", headers=self._headers(), params={"cql": cql, "limit": 20})
        if resp.status_code != 200:
            return []
        return resp.json().get("results", [])

    @staticmethod
    def authorize_url(client_id: str, redirect_uri: str, state: str) -> str:
        scopes = "read:confluence-content.all read:confluence-space.summary offline_access"
        return (
            "https://auth.atlassian.com/authorize"
            f"?audience=api.atlassian.com&client_id={client_id}&scope={scopes}"
            f"&redirect_uri={redirect_uri}&state={state}&response_type=code&prompt=consent"
        )

    @staticmethod
    async def exchange_code(client_id: str, client_secret: str, code: str, redirect_uri: str) -> dict:
        async with httpx.AsyncClient(timeout=15.0) as client:
            token_resp = await client.post(
                "https://auth.atlassian.com/oauth/token",
                json={
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
            )
            token_data = token_resp.json()
            resources_resp = await client.get(
                "https://api.atlassian.com/oauth/token/accessible-resources",
                headers={"Authorization": f"Bearer {token_data.get('access_token', '')}"},
            )
            resources = resources_resp.json() if resources_resp.status_code == 200 else []
        cloud_id = resources[0]["id"] if resources else None
        return {**token_data, "cloud_id": cloud_id}


def _safe_json(value):
    if not value:
        return None
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return None
