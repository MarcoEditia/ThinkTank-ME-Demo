import os
import re

import requests

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000")
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))
URL_REGEX = r"(https?://[^\s;,\s]+)"


def _extract_forecast_request(messages_array):
    if not messages_array:
        return None, None

    text = messages_array[-1].get("content", "")
    urls = re.findall(URL_REGEX, text)
    if not urls:
        return None, None

    url = urls[0]
    market_query = re.sub(re.escape(url), "", text, count=1).strip(" \t\n-:,;")
    return url, market_query or None


def _format_forecast_response(data):
    forecast_contract = data["forecast_contract"]
    market_snapshot = data["market_snapshot"]
    aggregate = data["aggregate"]
    expert_forecasts = data.get("expert_forecasts", [])
    evidence_packet = data.get("evidence_packet", {})
    warnings = data.get("warnings", [])

    content_lines = [
        f"### Forecast: {forecast_contract['question']}",
        f"- Median probability: **{aggregate['probability']:.1%}**",
    ]

    market_probability = aggregate.get("market_probability")
    if market_probability is not None:
        content_lines.append(f"- Market probability: **{market_probability:.1%}**")

    probability_gap = aggregate.get("probability_gap")
    if probability_gap is not None:
        content_lines.append(f"- Gap vs market: **{probability_gap:+.1%}**")

    content_lines.extend(
        [
            f"- Agreement: **{aggregate['agreement']}**",
            f"- Dispersion: **{aggregate['dispersion']:.3f}**",
        ]
    )

    if warnings:
        content_lines.append("\n**Warnings**")
        content_lines.extend(f"- {warning}" for warning in warnings)

    reasoning_lines = [
        "### Contract",
        f"- Event: {forecast_contract['event_slug']}",
        f"- Market: {forecast_contract['market_id']}",
        f"- Resolution: {forecast_contract['resolution_criteria']}",
        "",
        "### Market Snapshot",
        f"- Target probability: {market_snapshot.get('target_probability')}",
        f"- Last trade price: {market_snapshot.get('last_trade_price')}",
        f"- Volume: {market_snapshot.get('volume')}",
        f"- Liquidity: {market_snapshot.get('liquidity')}",
        "",
        "### Expert Forecasts",
    ]

    for expert in expert_forecasts:
        reasoning_lines.append(
            f"- **{expert['expert']}**: {expert['probability']:.1%} | {expert['summary']}"
        )

    evidence_items = evidence_packet.get("evidence", [])
    if evidence_items:
        reasoning_lines.extend(["", "### Evidence"])
        for item in evidence_items[:8]:
            reasoning_lines.append(
                f"- {item['source_title']}: {item['claim']} ({item['relation']})"
            )

    return {"content": "\n".join(content_lines) + "\n".join(reasoning_lines), "reasoning": "\n".join(reasoning_lines)}


def _extract_backend_error(response):
    try:
        payload = response.json()
        detail = payload.get("detail")
        if detail:
            return str(detail)
    except Exception:
        pass

    text = response.text.strip()
    return text or f"HTTP {response.status_code}"


def query_model(messages_array):
    url, market_query = _extract_forecast_request(messages_array)

    if not url:
        return {
            "content": "Please paste a Polymarket URL so I can run a forecast.",
            "reasoning": "",
        }

    api_payload = {"url": url}
    if market_query:
        api_payload["market_query"] = market_query

    try:
        inspect_response = requests.post(
            f"{BACKEND_API_URL}/inspect",
            json=api_payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if inspect_response.status_code >= 400:
            return {
                "content": f"Backend URL error: {_extract_backend_error(inspect_response)}",
                "reasoning": "",
            }

        response = requests.post(
            f"{BACKEND_API_URL}/forecast",
            json=api_payload,
        )
        response.raise_for_status()
        return _format_forecast_response(response.json())

    except Exception as e:
        return {"content": f"Backend API Error: {str(e)}", "reasoning": ""}