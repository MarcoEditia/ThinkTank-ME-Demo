from __future__ import annotations

from datetime import datetime, timezone

from src.agents import research_evidence, run_all_experts
from src.aggregation import aggregate_forecasts
from src.polymarket import inspect_polymarket_url
from src.schemas import AgentRole, EvidencePacket, ForecastResponse, MarketContext


class ForecastError(Exception):
    """Raised when the forecasting pipeline fails to execute."""
    pass


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

        # Only the contract—not the live market probability—is sent to research
        # and the independent expert agents.
        if use_research:
            evidence = await research_evidence(context.forecast_contract)
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
        if use_research and not evidence.evidence:
            warnings.append("The research agent returned no evidence items.")
        if not use_research:
            warnings.append("Web research was disabled for this forecast.")
        if aggregate.agreement == "low":
            warnings.append("Expert forecasts have high dispersion.")

        return ForecastResponse(
            forecast_contract=context.forecast_contract,
            market_snapshot=context.market_snapshot,
            evidence_packet=evidence,
            expert_forecasts=expert_forecasts,
            aggregate=aggregate,
            warnings=warnings,
        ) 
    # except Exception as exc:
    #     raise ForecastError(f"Forecasting pipeline failed for {url}") from exc
