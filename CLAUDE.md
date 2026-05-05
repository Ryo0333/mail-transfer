# mail-transfer

Gmail の受信メールを Notion データベースへ自動転送する Python 製 CLI ツール。

## 開発コマンド

すべてのコマンドは Docker コンテナ内で実行する（`make` 経由）。

```bash
make install   # 依存パッケージインストール (uv sync)
make test      # pytest でテスト実行
make lint      # ruff check + mypy による静的解析・型チェック
make format    # ruff format によるコード整形
make run       # メール転送ジョブを実行（DOTENV_PRIVATE_KEY が必要）
```

`make lint` はコミット前に必ず通すこと。

## アーキテクチャ

ポート＆アダプターパターン（Hexagonal Architecture）を採用。

```
src/
├── domain/
│   ├── interfaces.py          # MailFetcher / MailExporter Protocol 定義
│   └── models/mail.py         # Mail データモデル
├── infrastructure/
│   ├── gmail/
│   │   ├── gmail.py           # IMAP メール取得（GmailClient）
│   │   └── provider.py        # injector バインド
│   └── notion/
│       ├── notion.py          # Notion API ページ作成（NotionClient）
│       └── provider.py        # injector バインド
├── usecase/
│   └── mail_transfer_service.py  # フェッチ → エクスポートのオーケストレーション
├── main.py
├── settings.py
└── logger.py
```

- **ドメイン層**はインフラ実装に依存しない。`injector` で DI する。
- テスト時はモック実装を DI で差し替えるだけで外部 API 不要。
- 環境変数は `dotenvx` で `.env.encrypted` に暗号化済み。復号キーは GitHub Secrets / 環境変数 `DOTENV_PRIVATE_KEY` で管理。

## コーディング規約

### 命名

- ファイル内限定の関数・変数は先頭に `_` を付ける

### ファイルサイズ

- 各ファイルは最大 100 行程度（import 文は除く）

### 設計原則

- **単一責任原則**: 機能追加時は責務を分割する
- **YAGNI**: 今必要な機能のみ実装。将来のための拡張は不要
- **KISS**: 最もシンプルな解決策を選ぶ
- **DRY**: 3 箇所目で共通化を検討。2 箇所なら重複を許容
- **OAOO**: 同じロジックは 1 箇所にのみ実装

### 型・品質

- 関数定義には引数・返り値の型ヒントを必ず付ける（mypy strict）
- `while True` などの非推奨パターンは使わない
- 変更後は `make lint` でエラーがないことを確認

### コメント

- コードだけで意図が伝わる場合はコメント不要
- 複雑なアルゴリズムや特殊なライブラリの使い方にのみ簡潔なコメントを付ける

### import 文

- 必要なものだけを使う。既存コードの import は勝手に変更・削除しない

### 修正範囲

- 依頼された箇所以外は原則変更しない

## 技術スタック

| カテゴリ | 技術 |
|------|------|
| 言語 | Python 3.13 |
| パッケージ管理 | uv |
| HTTP クライアント | httpx |
| メール取得 | imap-tools (IMAP) |
| DI | injector |
| バリデーション | pydantic / pydantic-settings |
| HTML パース | beautifulsoup4 |
| 静的解析 | ruff, mypy (strict) |
| テスト | pytest |
| コンテナ | Docker |
| CI/CD | GitHub Actions（毎週火曜 2:00 JST 自動実行） |
