import httpx

from app.connectors.base import BaseConnector, ConnectorContent, ConnectorResource


class ZendeskConnector(BaseConnector):
    connector_type = "zendesk"

    def _base_url(self) -> str:
        return f"https://{self.config['subdomain']}.zendesk.com/api/v2"

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.credentials['access_token']}"}

    async def test_connection(self) -> bool:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{self._base_url()}/users/me", headers=self._headers())
        return resp.status_code == 200

    async def list_resources(self) -> list[ConnectorResource]:
        resources = []
        url = f"{self._base_url()}/tickets"
        params = {"per_page": 100}
        async with httpx.AsyncClient(timeout=20.0) as client:
            for _ in range(10):
                resp = await client.get(url, headers=self._headers(), params=params)
                resp.raise_for_status()
                data = resp.json()
                for ticket in data.get("tickets", []):
                    resources.append(ConnectorResource(resource_id=str(ticket["id"]), name=ticket.get("subject", str(ticket["id"])), kind="ticket"))
                next_url = data.get("next_page")
                if not next_url:
                    break
                url, params = next_url, None
        return resources

    async def fetch_content(self, resource_id: str) -> ConnectorContent:
        async with httpx.AsyncClient(timeout=20.0) as client:
            ticket_resp = await client.get(f"{self._base_url()}/tickets/{resource_id}", headers=self._headers())
            ticket_resp.raise_for_status()
            ticket = ticket_resp.json().get("ticket", {})
            comments_resp = await client.get(f"{self._base_url()}/tickets/{resource_id}/comments", headers=self._headers())
            comments = comments_resp.json().get("comments", []) if comments_resp.status_code == 200 else []

        lines = [f"Ticket #{resource_id}: {ticket.get('subject', '')}", f"Status: {ticket.get('status', '')}"]
        for comment in comments:
            lines.append(comment.get("plain_body") or comment.get("body", ""))
        combined = "\n\n".join(lines)
        return ConnectorContent(
            resource_id=resource_id,
            title=f"Zendesk ticket #{resource_id}",
            file_extension="txt",
            raw_bytes=combined.encode("utf-8"),
            source_uri=f"zendesk://ticket/{resource_id}",
        )

    async def search(self, query: str) -> list[dict]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(
                f"{self._base_url()}/search",
                headers=self._headers(),
                params={"query": f"type:ticket {query}"},
            )
        if resp.status_code != 200:
            return []
        return resp.json().get("results", [])

    @staticmethod
    def authorize_url(client_id: str, redirect_uri: str, state: str, subdomain: str = "") -> str:
        scopes = "tickets:read users:read"
        return (
            f"https://{subdomain}.zendesk.com/oauth/authorizations/new"
            f"?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope={scopes}&state={state}"
        )

    @staticmethod
    async def exchange_code(client_id: str, client_secret: str, code: str, redirect_uri: str, subdomain: str = "") -> dict:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"https://{subdomain}.zendesk.com/oauth/tokens",
                json={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "scope": "tickets:read users:read",
                },
            )
        return resp.json()
