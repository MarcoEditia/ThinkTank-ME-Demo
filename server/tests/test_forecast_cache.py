from datetime import datetime, timezone

from src.forecast_cache import ForecastCache, build_forecast_cache_key


def test_cache_key_ignores_agent_order_but_tracks_configuration():
    key = build_forecast_cache_key(
        market_id="market-1",
        selected_agents=["domain", "contrarian"],
        use_research=True,
        claude_model="sonnet",
        cache_version="v1",
    )

    assert key == build_forecast_cache_key(
        market_id="market-1",
        selected_agents=["contrarian", "domain"],
        use_research=True,
        claude_model="sonnet",
        cache_version="v1",
    )
    assert key != build_forecast_cache_key(
        market_id="market-1",
        selected_agents=["domain", "contrarian"],
        use_research=False,
        claude_model="sonnet",
        cache_version="v1",
    )


def test_cache_returns_stored_response(tmp_path):
    cache = ForecastCache(tmp_path / "forecast-cache.db", ttl_seconds=60)
    cache.initialize()
    cache.put("key", "market-1", '{"forecast": 0.42}')

    cached = cache.get("key")

    assert cached is not None
    assert cached.response_json == '{"forecast": 0.42}'
    assert datetime.fromisoformat(cached.created_at).tzinfo == timezone.utc


def test_cache_discards_expired_entry(tmp_path):
    cache = ForecastCache(tmp_path / "forecast-cache.db", ttl_seconds=-1)
    cache.initialize()
    cache.put("key", "market-1", "{}")

    assert cache.get("key") is None
