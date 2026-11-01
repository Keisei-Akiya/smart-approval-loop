"""Summarize JSONL approval logs."""

import argparse
import json
from collections import Counter
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def summarize(path: str | Path, agent: str | None = None,
              since: date | None = None, until: date | None = None) -> dict[str, Any]:
    rows = []
    with Path(path).open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                event = row.get("event", row)
                timestamp = _timestamp(event["occurred_at"])
                decision = row["decision"]
                event_agent = event["agent"]
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
                raise ValueError(f"invalid event on line {line_number}: {error}") from error
            if agent and event_agent != agent:
                continue
            if since and timestamp.date() < since:
                continue
            if until and timestamp.date() > until:
                continue
            rows.append({"agent": event_agent, "decision": decision,
                         "occurred_at": event["occurred_at"], "tool_name": event.get("tool_name"),
                         "reason": row.get("reason", "")})
    decisions = Counter(row["decision"] for row in rows)
    agents = Counter(row["agent"] for row in rows)
    return {"count": len(rows), "by_decision": dict(sorted(decisions.items())),
            "by_agent": dict(sorted(agents.items())),
            "over_escalations": [r for r in rows if r["decision"] == "ESCALATE"],
            "denials": [r for r in rows if r["decision"] == "DENY"]}


def main() -> None:
    parser = argparse.ArgumentParser(description="JSONL 承認ログを集計します")
    parser.add_argument("log", help="JSONL ログファイル")
    parser.add_argument("--agent", help="エージェント名で絞り込み")
    parser.add_argument("--since", type=date.fromisoformat, help="開始日 (YYYY-MM-DD、含む)")
    parser.add_argument("--until", type=date.fromisoformat, help="終了日 (YYYY-MM-DD、含む)")
    args = parser.parse_args()
    if args.since and args.until and args.since > args.until:
        parser.error("--since は --until 以下にしてください")
    print(json.dumps(summarize(args.log, args.agent, args.since, args.until), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
