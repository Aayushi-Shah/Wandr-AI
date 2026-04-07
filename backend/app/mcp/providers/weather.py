"""Open-Meteo weather provider — free, no API key required.

Tool: "get_weather"
Params: { location, start_date, end_date }
Returns: { daily: { date, temp_max_c, temp_min_c, precipitation_mm, description } }
"""

from typing import Any

import httpx

_WMO_DESCRIPTIONS: dict[int, str] = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Icy fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow",
    80: "Rain showers", 81: "Rain showers", 82: "Violent rain showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with hail",
}


class OpenMeteoProvider:
    """Direct HTTP client for Open-Meteo — no API key needed."""

    def __init__(self, base_url: str, geocoding_url: str) -> None:
        self._base_url = base_url
        self._geocoding_url = geocoding_url

    async def call(self, tool: str, params: dict[str, Any]) -> dict[str, Any]:
        location: str = params["location"]
        start_date: str = params["start_date"]   # YYYY-MM-DD
        end_date: str = params["end_date"]       # YYYY-MM-DD

        lat, lon, resolved = await self._geocode(location)

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self._base_url}/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
                    "start_date": start_date,
                    "end_date": end_date,
                    "timezone": "auto",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        daily = data.get("daily", {})
        dates = daily.get("time", [])
        temp_max = daily.get("temperature_2m_max", [])
        temp_min = daily.get("temperature_2m_min", [])
        precip = daily.get("precipitation_sum", [])
        codes = daily.get("weathercode", [])

        return {
            "location": resolved,
            "days": [
                {
                    "date": dates[i],
                    "temp_max_c": temp_max[i],
                    "temp_min_c": temp_min[i],
                    "precipitation_mm": precip[i],
                    "description": _WMO_DESCRIPTIONS.get(int(codes[i]), "Unknown"),
                }
                for i in range(len(dates))
            ],
        }

    async def _geocode(self, location: str) -> tuple[float, float, str]:
        """Resolve a place name to lat/lon using Open-Meteo geocoding."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self._geocoding_url}/search",
                params={"name": location, "count": 1, "language": "en", "format": "json"},
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])

        if not results:
            raise ValueError(f"Location not found: {location!r}")

        r = results[0]
        name = f"{r.get('name', location)}, {r.get('country', '')}"
        return float(r["latitude"]), float(r["longitude"]), name
