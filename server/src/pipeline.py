from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from src.agents import DEFAULT_AGENT_ROLES, research_evidence, run_all_experts
from src.aggregation import aggregate_forecasts
from src.config import settings
from src.forecast_cache import ForecastCache, build_forecast_cache_key
from src.polymarket import inspect_polymarket_url
from src.schemas import AgentRole, EvidencePacket, ForecastResponse, MarketContext


class ForecastError(Exception):
    """Raised when the forecasting pipeline fails to execute."""
    pass


forecast_cache = ForecastCache(
    settings.forecast_cache_db, settings.forecast_cache_ttl_seconds
)


async def inspect_market(
    url: str,
    market_query: str | None = None,
    market_index: int | None = None,
) -> MarketContext:
    return await inspect_polymarket_url(
        url=url,
        market_query=market_query,
        market_index=market_index,
        include_raw_event=False,
    )


async def run_forecast(
    url: str,
    market_query: str | None = None,
    market_index: int | None = None,
    selected_agents: list[AgentRole] | None = None,
    use_research: bool = True,
) -> ForecastResponse:
    # try:
        context = await inspect_market(
            url,
            market_query=market_query,
            market_index=market_index,
        )
        agent_roles = selected_agents or list(DEFAULT_AGENT_ROLES)
        cache_key = build_forecast_cache_key(
            market_id=context.forecast_contract.market_id,
            selected_agents=agent_roles,
            use_research=use_research,
            claude_model=settings.claude_model,
            cache_version=settings.forecast_cache_version,
        )
        cached_forecast = forecast_cache.get(cache_key)
        if cached_forecast:
            cached_response = ForecastResponse.model_validate_json(
                cached_forecast.response_json
            )
            market_probability = context.market_snapshot.target_probability
            aggregate = cached_response.aggregate.model_copy(
                update={
                    "market_probability": market_probability,
                    "probability_gap": (
                        cached_response.aggregate.probability - market_probability
                        if market_probability is not None
                        else None
                    ),
                }
            )
            return cached_response.model_copy(
                update={
                    "forecast_contract": context.forecast_contract,
                    "market_snapshot": context.market_snapshot,
                    "aggregate": aggregate,
                    "cache_hit": True,
                    "cached_at": cached_forecast.created_at,
                }
            )

        # Only the contract—not the live market probability—is sent to research
        # and the independent expert agents.
        research_failed = False
        if use_research:
            try:
                evidence = await asyncio.wait_for(
                    research_evidence(context.forecast_contract),
                    timeout=settings.research_timeout_seconds,
                )
            except Exception:
                research_failed = True
                evidence = EvidencePacket(
                    evidence_cutoff_time=datetime.now(timezone.utc).isoformat(),
                    key_unknowns=[
                        "Web research could not complete for this forecast."
                    ],
                )
        else:
            evidence = EvidencePacket(
                evidence_cutoff_time=datetime.now(timezone.utc).isoformat(),
                key_unknowns=["Web research was disabled for this forecast."],
            )
        expert_forecasts = await run_all_experts(
            context.forecast_contract,
            evidence,
            experts=selected_agents,
        )
        aggregate = aggregate_forecasts(
            expert_forecasts,
            context.market_snapshot.target_probability,
        )
        warnings: list[str] = []
        if context.market_snapshot.closed:
            warnings.append("The selected market is already closed.")
        if not context.forecast_contract.resolution_criteria:
            warnings.append("Resolution criteria are missing or empty.")
        if research_failed:
            warnings.append(
                "Web research could not complete; this forecast used no web evidence."
            )
        elif use_research and not evidence.evidence:
            warnings.append("The research agent returned no evidence items.")
        if not use_research:
            warnings.append("Web research was disabled for this forecast.")
        if aggregate.agreement == "low":
            warnings.append("Expert forecasts have high dispersion.")

        response = ForecastResponse(
            forecast_contract=context.forecast_contract,
            market_snapshot=context.market_snapshot,
            evidence_packet=evidence,
            expert_forecasts=expert_forecasts,
            aggregate=aggregate,
            warnings=warnings,
        )
        if not research_failed:
            forecast_cache.put(
                cache_key,
                context.forecast_contract.market_id,
                response.model_dump_json(),
            )
        return response
    # except Exception as exc:
    #     raise ForecastError(f"Forecasting pipeline failed for {url}") from exc
