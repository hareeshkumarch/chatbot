import asyncio

from app.core.logging import get_logger
from app.intelligence.base import FinanceHistoryPoint, FinanceProvider, FinanceQuote

logger = get_logger(__name__)


class YahooFinanceProvider(FinanceProvider):
    name = "yahoo_finance"

    async def quote(self, symbol: str) -> FinanceQuote:
        loop = asyncio.get_event_loop()

        def _fetch() -> FinanceQuote:
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            info = ticker.info
            price = info.get("currentPrice") or info.get("regularMarketPrice") or 0.0
            return FinanceQuote(
                symbol=symbol.upper(),
                price=float(price),
                currency=info.get("currency", "USD"),
                change_percent=float(info.get("regularMarketChangePercent") or 0.0),
                market_cap=info.get("marketCap"),
                pe_ratio=info.get("trailingPE"),
                fifty_two_week_high=info.get("fiftyTwoWeekHigh"),
                fifty_two_week_low=info.get("fiftyTwoWeekLow"),
            )

        return await loop.run_in_executor(None, _fetch)

    async def history(self, symbol: str, period: str = "1mo") -> list[FinanceHistoryPoint]:
        loop = asyncio.get_event_loop()

        def _fetch() -> list[FinanceHistoryPoint]:
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            frame = ticker.history(period=period)
            points = []
            for timestamp, row in frame.iterrows():
                points.append(FinanceHistoryPoint(date=str(timestamp.date()), close=float(row["Close"]), volume=int(row["Volume"])))
            return points

        return await loop.run_in_executor(None, _fetch)
