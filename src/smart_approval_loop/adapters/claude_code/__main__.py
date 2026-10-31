"""Claude Code の PermissionRequest フック入口。"""

import json
import os
import sys

from smart_approval_loop.core import common_event, record_event


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if payload.get("hook_event_name") != "PermissionRequest":
            return 0
        event = common_event("claude_code", "permission_request", payload)
        path = os.path.expanduser(os.environ.get("SMART_APPROVAL_LOOP_LOG", "~/.local/state/smart-approval-loop/events.jsonl"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        record_event(event, path)
        return 0
    except Exception:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
