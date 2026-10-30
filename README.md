# smart-approval-loop

承認要求を補助LLMで判定し、秘密を伏せたイベントを JSONL に記録・集計して、ポリシー改善につなげる OSS プラグインです。判定を自動適用する範囲などの詳細仕様は、親仕様 https://github.com/Keisei-Akiya/wiki/issues/4 を参照してください。

## 構成

- `src/smart_approval_loop/core/` — 共通イベント、秘密のマスキング、判定・記録・集計などのコア
- `src/smart_approval_loop/adapters/` — 各エージェントとの入出力を変換する薄いアダプタ
  - `claude_code/` — Claude Code
  - `codex/` — Codex
  - `hermes/` — Hermes
- `tests/` — テスト
- `docs/` — 方針・設計文書

## 対応環境

Claude Code、Codex、Hermes の承認要求フックを対象とします。各環境の具体的な連携方法は今後の実装で追加します。

## 開発

Python 3.11 以上と [uv](https://docs.astral.sh/uv/) を使用します。

```sh
uv sync
uv run pytest
```

## ライセンス

ライセンス候補と決定時期は [`docs/license-policy.md`](docs/license-policy.md) を参照してください。現時点では LICENSE ファイルを置いていません。

## 公開前

README の英語併記は公開前に追加します。
