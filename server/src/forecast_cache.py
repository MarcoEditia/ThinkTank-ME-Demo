from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3


@dataclass(frozen=True)
class CachedForecast:
    response_json: str
    created_at: str


def build_forecast_cache_key(
    market_id: str,
    selected_agents: list[str],
    use_research: bool,
    claude_model: str,
    cache_version: str,
) -> str:
    """Build a stable cache key for inputs that affect forecast output."""
    payload = {
        "cache_version": cache_version,
        "claude_model": claude_model,
        "market_id": market_id,
        "selected_agents": sorted(selected_agents),
        "use_research": use_research,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


class ForecastCache:
    def __init__(self, db_path: str | Path, ttl_seconds: int) -> None:
        self.db_path = Path(db_path)
        self.ttl_seconds = ttl_seconds

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS forecast_cache (
                    cache_key TEXT PRIMARY KEY,
                    market_id TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
                """
            )

    def get(self, cache_key: str) -> CachedForecast | None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM forecast_cache WHERE expires_at <= ?", (now,)
            )
            row = connection.execute(
                """
                SELECT response_json, created_at
                FROM forecast_cache
                WHERE cache_key = ?
                """,
                (cache_key,),
            ).fetchone()

        if row is None:
            return None
        return CachedForecast(response_json=row[0], created_at=row[1])

    def put(self, cache_key: str, market_id: str, response_json: str) -> None:
        created_at = datetime.now(timezone.utc)
        expires_at = created_at + timedelta(seconds=self.ttl_seconds)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO forecast_cache (
                    cache_key, market_id, response_json, created_at, expires_at
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    market_id = excluded.market_id,
                    response_json = excluded.response_json,
                    created_at = excluded.created_at,
                    expires_at = excluded.expires_at
                """,
                (
                    cache_key,
                    market_id,
                    response_json,
                    created_at.isoformat(),
                    expires_at.isoformat(),
                ),
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)
