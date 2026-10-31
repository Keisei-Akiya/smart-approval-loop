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


def test_default_log_path_is_expanded_and_parent_created(tmp_path):
    payload = {"hook_event_name": "PermissionRequest", "session_id": "session-default"}
    home = tmp_path / "home"
    home.mkdir()
    result = subprocess.run(
        [sys.executable, "-m", "smart_approval_loop.adapters.claude_code"],
        input=json.dumps(payload), text=True, capture_output=True,
        env={**os.environ, "HOME": str(home)},
    )
    log = home / ".local/state/smart-approval-loop/events.jsonl"
    assert result.returncode == 0, result.stderr
    assert len(log.read_text().splitlines()) == 1


def test_non_permission_event_exits_success_without_recording(tmp_path):
    log = tmp_path / "events.jsonl"
    payload = {"hook_event_name": "SomeOtherEvent"}
    result = subprocess.run(
        [sys.executable, "-m", "smart_approval_loop.adapters.claude_code"],
        input=json.dumps(payload), text=True, capture_output=True,
        env={**os.environ, "SMART_APPROVAL_LOOP_LOG": str(log)},
    )
    assert result.returncode == 0
    assert not log.exists()


def test_exception_exits_without_blocking(tmp_path):
    log = tmp_path / "events.jsonl"
    result = subprocess.run(
        [sys.executable, "-m", "smart_approval_loop.adapters.claude_code"],
        input="not-json", text=True, capture_output=True,
        env={**os.environ, "SMART_APPROVAL_LOOP_LOG": str(log)},
    )
    assert result.returncode not in (1, 2)
    assert result.returncode == 0
