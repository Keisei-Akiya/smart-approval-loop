import json
import os
import subprocess
import sys


def test_permission_request_is_masked_and_appended_as_common_jsonl(tmp_path):
    log = tmp_path / "events.jsonl"
    payload = {
        "session_id": "session-example",
        "transcript_path": "/tmp/transcript-example",
        "cwd": "/repo/example",
        "hook_event_name": "PermissionRequest",
        "tool_name": "Bash",
        "tool_input": {"command": "curl https://example.test?token=dummy-token-value"},
        "permission_mode": "default",
    }
    result = subprocess.run(
        [sys.executable, "-m", "smart_approval_loop.adapters.claude_code"],
        input=json.dumps(payload), text=True, capture_output=True,
        env={**os.environ, "SMART_APPROVAL_LOOP_LOG": str(log)},
    )
    assert result.returncode == 0, result.stderr
    lines = log.read_text().splitlines()
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["agent"] == "claude_code"
    assert event["event_type"] == "permission_request"
    assert event["tool_name"] == "Bash"
    assert "dummy-token-value" not in lines[0]
    assert "[REDACTED]" in lines[0]
