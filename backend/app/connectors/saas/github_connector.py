import base64

import httpx

from app.connectors.base import BaseConnector, ConnectorContent, ConnectorResource


class GitHubConnector(BaseConnector):
    connector_type = "github"
    base_url = "https://api.github.com"

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.credentials['access_token']}", "Accept": "application/vnd.github+json"}

    async def test_connection(self) -> bool:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{self.base_url}/user", headers=self._headers())
        return resp.status_code == 200

    async def list_resources(self) -> list[ConnectorResource]:
        resources = []
        org_or_user = self.config.get("owner")
        repo_filter = self.config.get("repo")
        async with httpx.AsyncClient(timeout=20.0) as client:
            if repo_filter:
                resources.append(ConnectorResource(resource_id=f"{org_or_user}/{repo_filter}", name=repo_filter, kind="repo"))
            else:
                resp = await client.get(f"{self.base_url}/users/{org_or_user}/repos", headers=self._headers(), params={"per_page": 100})
                for repo in resp.json():
                    if isinstance(repo, dict) and "full_name" in repo:
                        resources.append(ConnectorResource(resource_id=repo["full_name"], name=repo["name"], kind="repo", size_bytes=repo.get("size")))
        return resources

    async def fetch_content(self, resource_id: str) -> ConnectorContent:
        async with httpx.AsyncClient(timeout=20.0) as client:
            issues_resp = await client.get(f"{self.base_url}/repos/{resource_id}/issues", headers=self._headers(), params={"state": "all", "per_page": 50})
            readme_resp = await client.get(f"{self.base_url}/repos/{resource_id}/readme", headers=self._headers())

        lines = [f"Repository: {resource_id}"]
        if readme_resp.status_code == 200:
            content = readme_resp.json().get("content", "")
            try:
                decoded = base64.b64decode(content).decode("utf-8", errors="ignore")
                lines.append("README:\n" + decoded)
            except Exception:
                pass
        if issues_resp.status_code == 200:
            for issue in issues_resp.json():
                if "pull_request" in issue:
                    continue
                lines.append(f"Issue #{issue['number']} [{issue['state']}]: {issue['title']}\n{issue.get('body') or ''}")
        combined = "\n\n".join(lines)
        return ConnectorContent(
            resource_id=resource_id,
            title=resource_id,
            file_extension="txt",
            raw_bytes=combined.encode("utf-8"),
            source_uri=f"https://github.com/{resource_id}",
        )

    async def search_code(self, query: str) -> list[dict]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(f"{self.base_url}/search/code", headers=self._headers(), params={"q": query})
        if resp.status_code != 200:
            return []
        return resp.json().get("items", [])

    @staticmethod
    def authorize_url(client_id: str, redirect_uri: str, state: str) -> str:
        return (
            "https://github.com/login/oauth/authorize"
            f"?client_id={client_id}&redirect_uri={redirect_uri}&scope=repo,read:org&state={state}"
        )

    @staticmethod
    async def exchange_code(client_id: str, client_secret: str, code: str, redirect_uri: str) -> dict:
        headers = {"Accept": "application/json"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://github.com/login/oauth/access_token",
                headers=headers,
                data={"client_id": client_id, "client_secret": client_secret, "code": code, "redirect_uri": redirect_uri},
            )
        return resp.json()
