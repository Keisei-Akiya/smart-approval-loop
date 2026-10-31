# 共通イベントスキーマ（v1）

1 行 1 JSON オブジェクトの UTF-8 JSONL。`schema_version` は整数 `1`、`event_id` は入力の session ID、`occurred_at` は UTC ISO 8601、`agent` は `claude_code` / `codex` / `hermes`、`event_type` は `permission_request`。`tool_name`、`tool_input`、`permission_mode`、`cwd` は入力から正規化した情報。記録前に文字列中の API キー、トークン、パスワード、Bearer 認証値を `[REDACTED]` に置換する。

秘密を含む値の伏せ字処理に失敗した場合、イベントを記録しない。フックは JSON を標準入力から読み、`SMART_APPROVAL_LOOP_LOG` で指定した JSONL に追記する（未指定時 `~/.local/state/smart-approval-loop/events.jsonl`）。
