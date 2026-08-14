from __future__ import annotations

from statistics import median, pstdev

from src.schemas import AggregatedForecast, ExpertForecast


def aggregate_forecasts(
    forecasts: list[ExpertForecast],
    market_probability: float | None,
) -> AggregatedForecast:
    if not forecasts:
        raise ValueError("At least one expert forecast is required")

    values = [forecast.probability for forecast in forecasts]
    probability = float(median(values))
    dispersion = float(pstdev(values)) if len(values) > 1 else 0.0

    if dispersion <= 0.07:
        agreement = "high"
    elif dispersion <= 0.15:
        agreement = "medium"
    else:
        agreement = "low"

    gap = (
        probability - market_probability
        if market_probability is not None
        else None
    )

    return AggregatedForecast(
        probability=probability,
        expert_probabilities={
            forecast.expert: forecast.probability for forecast in forecasts
        },
        dispersion=dispersion,
        agreement=agreement,
        market_probability=market_probability,
        probability_gap=gap,
    )
