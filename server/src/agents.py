from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import TypeVar

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query
from pydantic import BaseModel

from src.schemas import AgentRole, EvidencePacket, ExpertForecast, ForecastContract
from src.skills import load_skill

T = TypeVar("T", bound=BaseModel)

AGENT_SKILLS: dict[AgentRole, str] = {
    "base_rate": "base-rate-forecasting",
    "domain": "domain-forecasting",
    "contrarian": "contrarian-review",
    "resolution": "resolution-review",
}
DEFAULT_AGENT_ROLES: tuple[AgentRole, ...] = tuple(AGENT_SKILLS)

async def _run_structured_agent(
    *,
    prompt: str,
    system_prompt: str,
    output_model: type[T],
    tools: list[str] | None = None,
    max_turns: int = 8,
) -> T:
    enabled_tools = tools or []

    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        tools=enabled_tools,
        allowed_tools=enabled_tools,
        max_turns=max_turns,
        output_format={
            "type": "json_schema",
            "schema": output_model.model_json_schema(),
        },
    )

    final_message: ResultMessage | None = None
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage):
            final_message = message

    if final_message is None:
        raise RuntimeError("Agent returned no ResultMessage")
    if final_message.subtype != "success":
        raise RuntimeError(
            f"Agent failed: subtype={final_message.subtype}, "
            f"errors={final_message.errors}"
        )
    if final_message.structured_output is None:
        raise RuntimeError("Agent returned no structured output")

    return output_model.model_validate(final_message.structured_output)


async def research_evidence(contract: ForecastContract) -> EvidencePacket:
    research_skill = load_skill("evidence-research")
    forecasting_skill = load_skill("superforecasting-method")

    system_prompt = f"""
You are the Evidence Research Agent for a prediction-market forecasting system.

Use web search and web fetch to find current, relevant, and source-grounded
information. Do not use or infer the current Polymarket market probability.
Return claims, not article summaries. Prefer official primary sources and
independent reporting. Separate support and opposition evidence. Deduplicate
reports that trace back to the same original source.

{research_skill}

{forecasting_skill}
"""

    prompt = f"""
Research the following forecast contract.

FORECAST CONTRACT:
{contract.model_dump_json(indent=2)}

Current UTC time:
{datetime.now(timezone.utc).isoformat()}

Tasks:
1. Interpret exactly what must happen for the target outcome to resolve.
2. Generate focused search queries for current status, official sources,
   supporting evidence, opposing evidence, historical base rates, and leading
   indicators.
3. Search and fetch the most relevant sources.
4. Return a compact evidence packet suitable for independent expert agents.
5. Include source URLs for every evidence item.
"""

    return await _run_structured_agent(
        prompt=prompt,
        system_prompt=system_prompt,
        output_model=EvidencePacket,
        tools=["WebSearch", "WebFetch"],
        max_turns=12,
    )


def _expert_system_prompt(expert: AgentRole) -> str:
    common = load_skill("superforecasting-method")
    evidence = load_skill("evidence-quality")

    role_skill = load_skill(AGENT_SKILLS[expert])
    
    return f"""
You are an independent {expert} forecasting agent.

You must not infer, request, or use the current Polymarket market probability.
You do not see other agents' forecasts. Start from an explicit base rate,
update using the supplied evidence, and return one calibrated probability.
Do not invent sources or facts that are absent from the evidence packet.

{common}

{evidence}

{role_skill}
"""


async def run_expert(
    expert: AgentRole,
    contract: ForecastContract,
    evidence: EvidencePacket,
) -> ExpertForecast:
    prompt = f"""
Produce an independent forecast for the target outcome.

FORECAST CONTRACT:
{contract.model_dump_json(indent=2)}

EVIDENCE PACKET:
{evidence.model_dump_json(indent=2)}

Your output field "expert" must be exactly "{expert}".
Explain the main upward and downward probability updates, assumptions,
resolution risks, and future update triggers.
"""

    result = await _run_structured_agent(
        prompt=prompt,
        system_prompt=_expert_system_prompt(expert),
        output_model=ExpertForecast,
        tools=[],
        max_turns=4,
    )

    if result.expert != expert:
        result.expert = expert
    return result

async def run_all_experts(
    contract: ForecastContract,
    evidence: EvidencePacket,
    experts: list[AgentRole] | None = None,
) -> list[ExpertForecast]:
    if experts is None:
        experts = list(DEFAULT_AGENT_ROLES)
    return list(
        await asyncio.gather(
            *(run_expert(expert, contract, evidence) for expert in experts)
        )
    )
