import asyncio

import pytest
from pydantic import ValidationError

from src.agents import AGENT_SKILLS, DEFAULT_AGENT_ROLES
from src import main
from src.schemas import ForecastRequest


def test_default_agent_roles_have_skills():
    assert tuple(AGENT_SKILLS) == DEFAULT_AGENT_ROLES


def test_forecast_request_accepts_selected_agents():
    request = ForecastRequest(
        url="https://polymarket.com/event/example",
        selected_agents=["domain", "contrarian"],
        use_research=False,
    )

    assert request.selected_agents == ["domain", "contrarian"]
    assert request.use_research is False


def test_forecast_request_rejects_unknown_agent():
    with pytest.raises(ValidationError):
        ForecastRequest(
            url="https://polymarket.com/event/example",
            selected_agents=["unknown"],
        )


def test_forecast_endpoint_forwards_agent_selection(monkeypatch):
    captured = {}

    async def fake_run_forecast(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return "forecast"

    monkeypatch.setattr(main, "run_forecast", fake_run_forecast)
    request = ForecastRequest(
        url="https://polymarket.com/event/example",
        selected_agents=["domain", "contrarian"],
        use_research=False,
    )

    assert asyncio.run(main.forecast_endpoint(request)) == "forecast"
    assert captured == {
        "url": "https://polymarket.com/event/example",
        "market_query": None,
        "market_index": None,
        "selected_agents": ["domain", "contrarian"],
        "use_research": False,
    }
