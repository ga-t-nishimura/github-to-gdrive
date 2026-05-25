# GitHub → Google Drive 自動同期システム 設計書

**作成日**: 2026-05-25  
**ステータス**: 承認済み

---

## 背景・目的

PR&マーケティング部では Claude Code で開発したアプリを GitHub で管理しているが、部内の多くのメンバーは GitHub に不慣れなため、以下の役割分担で管理する：

- **GitHub**: コード・プログラム一式
- **Google Drive**: マニュアル・人が読むためのドキュメント・GitHubリポジトリURL 等

mainブランチへのpushをトリガーに、リポジトリ内のドキュメントを対応するGoogle Driveフォルダへ自動同期する仕組みを構築する。

---

## アーキテクチャ

### 採用方式：Composite Action 型

この管理リポジトリ（`github-to-gdrive`）をGitHub Composite Actionとして公開し、各対象リポジトリのワークフローから呼び出す。

```
① 開発者が main ブランチに push
   各対象リポジトリ: .github/workflows/sync-to-gdrive.yml
         │
         │ GitHub Actions トリガー
         ▼
② Composite Action を呼び出し
   uses: ga-t-nishimura/github-to-gdrive@main
         │
         ├──────────────────────────────────┐
         ▼                                  ▼
③ スプレッドシートから設定取得       ④ ファイルをチェックアウト
   フォルダID・ファイルパターン          README.md, docs/*.md 等
         │                                  │
         └──────────────┬───────────────────┘
                        ▼
⑤ Markdown → Google Docs 形式に変換
                        ▼
⑥ Google Drive API で対象フォルダに上書きアップロード
```

### コンポーネント

| コンポーネント | 内容 |
|--------------|------|
| **管理リポジトリ** (`github-to-gdrive`) | `action.yml`（Composite Action定義）・`sync.py`（同期ロジック）・`README.md`（セットアップ手順） |
| **各対象リポジトリ** | `.github/workflows/sync-to-gdrive.yml`（数行の呼び出しコードのみ） |
| **Google スプレッドシート** | リポジトリとGoogle Driveフォルダの対応表 |
| **Google Drive** | 同期先フォルダ（Google Docs形式で保存） |

---

## Google スプレッドシート（対応表）の構成

| 列 | 項目 | 例 |
|----|------|----|
| A列 | GitHubリポジトリURL | `https://github.com/org/project-a` |
| B列 | Google Driveフォルダ名（参照用） | `プロジェクトAマニュアル` |
| C列 | Google DriveフォルダID | `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms` |
| D列 | 同期ファイルパターン | `README.md,docs/*.md` |
| E列 | 有効フラグ | `TRUE` / `FALSE` |

> **注意**: フォルダ名（B列）は人が確認するための参照用。同期処理ではC列のIDを使用する。

---

## 各対象リポジトリのワークフロー

```yaml
# .github/workflows/sync-to-gdrive.yml
name: Sync docs to Google Drive

on:
  push:
    branches: [main]

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ga-t-nishimura/github-to-gdrive@main
        with:
          google_credentials: ${{ secrets.GOOGLE_CREDENTIALS }}
          spreadsheet_id: ${{ secrets.GDRIVE_SPREADSHEET_ID }}
```

---

## ファイル同期の仕様

- **同期方式**: ファイルパターンはリポジトリごとにスプレッドシートで設定（例: `README.md,docs/*.md`）
- **出力形式**: Markdown → Google Docs 形式に変換してアップロード（部内メンバーがそのまま開けるように）
- **更新方式**: 既存ファイルは上書き、なければ新規作成

---

## 認証情報

| 情報 | 保存場所 | 説明 |
|------|---------|------|
| `GOOGLE_CREDENTIALS` | GitHub Secrets（各リポジトリ） | Google Service Account の JSON 鍵 |
| `GDRIVE_SPREADSHEET_ID` | GitHub Secrets（各リポジトリ） | 対応表スプレッドシートのID（全リポジトリで同じ値を設定する） |

---

## エラー処理

| 状況 | 動作 |
|------|------|
| リポジトリが対応表にない | 警告ログを出してスキップ（Actionsは成功扱い） |
| ファイルが見つからない | そのファイルのみスキップ、他のファイルは続行 |
| Google Drive API エラー | GitHub Actions を失敗にしてログに記録 |
| 認証エラー | 即座に失敗・エラーメッセージを表示 |

---

## テスト方針

| テスト種別 | 内容 |
|-----------|------|
| ユニットテスト | `sync.py` の各関数（スプレッドシート読み込み・ファイルパターンマッチ・Markdown変換）をモックを使ってテスト |
| 結合テスト | テスト用リポジトリ＋テスト用Google Driveフォルダを用意し、実際にActionsを動かして確認 |
| 手動確認 | 初回セットアップ時に管理者がワークフローを手動トリガーして動作確認 |

---

## 初回セットアップ手順（管理者向け）

```
1. Google Cloud で Service Account を作成し、鍵JSON を取得
2. Service Account に Google Drive・Sheets の編集権限を付与
3. 対応表スプレッドシートを作成し、Service Account を共有設定に追加
4. 各対象リポジトリの GitHub Secrets に以下を設定：
   - GOOGLE_CREDENTIALS  ← Service Account の JSON 内容
   - GDRIVE_SPREADSHEET_ID  ← スプレッドシートのID
5. .github/workflows/sync-to-gdrive.yml を各リポジトリに追加
6. スプレッドシートに対応行を追記して動作確認
```

---

## 費用について（README.md にも記載すること）

### 基本的に無料の部分

| コンポーネント | 費用 | 理由 |
|--------------|------|------|
| Google Sheets API | 無料 | 読み込み頻度がAPI上限（100リクエスト/100秒）に届かない |
| Google Drive API | 無料 | ドキュメントのアップロードは無料枠内に収まる |
| Google Cloud Service Account | 無料 | Drive・Sheets APIは課金不要 |
| Google Drive ストレージ | 無料（実質） | Markdownをドキュメント変換したファイルは数KB〜数十KB程度 |

### 注意が必要な部分：GitHub Actions 実行時間（privateリポジトリの場合）

| プラン | 無料枠 | 超過時の費用 |
|--------|--------|-------------|
| GitHub Free | 2,000分/月 | $0.008/分 |
| GitHub Team | 3,000分/月 | $0.008/分 |

- 1回の同期実行は約1〜2分
- 10リポジトリ × 1日5回push = 月500〜1,000分程度（無料枠内に収まる見込み）
- **publicリポジトリであれば完全無料・無制限**

**結論**: ほぼ無料で運用できる。privateリポジトリが多く、pushが非常に頻繁な場合のみ無料枠を超える可能性がある。

---

## 今後の拡張候補（スコープ外）

- 対応表への追加をトリガーに自動でワークフローを配置する仕組み
- 同期成功・失敗をSlackやメールで通知
- Google Docs以外の出力形式（PDF等）への対応
