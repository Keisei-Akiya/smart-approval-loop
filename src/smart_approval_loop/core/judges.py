"""Pluggable approval judges; all failures conservatively escalate."""

import asyncio
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable, Protocol

from . import record_event, redact


class Decision(str, Enum):
    APPROVE = "APPROVE"
    DENY = "DENY"
    ESCALATE = "ESCALATE"


@dataclass(frozen=True)
class Judgment:
    decision: Decision
    reason: str


class Judge(Protocol):
    async def judge(self, event: dict[str, Any]) -> Judgment: ...


Transport = Callable[..., Awaitable[Any]]


class ChatCompletionsJudge:
    """Adapter for an injected OpenAI-compatible chat-completions transport."""

    def __init__(self, transport: Transport):
        self.transport = transport

    async def judge(self, event: dict[str, Any]) -> Judgment:
        message = json.dumps(redact(event), ensure_ascii=False, separators=(",", ":"))
        response = await self.transport([{"role": "user", "content": message}])
        content = response["choices"][0]["message"]["content"].strip()
        decision = Decision(content)
        if decision is Decision.ESCALATE:
            return Judgment(decision, "judge requested escalation")
        return Judgment(decision, "chat-completions judge")


class JevJudge:
    """Adapter for a Jev probability transport; endpoint selection is explicit."""

    def __init__(self, transport: Transport, threshold: float = 0.8):
        if not 0 < threshold <= 1:
            raise ValueError("threshold must be in (0, 1]")
        self.transport = transport
        self.threshold = threshold

    async def judge(self, event: dict[str, Any]) -> Judgment:
        question = "Classify this approval request as allow or deny: " + json.dumps(
            redact(event), ensure_ascii=False, separators=(",", ":")
        )
        probabilities = await self.transport(question)
        if not isinstance(probabilities, dict) or set(probabilities) != {"allow", "deny"}:
            raise ValueError("unexpected Jev probability response")
        allow, deny = probabilities["allow"], probabilities["deny"]
        if (not isinstance(allow, (int, float)) or isinstance(allow, bool)
                or not isinstance(deny, (int, float)) or isinstance(deny, bool)
                or not 0 <= allow <= 1 or not 0 <= deny <= 1):
            raise ValueError("invalid Jev probabilities")
        if allow + deny > 1.000001:
            raise ValueError("Jev probabilities exceed one")
        confidence = max(allow, deny)
        if confidence < self.threshold:
            return Judgment(Decision.ESCALATE, "Jev confidence below threshold")
        return Judgment(Decision.APPROVE if allow > deny else Decision.DENY, "Jev probability classification")


async def judge_safely(judge: Judge, event: dict[str, Any], timeout: float = 5.0) -> Judgment:
    """Return a valid judge result or escalate on error, timeout, or bad output."""
    try:
        result = await asyncio.wait_for(judge.judge(redact(event)), timeout=timeout)
        if (not isinstance(result, Judgment) or not isinstance(result.decision, Decision)
                or not isinstance(result.reason, str)):
            raise ValueError("invalid judge response")
        return result
    except Exception:
        return Judgment(Decision.ESCALATE, "judge failure, timeout, or invalid response")


async def judge_and_record(
    judge: Judge, event: dict[str, Any], path: str, timeout: float = 5.0
) -> Judgment:
    """Judge safely and append the redacted event, decision, and reason as JSONL."""
    judgment = await judge_safely(judge, event, timeout)
    record_event(
        {"event": event, "decision": judgment.decision.value, "reason": judgment.reason},
        path,
    )
    return judgment
