"""Codex PermissionRequest command-hook entry point."""

import asyncio
import json
import os
import sys

from smart_approval_loop.core import common_event
from smart_approval_loop.core.judges import Decision, Judgment, judge_and_record


class _EscalateJudge:
    """No production judge is configured yet; preserve native approval."""

    async def judge(self, event):
        return Judgment(Decision.ESCALATE, "no judge configured")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if payload.get("hook_event_name") != "PermissionRequest":
            return 0
        event = common_event("codex", "permission_request", payload)
        path = os.path.expanduser(os.environ.get("SMART_APPROVAL_LOOP_LOG", "~/.local/state/smart-approval-loop/events.jsonl"))
        judgment = asyncio.run(judge_and_record(_EscalateJudge(), event, path, timeout=1.0))
        if judgment.decision is Decision.ESCALATE:
            return 0
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PermissionRequest",
            "decision": "override",
            "permissionDecision": "allow" if judgment.decision is Decision.APPROVE else "deny",
        }}, separators=(",", ":")))
        return 0
    except Exception:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
