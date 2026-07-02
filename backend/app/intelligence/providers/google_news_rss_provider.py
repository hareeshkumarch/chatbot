import re
import xml.etree.ElementTree as ET
from html import unescape

import httpx

from app.core.circuit_breaker import get_circuit_breaker
from app.core.logging import get_logger
from app.intelligence.base import SearchResult

logger = get_logger(__name__)

GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"

COUNTRY_CODES = {
    "india": ("hi", "IN", "IN:hi"),
    "us": ("en", "US", "US:en"),
    "usa": ("en", "US", "US:en"),
    "uk": ("en", "GB", "GB:en"),
    "united kingdom": ("en", "GB", "GB:en"),
    "canada": ("en", "CA", "CA:en"),
    "australia": ("en", "AU", "AU:en"),
    "germany": ("de", "DE", "DE:de"),
    "france": ("fr", "FR", "FR:fr"),
    "japan": ("ja", "JP", "JP:ja"),
    "china": ("zh-CN", "CN", "CN:zh-CN"),
    "brazil": ("pt-BR", "BR", "BR:pt-BR"),
    "mexico": ("es", "MX", "MX:es"),
    "south korea": ("ko", "KR", "KR:ko"),
    "russia": ("ru", "RU", "RU:ru"),
    "italy": ("it", "IT", "IT:it"),
    "spain": ("es", "ES", "ES:es"),
    "netherlands": ("nl", "NL", "NL:nl"),
    "singapore": ("en", "SG", "SG:en"),
    "uae": ("en", "AE", "AE:en"),
    "south africa": ("en", "ZA", "ZA:en"),
    "nigeria": ("en", "NG", "NG:en"),
    "indonesia": ("id", "ID", "ID:id"),
    "pakistan": ("en", "PK", "PK:en"),
    "bangladesh": ("bn", "BD", "BD:bn"),
    "israel": ("he", "IL", "IL:he"),
    "turkey": ("tr", "TR", "TR:tr"),
    "egypt": ("ar", "EG", "EG:ar"),
    "saudi arabia": ("ar", "SA", "SA:ar"),
    "argentina": ("es", "AR", "AR:es"),
    "thailand": ("th", "TH", "TH:th"),
    "vietnam": ("vi", "VN", "VN:vi"),
    "philippines": ("en", "PH", "PH:en"),
    "malaysia": ("en", "MY", "MY:en"),
    "kenya": ("en", "KE", "KE:en"),
    "colombia": ("es", "CO", "CO:es"),
    "poland": ("pl", "PL", "PL:pl"),
    "sweden": ("sv", "SE", "SE:sv"),
    "switzerland": ("de", "CH", "CH:de"),
    "taiwan": ("zh-TW", "TW", "TW:zh-TW"),
    "ireland": ("en", "IE", "IE:en"),
    "new zealand": ("en", "NZ", "NZ:en"),
    "portugal": ("pt-PT", "PT", "PT:pt-PT"),
    "belgium": ("nl", "BE", "BE:nl"),
    "austria": ("de", "AT", "AT:de"),
    "norway": ("no", "NO", "NO:no"),
    "denmark": ("da", "DK", "DK:da"),
    "finland": ("fi", "FI", "FI:fi"),
    "czech republic": ("cs", "CZ", "CZ:cs"),
    "greece": ("el", "GR", "GR:el"),
    "romania": ("ro", "RO", "RO:ro"),
    "ukraine": ("uk", "UA", "UA:uk"),
    "chile": ("es", "CL", "CL:es"),
    "peru": ("es", "PE", "PE:es"),
}

_TAG_RE = re.compile(r"<[^>]+>")


def _detect_country(query: str) -> tuple[str, str, str] | None:
    lower = query.lower()
    for country, codes in COUNTRY_CODES.items():
        if country in lower:
            return codes
    return None


class GoogleNewsRSSProvider:
    name = "google_news_rss"

    def __init__(self) -> None:
        self.breaker = get_circuit_breaker("intel:google_news_rss")

    async def search_news(
        self, query: str, max_results: int = 8, location: str | None = None
    ) -> list[SearchResult]:
        async def _do() -> list[SearchResult]:
            geo = _detect_country(query)
            hl = geo[0] if geo else "en"
            gl = location or (geo[1] if geo else "US")
            ceid = geo[2] if geo else f"{gl}:en"

            params = {"q": query, "hl": hl, "gl": gl, "ceid": ceid}

            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(GOOGLE_NEWS_RSS_URL, params=params)
            resp.raise_for_status()

            root = ET.fromstring(resp.text)
            channel = root.find("channel")
            if channel is None:
                return []

            results: list[SearchResult] = []
            for item in channel.findall("item"):
                if len(results) >= max_results:
                    break
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                description = item.findtext("description", "")
                pub_date = item.findtext("pubDate")
                source_el = item.find("source")
                source_name = source_el.text if source_el is not None and source_el.text else "Google News"

                snippet = unescape(description)
                snippet = _TAG_RE.sub("", snippet).strip()

                if title and link:
                    results.append(
                        SearchResult(
                            title=title,
                            url=link,
                            snippet=snippet[:500],
                            source=source_name,
                            published_at=pub_date,
                        )
                    )
            return results

        return await self.breaker.call(_do)
