import asyncio

from src import pipeline
from src.forecast_cache import ForecastCache
from src.schemas import (
    EvidencePacket,
    ExpertForecast,
    ForecastContract,
    MarketContext,
    MarketSnapshot,
    ParsedPolymarketURL,
)


def test_forecast_continues_when_research_fails(monkeypatch, tmp_path):
    contract = ForecastContract(
        event_id="event-1",
        market_id="market-1",
        event_slug="example",
        question="Will this happen?",
        outcomes=["Yes", "No"],
    )
    context = MarketContext(
        parsed_url=ParsedPolymarketURL(
            original_url="https://polymarket.com/event/example",
            normalized_url="https://polymarket.com/event/example",
            slug="example",
        ),
        forecast_contract=contract,
        market_snapshot=MarketSnapshot(
            target_probability=0.4,
            snapshot_time="2026-08-23T00:00:00+00:00",
        ),
    )

    async def failing_research(_contract):
        raise RuntimeError("research service unavailable")

    async def fake_experts(_contract, evidence, experts):
        assert evidence.evidence == []
        assert experts == ["domain"]
        return [
            ExpertForecast(
                expert="domain",
                probability=0.5,
                confidence=0.6,
                summary="Fallback forecast.",
            )
        ]

    monkeypatch.setattr(pipeline, "forecast_cache", ForecastCache(tmp_path / "cache.db", 60))
    pipeline.forecast_cache.initialize()
    monkeypatch.setattr(pipeline, "inspect_market", lambda *_args, **_kwargs: _async(context))
    monkeypatch.setattr(pipeline, "research_evidence", failing_research)
    monkeypatch.setattr(pipeline, "run_all_experts", fake_experts)

    response = asyncio.run(
        pipeline.run_forecast(
            "https://polymarket.com/event/example",
            selected_agents=["domain"],
            use_research=True,
        )
    )

    assert response.cache_hit is False
    assert response.evidence_packet.evidence == []
    assert any("Web research could not complete" in warning for warning in response.warnings)


async def _async(value):
    return value
