import os
import re
import json
import logging

import requests

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000")
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))
URL_REGEX = r"(https?://[^\s;,\s]+)"

# messagse_array has sessiond_id, content, files, url
def _extract_forecast_request(messages_array, url):
    '''
        extract the url and message query from the st.state.messages
        returns url and message_query both str
    '''
    latest_message = messages_array[-1]
    text = latest_message.get("content", "")
    market_url = url
    
    market_query = re.sub(re.escape(market_url), "", text, count=1).strip(" \t\n-:,;") or ""
    return market_url, market_query 

# In llm_client.py
def inspect_url(url: str, market_index: int = 0):
    """
    Inspects a Polymarket URL via the backend and returns parsed metadata + child markets.
    """
    try:
        response = requests.post(
            f"{BACKEND_API_URL}/inspect",
            json={"url": url, "market_index": market_index},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code == 200:
            data = response.json()
            return {
                "is_valid": True,
                "available_markets": data.get("available_markets", []),
                "contract": data.get("forecast_contract", {}),
                "error": None
            }
        else:
            error_msg = _extract_backend_error(response)
            return {"is_valid": False, "available_markets": [], "error": error_msg}
    except Exception as e:
        return {"is_valid": False, "available_markets": [], "error": str(e)}


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
        "\n### Contract",
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
    ]

    content_lines.append("### Expert Forecasts")
    for expert in expert_forecasts:
        summary = expert['summary'].replace("\n\n", "\n")
        content_lines.append(
            f"- **{expert['expert']}**: Probability: {expert['probability']:.1%} | {summary}"
        )

    evidence_items = evidence_packet.get("evidence", [])
    if evidence_items:
        content_lines.extend(["", "### Evidence"])
        for item in evidence_items[:8]:
            content_lines.append(
                f"- {item['source_title']}: {item['claim']} ({item['relation']})"
            )

    return {"content": "\n".join(content_lines), "reasoning": "\n".join(reasoning_lines)}


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


def query_model(messages_array, session_url):
    url, market_query = _extract_forecast_request(messages_array, session_url)

    if not url:
        return {
            "content": "Please paste a Polymarket URL so I can run a forecast.",
            "reasoning": "",
        }

    api_payload = {"url": url}
    api_payload["market_query"] = market_query
    try:
        inspect_response = requests.post(
            f"{BACKEND_API_URL}/inspect",
            json=api_payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if inspect_response.status_code >= 400:
            return {
                "content": f"{_extract_backend_error(inspect_response)}",
                "reasoning": ""
            }
    except Exception as e:
        return {"content": f"Backend API Error: {str(e)}", "reasoning": ""}

    try:
        response = requests.post(
            f"{BACKEND_API_URL}/forecast",
            json=api_payload,
        )
        response.raise_for_status()
        return _format_forecast_response(response.json())

    except Exception as e:
        return {"content": f"Backend API Error: {str(e)}", "reasoning": ""}