import asyncio

from app.core.logging import get_logger
from app.intelligence.base import TrendPoint, TrendsProvider, TrendsResult

logger = get_logger(__name__)


class GoogleTrendsProvider(TrendsProvider):
    name = "google_trends"

    async def interest_over_time(self, keyword: str, geo: str = "") -> TrendsResult:
        loop = asyncio.get_event_loop()

        def _fetch() -> TrendsResult:
            from pytrends_modern import TrendReq

            client = TrendReq(hl="en-US", tz=0)
            client.build_payload(kw_list=[keyword], timeframe="today 3-m", geo=geo)
            frame = client.interest_over_time()
            points = []
            if not frame.empty:
                for timestamp, row in frame.iterrows():
                    points.append(TrendPoint(date=str(timestamp.date()), value=int(row[keyword])))
            related_queries: list[str] = []
            try:
                related = client.related_queries()
                top = related.get(keyword, {}).get("top")
                if top is not None and not top.empty:
                    related_queries = top["query"].head(5).tolist()
            except Exception as exc:
                logger.warning(f"google trends related queries lookup failed: {exc}")
            return TrendsResult(keyword=keyword, points=points, related_queries=related_queries)

        return await loop.run_in_executor(None, _fetch)
