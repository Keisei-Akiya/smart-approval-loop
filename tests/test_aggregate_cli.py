import json
import subprocess
import sys


def test_cli_filters_and_lists_escalations_and_denials(tmp_path):
    log = tmp_path / "events.jsonl"
    rows = [
        {"event": {"agent": "codex", "occurred_at": "2026-01-02T12:00:00Z", "tool_name": "shell"}, "decision": "ESCALATE", "reason": "uncertain"},
        {"event": {"agent": "hermes", "occurred_at": "2026-01-02T12:30:00Z", "tool_name": "write"}, "decision": "DENY", "reason": "unsafe"},
        {"event": {"agent": "codex", "occurred_at": "2026-01-04T12:00:00Z", "tool_name": "shell"}, "decision": "APPROVE", "reason": "safe"},
    ]
    log.write_text("".join(json.dumps(row) + "\n" for row in rows))
    result = subprocess.run(
        [sys.executable, "-m", "smart_approval_loop.aggregate", str(log), "--agent", "codex", "--since", "2026-01-01", "--until", "2026-01-03"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["count"] == 1
    assert output["by_decision"] == {"ESCALATE": 1}
    assert output["by_agent"] == {"codex": 1}
    assert output["over_escalations"][0]["reason"] == "uncertain"
    assert output["denials"] == []
