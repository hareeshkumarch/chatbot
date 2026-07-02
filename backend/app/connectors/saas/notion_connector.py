import base64

import httpx

from app.connectors.base import BaseConnector, ConnectorContent, ConnectorResource

NOTION_VERSION = "2026-03-11"


class NotionConnector(BaseConnector):
    connector_type = "notion"
    base_url = "https://api.notion.com/v1"

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.credentials['access_token']}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        }

    async def test_connection(self) -> bool:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{self.base_url}/users/me", headers=self._headers())
        return resp.status_code == 200

    async def list_resources(self) -> list[ConnectorResource]:
        resources = []
        cursor = None
        async with httpx.AsyncClient(timeout=20.0) as client:
            while True:
                payload = {"filter": {"property": "object", "value": "page"}, "page_size": 100}
                if cursor:
                    payload["start_cursor"] = cursor
                resp = await client.post(f"{self.base_url}/search", headers=self._headers(), json=payload)
                resp.raise_for_status()
                data = resp.json()
                for page in data.get("results", []):
                    title = _page_title(page)
                    resources.append(ConnectorResource(resource_id=page["id"], name=title, kind="page"))
                if not data.get("has_more"):
                    break
                cursor = data.get("next_cursor")
        return resources

    async def fetch_content(self, resource_id: str) -> ConnectorContent:
        blocks_text: list[str] = []
        cursor = None
        async with httpx.AsyncClient(timeout=20.0) as client:
            for _ in range(10):
                params = {"page_size": 100}
                if cursor:
                    params["start_cursor"] = cursor
                resp = await client.get(f"{self.base_url}/blocks/{resource_id}/children", headers=self._headers(), params=params)
                if resp.status_code != 200:
                    break
                data = resp.json()
                for block in data.get("results", []):
                    blocks_text.append(_block_to_text(block))
                if not data.get("has_more"):
                    break
                cursor = data.get("next_cursor")
        combined = "\n".join(t for t in blocks_text if t)
        return ConnectorContent(
            resource_id=resource_id,
            title=f"Notion page {resource_id}",
            file_extension="txt",
            raw_bytes=combined.encode("utf-8"),
            source_uri=f"notion://page/{resource_id}",
        )

    async def search(self, query: str) -> list[dict]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(f"{self.base_url}/search", headers=self._headers(), json={"query": query, "page_size": 20})
        if resp.status_code != 200:
            return []
        return resp.json().get("results", [])

    @staticmethod
    def authorize_url(client_id: str, redirect_uri: str, state: str) -> str:
        return (
            "https://api.notion.com/v1/oauth/authorize"
            f"?client_id={client_id}&response_type=code&owner=user&redirect_uri={redirect_uri}&state={state}"
        )

    @staticmethod
    async def exchange_code(client_id: str, client_secret: str, code: str, redirect_uri: str) -> dict:
        basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.notion.com/v1/oauth/token",
                headers={"Authorization": f"Basic {basic}", "Content-Type": "application/json"},
                json={"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri},
            )
        return resp.json()


def _page_title(page: dict) -> str:
    properties = page.get("properties", {})
    for prop in properties.values():
        if prop.get("type") == "title":
            title_parts = prop.get("title", [])
            text = "".join(t.get("plain_text", "") for t in title_parts)
            if text:
                return text
    return page.get("id", "Untitled")


def _block_to_text(block: dict) -> str:
    block_type = block.get("type")
    content = block.get(block_type, {})
    rich_text = content.get("rich_text", [])
    text = "".join(t.get("plain_text", "") for t in rich_text)
    return text
