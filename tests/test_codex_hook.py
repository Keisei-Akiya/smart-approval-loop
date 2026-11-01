import json
import os
import subprocess
import sys


def test_codex_permission_request_is_normalized_and_logged(tmp_path):
    log = tmp_path / "events.jsonl"
    payload = {"session_id": "s1", "hook_event_name": "PermissionRequest", "tool_name": "Bash",
               "tool_input": {"command": "echo token=secretvalue"}, "cwd": "/repo", "permission_mode": "default"}
    env = {**os.environ, "SMART_APPROVAL_LOOP_LOG": str(log), "PYTHONPATH": "src"}
    result = subprocess.run([sys.executable, "-m", "smart_approval_loop.adapters.codex"], input=json.dumps(payload),
                            text=True, capture_output=True, env=env, check=False)
    assert result.returncode == 0
    assert result.stdout == ""
    event = json.loads(log.read_text())
    assert event["event"]["agent"] == "codex"
    assert event["event"]["event_type"] == "permission_request"
    assert event["event"]["tool_name"] == "Bash"
    assert event["event"]["tool_input"]["command"] == "echo token=[REDACTED]"


def test_codex_unknown_hook_is_ignored(tmp_path):
    log = tmp_path / "events.jsonl"
    env = {**os.environ, "SMART_APPROVAL_LOOP_LOG": str(log), "PYTHONPATH": "src"}
    subprocess.run([sys.executable, "-m", "smart_approval_loop.adapters.codex"], input='{"hook_event_name":"Stop"}',
                   text=True, capture_output=True, env=env, check=True)
    assert not log.exists()


def test_codex_without_judge_preserves_native_approval(tmp_path):
    log = tmp_path / "events.jsonl"
    payload = {"session_id": "s2", "hook_event_name": "PermissionRequest", "tool_name": "Bash",
               "tool_input": {"command": "rm -rf /"}, "cwd": "/repo"}
    env = {**os.environ, "SMART_APPROVAL_LOOP_LOG": str(log), "PYTHONPATH": "src"}
    result = subprocess.run([sys.executable, "-m", "smart_approval_loop.adapters.codex"], input=json.dumps(payload),
                            text=True, capture_output=True, env=env, check=False)
    assert result.returncode == 0
    assert result.stdout == ""
