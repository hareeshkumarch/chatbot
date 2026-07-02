import httpx

from app.connectors.base import BaseConnector, ConnectorContent, ConnectorResource


class SlackConnector(BaseConnector):
    connector_type = "slack"
    base_url = "https://slack.com/api"

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.credentials['access_token']}"}

    async def test_connection(self) -> bool:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(f"{self.base_url}/auth.test", headers=self._headers())
        data = resp.json()
        return bool(data.get("ok"))

    async def list_resources(self) -> list[ConnectorResource]:
        resources = []
        cursor = None
        async with httpx.AsyncClient(timeout=20.0) as client:
            while True:
                params = {"limit": 200, "types": "public_channel,private_channel"}
                if cursor:
                    params["cursor"] = cursor
                resp = await client.get(f"{self.base_url}/conversations.list", headers=self._headers(), params=params)
                data = resp.json()
                if not data.get("ok"):
                    break
                for channel in data.get("channels", []):
                    resources.append(ConnectorResource(resource_id=channel["id"], name=channel.get("name", channel["id"]), kind="channel"))
                cursor = data.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break
        return resources

    async def fetch_content(self, resource_id: str) -> ConnectorContent:
        messages: list[str] = []
        cursor = None
        async with httpx.AsyncClient(timeout=20.0) as client:
            for _ in range(5):
                params = {"channel": resource_id, "limit": 200}
                if cursor:
                    params["cursor"] = cursor
                resp = await client.get(f"{self.base_url}/conversations.history", headers=self._headers(), params=params)
                data = resp.json()
                if not data.get("ok"):
                    break
                for message in data.get("messages", []):
                    text = message.get("text", "")
                    user = message.get("user", "unknown")
                    if text:
                        messages.append(f"{user}: {text}")
                cursor = data.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break
        combined = "\n".join(reversed(messages))
        return ConnectorContent(
            resource_id=resource_id,
            title=f"Slack #{resource_id}",
            file_extension="txt",
            raw_bytes=combined.encode("utf-8"),
            source_uri=f"slack://channel/{resource_id}",
        )

    async def search(self, query: str) -> list[dict]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(f"{self.base_url}/search.messages", headers=self._headers(), params={"query": query, "count": 20})
        data = resp.json()
        if not data.get("ok"):
            return []
        return data.get("messages", {}).get("matches", [])

    @staticmethod
    def authorize_url(client_id: str, redirect_uri: str, state: str) -> str:
        scopes = "channels:history,channels:read,groups:history,groups:read,search:read"
        return (
            "https://slack.com/oauth/v2/authorize"
            f"?client_id={client_id}&scope={scopes}&redirect_uri={redirect_uri}&state={state}"
        )

    @staticmethod
    async def exchange_code(client_id: str, client_secret: str, code: str, redirect_uri: str) -> dict:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://slack.com/api/oauth.v2.access",
                data={"client_id": client_id, "client_secret": client_secret, "code": code, "redirect_uri": redirect_uri},
            )
        return resp.json()
