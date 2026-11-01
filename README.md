# smart-approval-loop

承認要求を補助LLMで判定し、秘密を伏せたイベントを JSONL に記録・集計して、ポリシー改善につなげる OSS プラグインです。判定を自動適用する範囲などの詳細仕様は、仕様 https://github.com/Keisei-Akiya/smart-approval-loop/issues/11 を参照してください（由来: https://github.com/Keisei-Akiya/wiki/issues/4）。

## 構成

- `src/smart_approval_loop/core/` — 共通イベント、秘密のマスキング、判定・記録・集計などのコア
- `src/smart_approval_loop/adapters/` — 各エージェントとの入出力を変換する薄いアダプタ
  - `claude_code/` — Claude Code
  - `codex/` — Codex
  - `hermes/` — Hermes
- `tests/` — テスト
- `docs/` — 方針・設計文書

## 対応環境

Claude Code、Codex、Hermes の承認要求フックを対象とします。Claude Code の `PermissionRequest` は以下の設定例で記録できます（`uv` とリポジトリの配置先を環境に合わせてください）。ログ形式は [`docs/event-schema.md`](docs/event-schema.md) を参照してください。

```json
{
  "hooks": {
    "PermissionRequest": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "uv run --directory /path/to/smart-approval-loop python -m smart_approval_loop.adapters.claude_code",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

ログ保存先は `SMART_APPROVAL_LOOP_LOG` 環境変数で変更できます。集計 CLI は `uv run python -m smart_approval_loop.aggregate <ログ>` で実行します。`--agent codex`、`--since YYYY-MM-DD`、`--until YYYY-MM-DD` で絞り込めます。全件数・判定別・エージェント別の件数と、`ESCALATE` (過剰エスカレーション候補)・`DENY` (拒否) の一覧を JSON で出力します。Codex の `PermissionRequest` hooks.json 例、タイムアウト検証、`/hooks` による信頼手順は [`docs/codex-hook.md`](docs/codex-hook.md) を参照してください。Codex アダプタは現時点で判定器未接続のため、記録後に通常の承認へ戻ります。

## 開発

Python 3.11 以上と [uv](https://docs.astral.sh/uv/) を使用します。

```sh
uv sync
uv run pytest
```

## 判定器

`smart_approval_loop.core.judges` は `Judge` プロトコルと `APPROVE` / `DENY` / `ESCALATE` の結果型を提供します。実装は `ChatCompletionsJudge` または `JevJudge` を注入して切り替えます。通信 transport は呼び出し側で与えるため、接続先と認証情報を明示でき、コアは実ネットワークやキーに依存しません。Jev は確率しきい値(既定 0.8)を下回るとエスカレートします。

`judge_safely` は例外、タイムアウト、不正な応答を `ESCALATE` に変換し、`judge_and_record` は伏せ字済みイベント・判定・理由を JSONL に追記します。外部送信を行うアダプタも伏せ字後の内容だけを渡します。自動でポリシーを変更しません。

## ライセンス

ライセンス候補と決定時期は [`docs/license-policy.md`](docs/license-policy.md) を参照してください。現時点では LICENSE ファイルを置いていません。

## 公開前

README の英語併記は公開前に追加します。
