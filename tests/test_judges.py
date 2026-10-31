import asyncio

import pytest

from smart_approval_loop.core.judges import (
    Decision,
    Judgment,
    JevJudge,
    judge_and_record,
    judge_safely,
)


class FakeJudge:
    def __init__(self, result=None, error=None, delay=0):
        self.result = result
        self.error = error
        self.delay = delay
        self.event = None

    async def judge(self, event):
        self.event = event
        await asyncio.sleep(self.delay)
        if self.error:
            raise self.error
        return self.result


@pytest.mark.parametrize("failure", [RuntimeError("offline"), ValueError("invalid")])
def test_judge_failure_or_invalid_result_escalates(failure):
    result = asyncio.run(judge_safely(FakeJudge(result=failure), {}, timeout=1))
    assert result.decision is Decision.ESCALATE


def test_judge_timeout_escalates():
    result = asyncio.run(judge_safely(FakeJudge(result=Decision.APPROVE, delay=0.05), {}, timeout=0.001))
    assert result.decision is Decision.ESCALATE


def test_uncertain_jev_probability_escalates():
    result = JevJudge(fake_transport, threshold=0.8)
    judgment = asyncio.run(judge_safely(result, {}))
    assert judgment.decision is Decision.ESCALATE


async def fake_transport(question):
    return {"allow": 0.6, "deny": 0.4}


def test_jev_high_confidence_maps_only_allow_or_deny():
    judge = JevJudge(fake_transport, threshold=0.8)
    async def response(question):
        return {"allow": 0.95, "deny": 0.05}
    judge.transport = response
    assert asyncio.run(judge_safely(judge, {})).decision is Decision.APPROVE


def test_jev_receives_redacted_event():
    captured = {}
    async def transport(question):
        captured["question"] = question
        return {"allow": 0.9, "deny": 0.1}
    judgment = asyncio.run(judge_safely(JevJudge(transport), {"command": "run token=do-not-leak"}))
    assert "do-not-leak" not in captured["question"]
    assert "[REDACTED]" in captured["question"]
    assert judgment.decision is Decision.APPROVE


def test_judge_reason_is_recorded_with_redacted_event(tmp_path):
    import json
    path = tmp_path / "decisions.jsonl"
    judgment = asyncio.run(judge_and_record(
        FakeJudge(result=Judgment(Decision.DENY, "policy rejected")),
        {"command": "token=private-value"}, str(path),
    ))
    line = path.read_text()
    entry = json.loads(line)
    assert judgment.decision is Decision.DENY
    assert entry["reason"] == "policy rejected"
    assert entry["decision"] == "DENY"
    assert "private-value" not in line


def test_jev_bad_probability_format_escalates():
    async def transport(question):
        return {"approve": 0.99}
    result = asyncio.run(judge_safely(JevJudge(transport), {}))
    assert result.decision is Decision.ESCALATE


def test_generic_chat_bad_reply_escalates_without_exposing_secrets():
    from smart_approval_loop.core.judges import ChatCompletionsJudge
    captured = {}
    async def transport(messages):
        captured["content"] = messages[-1]["content"]
        return {"choices": [{"message": {"content": "maybe"}}]}
    judgment = asyncio.run(judge_safely(ChatCompletionsJudge(transport), {"command": "token=private-value"}))
    assert judgment.decision is Decision.ESCALATE
    assert "private-value" not in captured["content"]
