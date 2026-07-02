import httpx

from app.connectors.base import BaseConnector, ConnectorContent, ConnectorResource
from app.connectors.saas._atlassian import extract_adf_text


class JiraConnector(BaseConnector):
    connector_type = "jira"

    def _base_url(self) -> str:
        return f"https://api.atlassian.com/ex/jira/{self.credentials['cloud_id']}"

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.credentials['access_token']}", "Accept": "application/json"}

    async def test_connection(self) -> bool:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{self._base_url()}/rest/api/3/myself", headers=self._headers())
        return resp.status_code == 200

    async def list_resources(self) -> list[ConnectorResource]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(f"{self._base_url()}/rest/api/3/project/search", headers=self._headers())
        resp.raise_for_status()
        return [ConnectorResource(resource_id=p["key"], name=p["name"], kind="project") for p in resp.json().get("values", [])]

    async def fetch_content(self, resource_id: str) -> ConnectorContent:
        jql = f"project = {resource_id} ORDER BY updated DESC"
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(
                f"{self._base_url()}/rest/api/3/search",
                headers=self._headers(),
                params={"jql": jql, "maxResults": 100, "fields": "summary,description,status,issuetype"},
            )
        resp.raise_for_status()
        lines = [f"Project: {resource_id}"]
        for issue in resp.json().get("issues", []):
            fields = issue["fields"]
            description = extract_adf_text(fields.get("description"))
            lines.append(f"{issue['key']} [{fields['status']['name']}] {fields['summary']}\n{description}")
        combined = "\n\n".join(lines)
        return ConnectorContent(
            resource_id=resource_id,
            title=f"Jira {resource_id}",
            file_extension="txt",
            raw_bytes=combined.encode("utf-8"),
            source_uri=f"jira://project/{resource_id}",
        )

    async def search_jql(self, jql: str) -> list[dict]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(f"{self._base_url()}/rest/api/3/search", headers=self._headers(), params={"jql": jql, "maxResults": 50})
        if resp.status_code != 200:
            return []
        return resp.json().get("issues", [])

    @staticmethod
    def authorize_url(client_id: str, redirect_uri: str, state: str) -> str:
        scopes = "read:jira-work read:jira-user offline_access"
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
