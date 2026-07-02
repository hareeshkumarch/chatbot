from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str
    published_at: str | None = None


class SearchProvider(ABC):
    name: str

    @abstractmethod
    async def search(self, query: str, max_results: int = 8, location: str | None = None) -> list[SearchResult]: ...


@dataclass
class AnsweredResult:
    answer: str
    citations: list[str] = field(default_factory=list)


class AnswerProvider(ABC):
    name: str

    @abstractmethod
    async def answer(self, query: str) -> AnsweredResult: ...


@dataclass
class TrendPoint:
    date: str
    value: int


@dataclass
class TrendsResult:
    keyword: str
    points: list[TrendPoint]
    related_queries: list[str] = field(default_factory=list)


class TrendsProvider(ABC):
    name: str

    @abstractmethod
    async def interest_over_time(self, keyword: str, geo: str = "") -> TrendsResult: ...


@dataclass
class FinanceQuote:
    symbol: str
    price: float
    currency: str
    change_percent: float
    market_cap: float | None = None
    pe_ratio: float | None = None
    fifty_two_week_high: float | None = None
    fifty_two_week_low: float | None = None


@dataclass
class FinanceHistoryPoint:
    date: str
    close: float
    volume: int


class FinanceProvider(ABC):
    name: str

    @abstractmethod
    async def quote(self, symbol: str) -> FinanceQuote: ...

    @abstractmethod
    async def history(self, symbol: str, period: str = "1mo") -> list[FinanceHistoryPoint]: ...


@dataclass
class DemographicsResult:
    place: str
    population: int | None
    median_household_income: int | None
    median_age: float | None


class DemographicsProvider(ABC):
    name: str

    @abstractmethod
    async def lookup(self, place: str) -> DemographicsResult: ...
