from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse

import httpx

from src.config import settings
from src.schemas import (
    ForecastContract,
    MarketContext,
    MarketSnapshot,
    ParsedPolymarketURL,
)

GAMMA_BASE = "https://gamma-api.polymarket.com"


def parse_polymarket_url(url: str) -> ParsedPolymarketURL:
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

    return ParsedPolymarketURL(
        original_url=url,
        normalized_url=normalized,
        slug=slug,
    )


async def fetch_event_by_slug(slug: str) -> dict:
    url = f"{GAMMA_BASE}/events/slug/{slug}"
    timeout = httpx.Timeout(settings.request_timeout_seconds)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        print(data)
    if not isinstance(data, dict):
        raise ValueError("Unexpected Polymarket event response")
    return data


def _jsonish_list(value: object) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else [parsed]
        except json.JSONDecodeError:
            return [value]
    return [value]


def _float_or_none(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_tag_names(event: dict) -> list[str]:
    result: list[str] = []
    for tag in event.get("tags") or []:
        if isinstance(tag, dict):
            value = tag.get("label") or tag.get("name") or tag.get("slug")
        else:
            value = str(tag)
        if value:
            result.append(str(value))
    return result


def _market_question(market: dict) -> str:
    return str(market.get("question") or market.get("title") or "")


def _market_choices(event: dict) -> list[dict]:
    choices = []
    for index, market in enumerate(event.get("markets") or []):
        choices.append(
            {
                "index": index,
                "id": str(market.get("id", "")),
                "slug": market.get("slug"),
                "question": _market_question(market),
                "active": market.get("active"),
                "closed": market.get("closed"),
            }
        )
    return choices


def select_target_market(
    event: dict,
    market_query: str | None = None,
    market_index: int | None = None,
) -> tuple[int, dict]:
    markets = event.get("markets") or []
    if not markets:
        raise ValueError("The event contains no child markets")

    if market_query:
        needle = market_query.strip().casefold()

        exact = [
            (index, market)
            for index, market in enumerate(markets)
            if needle in {
                _market_question(market).casefold(),
                str(market.get("slug") or "").casefold(),
            }
        ]
        if len(exact) == 1:
            return exact[0]

        partial = [
            (index, market)
            for index, market in enumerate(markets)
            if needle in _market_question(market).casefold()
            or needle in str(market.get("slug") or "").casefold()
        ]
        if len(partial) == 1:
            return partial[0]
        if len(partial) > 1:
            candidates = [_market_question(market) for _, market in partial[:10]]
            raise ValueError(
                "market_query matched multiple child markets: "
                + "; ".join(candidates)
            )
        available_options = "\n\n".join(f"- {_market_question(m)}" for m in markets)
        raise ValueError(f"No child market matched market_query={market_query!r} \n\nPlease select the following child market:\n\n{available_options}")

    if market_index is not None:
        if market_index >= len(markets):
            raise IndexError(
                f"market_index={market_index} is invalid; "
                f"event has {len(markets)} markets"
            )
        return market_index, markets[market_index]

    if len(markets) == 1:
        return 0, markets[0]

    available_options = "\n\n".join(f"- {_market_question(m)}" for m in markets)
    raise ValueError(
        "This Event contains multiple child markets. "
        "Supply market_query (recommended) or market_index."
        f"\n\nPlease select the following child market:\n\n{available_options}"
    )


def build_market_context(
    parsed_url: ParsedPolymarketURL,
    event: dict,
    market_query: str | None = None,
    market_index: int | None = None,
    include_raw_event: bool = False,
) -> MarketContext:
    selected_index, market = select_target_market(
        event,
        market_query=market_query,
        market_index=market_index,
    )

    outcomes = [str(x) for x in _jsonish_list(market.get("outcomes"))]
    prices = [_float_or_none(x) for x in _jsonish_list(market.get("outcomePrices"))]

    probability_map = {
        outcome: price
        for outcome, price in zip(outcomes, prices)
        if price is not None
    }

    target_outcome = next(
        (outcome for outcome in outcomes if outcome.lower() == "yes"),
        outcomes[0] if outcomes else "Yes",
    )

    description = market.get("description") or event.get("description") or ""
    resolution_source = (
        market.get("resolutionSource") or event.get("resolutionSource")
    )

    contract = ForecastContract(
        event_id=str(event.get("id", "")),
        market_id=str(market.get("id", "")),
        event_slug=str(event.get("slug") or parsed_url.slug),
        market_slug=market.get("slug"),
        question=_market_question(market) or str(event.get("title") or ""),
        description=str(description),
        target_outcome=target_outcome,
        outcomes=outcomes,
        deadline=market.get("endDate") or event.get("endDate"),
        resolution_source=resolution_source,
        resolution_criteria=str(description),
        category=event.get("category"),
        tags=_extract_tag_names(event),
    )

    snapshot = MarketSnapshot(
        outcome_probabilities=probability_map,
        target_probability=probability_map.get(target_outcome),
        volume=_float_or_none(market.get("volume") or event.get("volume")),
        liquidity=_float_or_none(
            market.get("liquidity") or event.get("liquidity")
        ),
        best_bid=_float_or_none(market.get("bestBid")),
        best_ask=_float_or_none(market.get("bestAsk")),
        spread=_float_or_none(market.get("spread")),
        last_trade_price=_float_or_none(market.get("lastTradePrice")),
        active=market.get("active"),
        closed=market.get("closed"),
        snapshot_time=datetime.now(timezone.utc).isoformat(),
    )

    choices = _market_choices(event)
    # Helpful marker for debugging/display.
    for choice in choices:
        choice["selected"] = choice["index"] == selected_index

    return MarketContext(
        parsed_url=parsed_url,
        forecast_contract=contract,
        market_snapshot=snapshot,
        available_markets=choices,
        raw_event=event if include_raw_event else None,
    )


async def inspect_polymarket_url(
    url: str,
    market_query: str | None = None,
    market_index: int | None = None,
    include_raw_event: bool = False,
) -> MarketContext:
    parsed = parse_polymarket_url(url)
    event = await fetch_event_by_slug(parsed.slug)
    return build_market_context(
        parsed,
        event,
        market_query=market_query,
        market_index=market_index,
        include_raw_event=include_raw_event,
    )
 