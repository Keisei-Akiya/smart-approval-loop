"""共通イベントの正規化、秘密の伏せ字、JSONL 記録。"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SECRET_PATTERNS = [
    re.compile(r"(?i)(\b(?:api[_-]?key|token|password|passwd|secret)\b\s*[=:]\s*)([^\s&'\"]+)"),
    re.compile(r"\b(sk-[A-Za-z0-9_-]{8,})\b"),
    re.compile(r"(?i)(Bearer\s+)[A-Za-z0-9._~+/-]+=*"),
]

def redact(value: Any) -> Any:
    if isinstance(value, str):
        for pattern in _SECRET_PATTERNS:
            value = pattern.sub(lambda m: (m.group(1) if m.lastindex and m.lastindex > 1 else "") + "[REDACTED]", value)
        return value
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, dict):
        return {str(key): redact(item) for key, item in value.items()}
    return value

def record_event(event: dict[str, Any], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(redact(event), ensure_ascii=False, separators=(",", ":"))
    with target.open("a", encoding="utf-8") as stream:
        stream.write(line + "\n")

def common_event(agent: str, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {"schema_version": 1, "event_id": payload.get("session_id", "unknown"),
            "occurred_at": datetime.now(timezone.utc).isoformat(), "agent": agent,
            "event_type": event_type, "tool_name": payload.get("tool_name"),
            "tool_input": payload.get("tool_input", {}), "permission_mode": payload.get("permission_mode"),
            "cwd": payload.get("cwd")}
