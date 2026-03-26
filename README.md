# mail-transfer

Gmail の受信メールを Notion データベースへ自動転送する Python 製 CLI ツールです。
GitHub Actions により毎週火曜 2:00 JST にスケジュール実行され、ニュースレター等の定期メールを自動でストックします。

---

## 目次

1. [開発した背景](#開発した背景)
2. [使用技術](#使用技術)
3. [アーキテクチャ・ダイアグラム](#アーキテクチャダイアグラム)
4. [ディレクトリ構成](#ディレクトリ構成)
5. [API 一覧](#api-一覧)
6. [こだわり・工夫した点](#こだわり工夫した点)
7. [環境構築手順](#環境構築手順)
8. [使い方](#使い方)

---

## 開発した背景

毎週届くニュースレターを Gmail で受け取るものの、読み返したいときに埋もれてしまい検索しづらいという課題がありました。
Notion で情報を一元管理していたため、「メールが届いたら自動で Notion に転送・保存する仕組みがあれば便利」と考え本ツールを開発しました。

手動コピーを完全になくしたこと、週次スケジュール実行で運用コストをゼロに抑えたことが主な成果です。

---

## 使用技術


| カテゴリ  | 技術・ツール         |
| ----- | -------------- |
| 言語    | Python 3.13    |
| コンテナ化 | Docker         |
| CI/CD | GitHub Actions |


---

## アーキテクチャ・ダイアグラム

### データフロー

```
Gmail (IMAP)
    │
    ▼
GmailClient.fetch_all()          ← IMAPでメール一括取得・フィルタリング
    │  HTML → プレーンテキスト変換
    ▼
MailTransferService.execute()    ← ユースケース層でオーケストレーション
    │  件名重複チェック
    ▼
NotionClient.export()            ← Notion API でページ作成
    │
    ▼
Notion データベース
```

### レイヤー構成（ポート＆アダプター）

```
┌─────────────────────────────────────────────┐
│  Entrypoint  (src/main.py)                  │
│  ┌───────────────────────────────────────┐  │
│  │  Usecase  (MailTransferService)       │  │
│  │  ┌─────────────────────────────────┐ │  │
│  │  │  Domain  (interfaces / models)  │ │  │
│  │  └────────────┬────────────────────┘ │  │
│  └───────────────┼───────────────────────┘  │
│                  │ Protocol                  │
│  ┌───────────────▼───────────────────────┐  │
│  │  Infrastructure                       │  │
│  │  ├── gmail/   (GmailClient)           │  │
│  │  └── notion/  (NotionClient)          │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

---

## ディレクトリ構成

```
mail-transfer/
├── src/
│   ├── domain/
│   │   ├── interfaces.py              # MailFetcher / MailExporter プロトコル定義
│   │   └── models/
│   │       └── mail.py                # Mail データモデル
│   ├── infrastructure/
│   │   ├── gmail/
│   │   │   ├── gmail.py               # IMAP メール取得（GmailClient）
│   │   │   └── provider.py            # Injector 用バインド
│   │   └── notion/
│   │       ├── notion.py              # Notion API ページ作成（NotionClient）
│   │       └── provider.py            # Injector 用バインド
│   ├── usecase/
│   │   └── mail_transfer_service.py   # フェッチ → エクスポートのオーケストレーション
│   ├── main.py
│   ├── settings.py
│   └── logger.py
├── tests/
│   ├── domain/models/test_mail.py
│   ├── infrastructure/gmail/test_gmail.py
│   ├── infrastructure/notion/test_notion.py
│   └── usecase/test_mail_transfer_service.py
├── .github/workflows/mail-transfer.yml
├── .env.encrypted                     # dotenvx で暗号化された環境変数
├── compose.yaml
├── Dockerfile
├── Makefile
└── pyproject.toml
```

---

## API 一覧

本ツールが利用する外部 API・プロトコルの一覧です。

### Gmail IMAP


| 項目    | 内容                         |
| ----- | -------------------------- |
| サーバー  | `imap.gmail.com:993` (SSL) |
| 認証    | Gmail アプリパスワード             |
| 操作    | 受信トレイのメール取得（`FROM` フィルタ）   |
| ライブラリ | imap-tools                 |


### Notion API


| メソッド   | エンドポイント                                   | 用途                     |
| ------ | ----------------------------------------- | ---------------------- |
| `POST` | `/v1/data_sources/{data_source_id}/query` | 同一件名のページが既存かチェック（重複防止） |
| `POST` | `/v1/pages`                               | メールをページとして新規作成         |


**リクエスト例（ページ作成）**

```json
{
  "parent": { "type": "data_source_id", "data_source_id": "<ID>" },
  "properties": {
    "Name": { "title": [{ "text": { "content": "<件名>" } }] }
  },
  "children": [
    {
      "object": "block",
      "type": "paragraph",
      "paragraph": { "rich_text": [{ "text": { "content": "<本文>" } }] }
    }
  ]
}
```

---

## こだわり・工夫した点

### 1. ポート＆アダプターパターンによる疎結合設計

`src/domain/interfaces.py` に `MailFetcher` / `MailExporter` の Protocol を定義し、ユースケース層は具体的な実装（Gmail・Notion）に依存しません。
Gmail を別のメールプロバイダに、Notion を別のストレージに差し替える場合も、インフラ層の実装を追加するだけで済みます。

```python
class MailFetcher(Protocol):
    def fetch_all(self) -> list[Mail]: ...

class MailExporter(Protocol):
    def export(self, mail: Mail) -> None: ...
```

### 2. injector による DI（依存性注入）

`injector` ライブラリで `MailFetcher` / `MailExporter` の実装をバインドし、`MailTransferService` はコンストラクタインジェクションで受け取ります。
テスト時はモック実装をバインドするだけで、外部 API への接続なしにユースケースのテストが可能です。

### 3. HTML メールのプレーンテキスト変換

BeautifulSoup でリンクを `表示テキスト (URL)` 形式に変換してからテキスト抽出することで、Notion 上でも URL が失われずに読めます。

### 4. Notion への重複登録防止

ページ作成前に `data_sources/{id}/query` で同一件名を検索し、既存ページがあればスキップします。
スケジュール実行を繰り返しても冪等に動作します。

### 5. dotenvx による秘密情報の暗号化管理

`.env.encrypted` をリポジトリに含め、復号キーのみ GitHub Secrets / 環境変数で管理します。
平文の `.env` をリポジトリに含めずに秘密情報をコードと一緒にバージョン管理できます。

### 6. mypy strict + ruff による型安全性

`mypy --strict` モードで全ファイルに型を強制し、`ruff` で静的解析・フォーマットを自動化しています。
pre-commit フックと組み合わせることで、コミット前にコード品質を担保しています。

### 7. Notion rich_text の 2000 文字制限への対応

Notion API の `rich_text` フィールドは 1 要素あたり 2000 文字が上限です。
本文を 2000 文字ごとに分割して複数の paragraph ブロックとして送信することで、長文メールにも対応しています。

---

## 環境構築手順

### 必要なもの

- Docker（推奨）
- Gmail アカウント（アプリパスワード発行済み）
- Notion アカウント（API キー + 転送先データベース ID）

### 1. リポジトリのクローン

```bash
git clone https://github.com/<your-username>/mail-transfer.git
cd mail-transfer
```

### 2. 環境変数の設定

[dotenvx](https://dotenvx.com/) を使って `.env.encrypted` に暗号化して保存します。

```bash
# dotenvx インストール（未インストールの場合）
curl -sfS https://dotenvx.sh/install.sh | sh

# 各環境変数を設定（.env.encrypted と .env.keys が自動生成されます）
dotenvx set GMAIL_USERNAME your@gmail.com
dotenvx set GMAIL_APP_PASSWORD xxxx-xxxx-xxxx-xxxx
dotenvx set NOTION_API_KEY secret_...
dotenvx set NOTION_DATA_SOURCE_ID <data-source-id>
dotenvx set FROM_EMAIL sender@example.com

# 任意：件名がこの文字列で始まるメールのみ転送
dotenvx set SUBJECT_PREFIX '[Newsletter] '
```


| 変数名                     | 必須  | 説明                       |
| ----------------------- | --- | ------------------------ |
| `GMAIL_USERNAME`        | ✅   | Gmail アドレス               |
| `GMAIL_APP_PASSWORD`    | ✅   | Gmail アプリパスワード           |
| `NOTION_API_KEY`        | ✅   | Notion インテグレーションの API キー |
| `NOTION_DATA_SOURCE_ID` | ✅   | 転送先 Notion データソースの ID    |
| `FROM_EMAIL`            | ✅   | 転送対象の送信元メールアドレス          |
| `SUBJECT_PREFIX`        | ─   | 指定時は、この文字列で始まる件名のみ処理     |


### 3. 実行

```bash
# 復号キーをエクスポート（.env.keys の DOTENV_PRIVATE_KEY の値）
export DOTENV_PRIVATE_KEY='<復号用の秘密鍵>'

# Docker でジョブ実行
make run
```

### ホスト環境での開発

```bash
# uv でパッケージインストール
uv sync

# テスト
make test

# Lint / 型チェック
make lint

# フォーマット
make format
```

---

## 使い方

### 転送ジョブの手動実行

```bash
export DOTENV_PRIVATE_KEY='<復号用の秘密鍵>'
make run
```

### GitHub Actions による自動実行

`.github/workflows/mail-transfer.yml` で毎週火曜 2:00 JST に自動実行されます。
リポジトリの **Settings → Secrets** に以下を登録してください。


| Secret 名             | 説明              |
| -------------------- | --------------- |
| `DOTENV_PRIVATE_KEY` | dotenvx の復号用秘密鍵 |


