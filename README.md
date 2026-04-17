# mail-transfer

Gmail の受信メールを Notion データベースへ自動転送する Python 製 CLI ツールです。
GitHub Actions により毎週火曜 2:00 JST にスケジュール実行され、ニュースレター等の定期メールを自動でストックします。

---

## 目次

1. [開発した背景](#開発した背景)
2. [使用技術](#使用技術)
3. [アーキテクチャ・ダイアグラム](#アーキテクチャダイアグラム)
4. [ディレクトリ構成](#ディレクトリ構成)
5. [こだわり・工夫した点](#こだわり工夫した点)
6. [環境構築手順](#環境構築手順)
7. [使い方](#使い方)
8. [今後の方針](#今後の方針)

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

## こだわり・工夫した点

### 1. ポート＆アダプターパターンと DI によるドメインの隔離

ドメイン層を外部の技術的な詳細（Gmail / Notion）から完全に隔離し、ビジネスロジックを純粋に保ちます。

- **ドメインの抽象化**: `src/domain/interfaces.py` に Protocol を定義し、「メールを取得する」「エクスポートする」というドメインの関心事だけを記述します。
- **インフラ層の差し替え**: `injector` を用いて、実行時に Gmail や Notion といった具体的なインフラ実装を注入（DI）します。
- **テストの効率化**: テスト時はモック実装を DI で差し替えるだけで、外部 API に依存しない高速かつ堅牢な検証が可能です。

```python
class MailFetcher(Protocol):
    def fetch_all(self) -> list[Mail]: ...

class MailExporter(Protocol):
    def export(self, mail: Mail) -> None: ...
```

### 2. dotenvx による秘密情報の暗号化管理

`.env.encrypted` をリポジトリに含め、復号キーのみ GitHub Secrets / 環境変数で管理します。
平文の `.env` をリポジトリに含めずに秘密情報をコードと一緒にバージョン管理できます。

### 3. mypy + ruff による型安全性

`mypy`で全ファイルに型を強制し、`ruff` で静的解析・フォーマットを自動化しています。
pre-commit フックと組み合わせることで、コミット前にコード品質を担保しています。

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

[dotenvx](https://dotenvx.com/) を使って `.env.encrypted` に暗号化して保存します。Docker イメージに dotenvx が入っており、リポジトリが `/app` にマウントされるため、**ホストに dotenvx を入れずに**、以下のようにコンテナ内で `dotenvx set` を実行します。`.env.encrypted` と `.env.keys` はワークスペース直下に生成・更新されます。

```bash
# 各環境変数を設定
docker compose run --rm mail-transfer dotenvx set GMAIL_USERNAME your@gmail.com
docker compose run --rm mail-transfer dotenvx set GMAIL_APP_PASSWORD xxxx-xxxx-xxxx-xxxx
docker compose run --rm mail-transfer dotenvx set NOTION_API_KEY secret_...
docker compose run --rm mail-transfer dotenvx set NOTION_DATA_SOURCE_ID <data-source-id>
docker compose run --rm mail-transfer dotenvx set FROM_EMAIL sender@example.com

# 任意：件名がこの文字列で始まるメールのみ転送
docker compose run --rm mail-transfer dotenvx set SUBJECT_PREFIX '[Newsletter] '
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
make install

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

---

## 今後の方針

現状の実装を踏まえ、優先度の高い順に改善したい点です。

- **取得対象の絞り込み**: IMAP で送信元以外に、受信日時・未読のみ・ラベルなどでフィルタできるようにし、毎回の取得件数とAPI呼び出しを抑える。
- **失敗時の堅牢性**: Notion API の一時的なエラーに対するリトライ、部分成功時のログと終了コードの整理、必要なら失敗通知（メール・Slack 等）で運用の見える化をする。
- **添付ファイル**: 現状は本文中心。画像や PDF があるメールでは、Notion ブロックや外部ストレージ連携で扱えるように拡張する。
