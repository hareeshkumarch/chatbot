import httpx

from app.core.circuit_breaker import get_circuit_breaker
from app.core.logging import get_logger
from app.intelligence.base import DemographicsProvider, DemographicsResult

logger = get_logger(__name__)

STATE_FIPS: dict[str, str] = {
    "alabama": "01", "alaska": "02", "arizona": "04", "arkansas": "05", "california": "06",
    "colorado": "08", "connecticut": "09", "delaware": "10", "florida": "12", "georgia": "13",
    "hawaii": "15", "idaho": "16", "illinois": "17", "indiana": "18", "iowa": "19",
    "kansas": "20", "kentucky": "21", "louisiana": "22", "maine": "23", "maryland": "24",
    "massachusetts": "25", "michigan": "26", "minnesota": "27", "mississippi": "28", "missouri": "29",
    "montana": "30", "nebraska": "31", "nevada": "32", "new hampshire": "33", "new jersey": "34",
    "new mexico": "35", "new york": "36", "north carolina": "37", "north dakota": "38", "ohio": "39",
    "oklahoma": "40", "oregon": "41", "pennsylvania": "42", "rhode island": "44", "south carolina": "45",
    "south dakota": "46", "tennessee": "47", "texas": "48", "utah": "49", "vermont": "50",
    "virginia": "51", "washington": "53", "west virginia": "54", "wisconsin": "55", "wyoming": "56",
    "district of columbia": "11",
}


class CensusDemographicsProvider(DemographicsProvider):
    name = "census"
    base_url = "https://api.census.gov/data/2022/acs/acs5"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.breaker = get_circuit_breaker("intel:census")

    async def lookup(self, place: str) -> DemographicsResult:
        fips = STATE_FIPS.get(place.strip().lower())
        if fips is None:
            raise ValueError(f"demographics lookup currently supports US states only, got: {place}")

        async def _do() -> DemographicsResult:
            params = {
                "get": "NAME,B01003_001E,B19013_001E,B01002_001E",
                "for": f"state:{fips}",
                "key": self.api_key,
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(self.base_url, params=params, follow_redirects=True)
            resp.raise_for_status()
            rows = resp.json()
            header, values = rows[0], rows[1]
            record = dict(zip(header, values, strict=True))
            return DemographicsResult(
                place=record.get("NAME", place),
                population=int(record["B01003_001E"]) if record.get("B01003_001E") else None,
                median_household_income=int(record["B19013_001E"]) if record.get("B19013_001E") not in (None, "-666666666") else None,
                median_age=float(record["B01002_001E"]) if record.get("B01002_001E") not in (None, "-666666666") else None,
            )

        return await self.breaker.call(_do)
