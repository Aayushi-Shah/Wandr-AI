"""Frankfurter currency provider — free, no API key required.

Tool: "get_exchange_rate"
Params: { from_currency, to_currency, amount? }
Returns: { from, to, rate, amount, converted }
"""

from typing import Any

import httpx


class FrankfurterProvider:
    """Direct HTTP client for Frankfurter exchange rate API."""

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url

    async def call(self, tool: str, params: dict[str, Any]) -> dict[str, Any]:
        from_currency: str = params["from_currency"].upper()
        to_currency: str = params["to_currency"].upper()
        amount: float = float(params.get("amount", 1.0))

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self._base_url}/latest",
                params={"from": from_currency, "to": to_currency},
            )
            resp.raise_for_status()
            data = resp.json()

        rate = data["rates"][to_currency]
        return {
            "from": from_currency,
            "to": to_currency,
            "rate": rate,
            "amount": amount,
            "converted": round(amount * rate, 2),
        }
