from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

AgentRole = Literal["base_rate", "domain", "contrarian", "resolution"]


class ParsedPolymarketURL(BaseModel):
    original_url: str
    normalized_url: str
    slug: str


class ForecastContract(BaseModel):
    event_id: str
    market_id: str
    event_slug: str
    market_slug: str | None = None
    question: str
    description: str = ""
    target_outcome: str = "Yes"
    outcomes: list[str]
    deadline: str | None = None
    resolution_source: str | None = None
    resolution_criteria: str = ""
    category: str | None = None
    tags: list[str] = Field(default_factory=list)


class MarketSnapshot(BaseModel):
    outcome_probabilities: dict[str, float] = Field(default_factory=dict)
    target_probability: float | None = None
    volume: float | None = None
    liquidity: float | None = None
    best_bid: float | None = None
    best_ask: float | None = None
    spread: float | None = None
    last_trade_price: float | None = None
    active: bool | None = None
    closed: bool | None = None
    snapshot_time: str


class MarketContext(BaseModel):
    parsed_url: ParsedPolymarketURL
    forecast_contract: ForecastContract
    market_snapshot: MarketSnapshot
    available_markets: list[dict] = Field(default_factory=list)
    raw_event: dict | None = None


class EvidenceItem(BaseModel):
    claim: str
    relation: Literal["support", "oppose", "neutral", "uncertain"]
    source_title: str
    source_url: str
    source_type: Literal[
        "official", "major_news", "academic", "expert_analysis", "other"
    ]
    published_at: str | None = None
    relevance: float = Field(ge=0.0, le=1.0)
    reliability: float = Field(ge=0.0, le=1.0)
    freshness: float = Field(ge=0.0, le=1.0)
    reasoning: str


class EvidencePacket(BaseModel):
    retrieval_queries: list[str] = Field(default_factory=list)
    base_rate_summary: str = ""
    evidence: list[EvidenceItem] = Field(default_factory=list)
    key_unknowns: list[str] = Field(default_factory=list)
    evidence_cutoff_time: str


class ExpertForecast(BaseModel):
    expert: AgentRole
    probability: float = Field(ge=0.01, le=0.99)
    confidence: float = Field(ge=0.0, le=1.0)
    base_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    summary: str
    supporting_claims: list[str] = Field(default_factory=list)
    opposing_claims: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    update_triggers: list[str] = Field(default_factory=list)
    resolution_risks: list[str] = Field(default_factory=list)


class AggregatedForecast(BaseModel):
    method: Literal["median"] = "median"
    probability: float = Field(ge=0.01, le=0.99)
    expert_probabilities: dict[str, float]
    dispersion: float = Field(ge=0.0)
    agreement: Literal["high", "medium", "low"]
    market_probability: float | None = None
    probability_gap: float | None = None


class ForecastResponse(BaseModel):
    forecast_contract: ForecastContract
    market_snapshot: MarketSnapshot
    evidence_packet: EvidencePacket
    expert_forecasts: list[ExpertForecast]
    aggregate: AggregatedForecast
    warnings: list[str] = Field(default_factory=list)


class ForecastRequest(BaseModel):
    url: str
    # Prefer market_query for multi-market events such as World Cup Winner.
    # market_index remains available as a fallback/debugging option.
    market_query: str | None = None
    market_index: int | None = Field(default=None, ge=0)
    selected_agents: list[AgentRole] | None = Field(default=None, min_length=1)
    use_research: bool = True
