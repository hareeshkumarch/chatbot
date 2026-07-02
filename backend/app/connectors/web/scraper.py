import asyncio
import time
import urllib.robotparser
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.connectors.base import BaseConnector, ConnectorContent, ConnectorResource

USER_AGENT = "EnterpriseAIPlatform-Ingestor/1.0 (+respectful-crawler)"
MIN_DELAY_SECONDS = 1.0


class RobotsCache:
    def __init__(self):
        self._cache: dict[str, urllib.robotparser.RobotFileParser] = {}

    async def is_allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin not in self._cache:
            parser = urllib.robotparser.RobotFileParser()
            parser.set_url(f"{origin}/robots.txt")
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(f"{origin}/robots.txt", headers={"User-Agent": USER_AGENT})
                if resp.status_code == 200:
                    parser.parse(resp.text.splitlines())
                else:
                    parser.parse([])
            except Exception:
                parser.parse([])
            self._cache[origin] = parser
        return self._cache[origin].can_fetch(USER_AGENT, url)


_robots_cache = RobotsCache()


class WebScraperConnector(BaseConnector):
    connector_type = "web"

    async def test_connection(self) -> bool:
        urls = self.config.get("urls", [])
        if not urls:
            return False
        return await _robots_cache.is_allowed(urls[0])

    async def list_resources(self) -> list[ConnectorResource]:
        urls = self.config.get("urls", [])
        return [ConnectorResource(resource_id=url, name=url, kind="page") for url in urls]

    async def fetch_content(self, resource_id: str) -> ConnectorContent:
        allowed = await _robots_cache.is_allowed(resource_id)
        if not allowed:
            raise PermissionError(f"robots.txt disallows fetching {resource_id}")
        await asyncio.sleep(MIN_DELAY_SECONDS)
        headers = {"User-Agent": USER_AGENT}
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            resp = await client.get(resource_id, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()
        title = soup.title.string.strip() if soup.title and soup.title.string else resource_id
        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        cleaned = "\n".join(lines)
        return ConnectorContent(
            resource_id=resource_id,
            title=title,
            file_extension="txt",
            raw_bytes=cleaned.encode("utf-8"),
            source_uri=resource_id,
        )

    async def sync(self) -> list[ConnectorContent]:
        contents = []
        last_call = 0.0
        for resource in await self.list_resources():
            elapsed = time.monotonic() - last_call
            if elapsed < MIN_DELAY_SECONDS:
                await asyncio.sleep(MIN_DELAY_SECONDS - elapsed)
            last_call = time.monotonic()
            try:
                contents.append(await self.fetch_content(resource.resource_id))
            except Exception:
                continue
        return contents
