# Codex `PermissionRequest` hook

Codex command hooks receive one JSON object on stdin. This adapter accepts `hook_event_name: "PermissionRequest"`, normalizes common fields, redacts secrets, records the event and judgment as JSONL, and writes an override only for `APPROVE` or `DENY`. `ESCALATE`, invalid input, and failures produce no stdout, leaving native approval in place. Codex specifies that a deny from any matching hook takes precedence over allows.

## Timeout verification

Verified against the [official Codex Hooks documentation](https://developers.openai.com/codex/hooks) on 2026-11-01: command hooks default to 600 seconds unless configured; `timeout` is in seconds, and matching command hooks run concurrently. The docs do not specify a special maximum for `PermissionRequest`. This adapter bounds judging to one second and emits no decision on timeout. Auxiliary LLM latency cannot be guaranteed within any configured timeout. If reliable inference under a strict deadline is required, move inference to a resident local service and have the hook make bounded local IPC; connection/response timeout must emit no decision. The resident service must retain redaction, logging, and conservative escalation.

## Install and trust

Install the package in the environment used by Codex and add to `~/.codex/hooks.json` or `.codex/hooks.json` (project config needs trust):

```json
{
  "hooks": {
    "PermissionRequest": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "uv run --project /path/to/smart-approval-loop python -m smart_approval_loop.adapters.codex",
            "timeout": 2,
            "statusMessage": "Checking approval request"
          }
        ]
      }
    ]
  }
}
```

Reload Codex and run `/hooks` to inspect, review, and explicitly trust this exact hook definition. Changed definitions require renewed review. Do not bypass hook trust as a normal installation step.

Tests exercise local fixtures only; no Codex process or real judge service is used.
