from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse
import asyncio
import httpx


GAMMA_BASE = "https://gamma-api.polymarket.com"

def parse_polymarket_url(url: str):
    """
    Supports canonical and localized Polymarket URLs, for example:
      /event/world-cup-winner
      /zh/event/world-cup-winner
      /en/event/world-cup-winner
    """
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower().split(":")[0]

    if host not in {"polymarket.com", "www.polymarket.com"}:
        raise ValueError("URL must use polymarket.com")

    parts = [part for part in parsed.path.split("/") if part]

    try:
        event_pos = parts.index("event")
    except ValueError as exc:
        raise ValueError(
            "Expected a Polymarket event URL containing /event/{slug}"
        ) from exc

    if event_pos + 1 >= len(parts):
        raise ValueError("The event slug is missing from the URL")

    slug = parts[event_pos + 1]

    # Normalize localized URLs to the stable canonical path.
    normalized = urlunparse(
        ("https", "polymarket.com", f"/event/{slug}", "", "", "")
    )

    return (url, normalized, slug)

async def fetch_event_by_slug(slug: str) -> dict:
    url = f"{GAMMA_BASE}/events/slug/{slug}"
    timeout = httpx.Timeout(20)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        print(data)
    if not isinstance(data, dict):
        raise ValueError("Unexpected Polymarket event response")
    return data

def _market_choices(event: dict) -> list[dict]:
    choices = []
    for index, market in enumerate(event.get("markets") or []):
        choices.append(
            {
                "index": index,
                "id": str(market.get("id", "")),
                "slug": market.get("slug"),
                "active": market.get("active"),
                "closed": market.get("closed"),
            }
        )
    return choices

async def main():
    parsed_url = parse_polymarket_url("https://polymarket.com/event/nba-lebron-james-next-team")
    event = await fetch_event_by_slug(parsed_url[2])
    choices = _market_choices(event)
    for t in choices:
        print(t)

if __name__ == "__main__":
    asyncio.run(main())