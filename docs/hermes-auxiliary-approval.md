# Hermes auxiliary.approval 変換サーバー

このアダプターはローカルの OpenAI 互換 `/chat/completions` エンドポイントとして動き、Hermes の `auxiliary.approval` からの判定要求を共通イベント形式に変換します。判定には `core.judges.ChatCompletionsJudge` を使います。モデルの応答が `APPROVE` / `DENY` / `ESCALATE` のいずれでもない、空、無効な形式、例外、タイムアウトの場合は Hermes が通常の承認へ戻れるよう `ESCALATE` を返します。

## 起動

外部判定器 (OpenAI 互換チャット completions API) を明示して起動します。リクエストの送信先 URL は必ず `/chat/completions` を含む完全な URL にしてください。サーバーは既定で loopback のみに bind します。

```sh
export SMART_APPROVAL_LOOP_JUDGE_URL='https://your-approved-provider.example/v1/chat/completions'
export SMART_APPROVAL_LOOP_JUDGE_MODEL='your-model'
# API キーが必要な場合のみ、環境変数で与える。実キーを設定ファイルやログへ記録しない。
export SMART_APPROVAL_LOOP_JUDGE_API_KEY='...'
uv run --project /path/to/smart-approval-loop python -m smart_approval_loop.adapters.hermes.server
```

`SMART_APPROVAL_LOOP_HOST` (既定 `127.0.0.1`)、`SMART_APPROVAL_LOOP_PORT` (既定 `8765`)、`SMART_APPROVAL_LOOP_TIMEOUT` 秒 (既定 `5`) で待受と時間制限を調整できます。`SMART_APPROVAL_LOOP_JUDGE_URL` が未設定なら起動を拒否します。送信先は明示した判定器のみで、自動切替・再試行はしません。Hermes から届く system prompt と user prompt は共通イベント内に保持され、既存の秘密伏せ字を通してから判定器へ渡されます。

## Hermes 側の登録

Hermes の設定に既存の `auxiliary.approval` タスク設定を置き、provider/base URL をローカル OpenAI 互換サーバーへ向けます。環境の設定形式は Hermes バージョンによって異なるため、既存の auxiliary task 定義を残したまま `base_url` を `http://127.0.0.1:8765/v1` (Hermes が `/chat/completions` を補う形式の場合) または `http://127.0.0.1:8765` (完全な endpoint を要求する形式の場合) に指定します。model は任意のローカル識別子にできます。実際の Hermes の設定ソースで対象バージョンの `base_url` 仕様を確認してから登録してください。既存の primary LLM 設定は変更しません。

Hermes の `approvals.smart_policy` と標準の system prompt は `auxiliary.approval` 要求内で転送されます。運用ポリシーを変更した後は、テスト承認要求を使い判定器に反映されたことを確認してください。サーバーは Hermes 自体の設定ファイルを変更しません。

## 移行とロールバック

1. Hermes の現在の `approvals.mode: smart`、補助 LLM 設定、タイムアウト、`smart_policy` を控え、設定のバックアップを取ります。
2. 上記の変換サーバーをローカル起動し、`auxiliary.approval` のみをローカル endpoint に向けます。primary model や他タスクは変更しません。
3. 秘密でないテスト要求で `APPROVE`、`DENY`、`ESCALATE` の各応答を確認します。失敗・タイムアウト時は通常承認に戻ることを確認します。本番利用前に運用者がポリシーと送信先を審査してください。
4. 問題があれば変更した `auxiliary.approval` の endpoint/provider を元の値 (例: luna) に戻し、元の smart mode と補助 LLM 設定を復元します。サーバーを停止します。primary LLM の値や他設定を一括置換しないでください。

このリポジトリの自動テストは HTTP 入出力をローカルで検証し、実キー・実ネットワークを使用しません。Hermes 実プロセスとの統合実行は、ユーザーの Hermes 設定を変更せず、実プロバイダーに接続せずに行うことはできないため未実施です。
