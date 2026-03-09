# mail-transfer

Gmail の受信メールを Notion データベースへ自動転送するツールです。
GitHub Actions により毎週火曜 2:00 JST にスケジュール実行されます。

## 概要

指定した送信元アドレス (`FROM_EMAIL`) から届いたメールを IMAP で取得し、件名・本文を Notion のデータベースページとして登録します。
同じ件名のページがすでに存在する場合はスキップするため、重複登録されません。

```
Gmail (IMAP) ──► MailTransferService ──► Notion API
```

## 技術スタック

| 用途 | ライブラリ / ツール |
|---|---|
| パッケージ管理 | [uv](https://docs.astral.sh/uv/) |
| 環境変数の暗号化 | [dotenvx](https://dotenvx.com/) |
| HTTP クライアント | httpx |
| DI コンテナ | injector |
| バリデーション | pydantic / pydantic-settings |
| Lint / Format | ruff, mypy |

## ディレクトリ構成

```
src/
├── domain/
│   ├── interfaces.py          # MailFetcher / MailExporter プロトコル
│   └── models/mail.py         # Mail データモデル
├── infrastructure/
│   ├── gmail/                 # IMAP でメールを取得
│   └── notion/                # Notion API へページを作成
├── usecase/
│   └── mail_transfer_service.py  # フェッチ → エクスポートのオーケストレーション
├── main.py
├── settings.py
└── logger.py
```

## セットアップ

### 必要なもの

- Python 3.10.13+
- [uv](https://docs.astral.sh/uv/)
- [dotenvx](https://dotenvx.com/)
- Gmail アカウント（IMAP 有効 + アプリパスワード発行済み）
- Notion インテグレーション（API キー + データベース ID）

### インストール

```bash
uv sync
```

### 環境変数の設定

`.env` の値は dotenvx で暗号化されています。`make set` で追加・更新できます。

```bash
make set KEY=GMAIL_USERNAME VALUE=your@gmail.com
make set KEY=GMAIL_APP_PASSWORD VALUE=xxxx-xxxx-xxxx-xxxx
make set KEY=NOTION_API_KEY VALUE=secret_...
make set KEY=NOTION_DATA_SOURCE_ID VALUE=<database-id>
make set KEY=FROM_EMAIL VALUE=sender@example.com
```

| 変数名 | 説明 |
|---|---|
| `GMAIL_USERNAME` | Gmail アドレス |
| `GMAIL_APP_PASSWORD` | Gmail アプリパスワード |
| `NOTION_API_KEY` | Notion インテグレーションの API キー |
| `NOTION_DATA_SOURCE_ID` | 転送先 Notion データベースの ID |
| `FROM_EMAIL` | 転送対象の送信元メールアドレス |

## 使い方

### ローカル実行

```bash
make run
```

### Lint / Format

```bash
make lint    # ruff + mypy
make format  # ruff format
```

## GitHub Actions

`.github/workflows/mail-transfer.yml` で定義されており、毎週火曜 2:00 JST（UTC 月曜 17:00）に自動実行されます。
手動実行は `workflow_dispatch` から行えます。

リポジトリの Secrets に以下を登録してください。

| Secret 名 | 説明 |
|---|---|
| `GMAIL_USERNAME` | Gmail アドレス |
| `GMAIL_APP_PASSWORD` | Gmail アプリパスワード |
| `NOTION_API_KEY` | Notion API キー |
| `NOTION_DATA_SOURCE_ID` | Notion データベース ID |
| `FROM_EMAIL` | 転送対象の送信元アドレス |
| `DOTENV_PRIVATE_KEY` | dotenvx の復号用秘密鍵 |
