import httpx

from app.connectors.base import BaseConnector, ConnectorContent, ConnectorResource

LINEAR_URL = "https://api.linear.app/graphql"


class LinearConnector(BaseConnector):
    connector_type = "linear"

    def _headers(self) -> dict:
        return {"Authorization": self.credentials["api_key"], "Content-Type": "application/json"}

    async def _query(self, client: httpx.AsyncClient, query: str, variables: dict | None = None) -> dict:
        resp = await client.post(LINEAR_URL, headers=self._headers(), json={"query": query, "variables": variables or {}})
        resp.raise_for_status()
        data = resp.json()
        if data.get("errors"):
            raise RuntimeError(str(data["errors"]))
        return data.get("data", {})

    async def test_connection(self) -> bool:
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                await self._query(client, "{ viewer { id } }")
                return True
            except Exception:
                return False

    async def list_resources(self) -> list[ConnectorResource]:
        query = """
        query Issues($after: String) {
          issues(first: 100, after: $after) {
            nodes { id identifier title }
            pageInfo { hasNextPage endCursor }
          }
        }
        """
        resources = []
        cursor = None
        async with httpx.AsyncClient(timeout=20.0) as client:
            for _ in range(10):
                data = await self._query(client, query, {"after": cursor})
                issues = data.get("issues", {})
                for node in issues.get("nodes", []):
                    resources.append(ConnectorResource(resource_id=node["id"], name=f"{node['identifier']}: {node['title']}", kind="issue"))
                page_info = issues.get("pageInfo", {})
                if not page_info.get("hasNextPage"):
                    break
                cursor = page_info.get("endCursor")
        return resources

    async def fetch_content(self, resource_id: str) -> ConnectorContent:
        query = """
        query Issue($id: String!) {
          issue(id: $id) {
            identifier
            title
            description
            state { name }
            comments { nodes { body } }
          }
        }
        """
        async with httpx.AsyncClient(timeout=20.0) as client:
            data = await self._query(client, query, {"id": resource_id})
        issue = data.get("issue", {})
        comments = [c.get("body", "") for c in issue.get("comments", {}).get("nodes", [])]
        lines = [
            f"{issue.get('identifier', resource_id)} [{issue.get('state', {}).get('name', '')}] {issue.get('title', '')}",
            issue.get("description") or "",
            *comments,
        ]
        combined = "\n\n".join(line for line in lines if line)
        return ConnectorContent(
            resource_id=resource_id,
            title=f"Linear {issue.get('identifier', resource_id)}",
            file_extension="txt",
            raw_bytes=combined.encode("utf-8"),
            source_uri=f"linear://issue/{resource_id}",
        )

    async def search(self, query: str) -> list[dict]:
        gql = """
        query Search($term: String!) {
          searchIssues(term: $term, first: 20) {
            nodes { id identifier title }
          }
        }
        """
        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                data = await self._query(client, gql, {"term": query})
            except Exception:
                return []
        return data.get("searchIssues", {}).get("nodes", [])
