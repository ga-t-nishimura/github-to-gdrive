# github-to-gdrive

mainブランチへのpushをトリガーに、GitHubリポジトリ内のMarkdownドキュメントをGoogle DriveへGoogle Docs形式で自動同期するGitHub Composite Actionです。

## 概要

- **トリガー**: mainブランチへのpush（または手動実行）
- **設定管理**: Google スプレッドシートでリポジトリ↔フォルダの対応を管理
- **出力形式**: Markdown → Google Docs（部内メンバーがそのまま開いて読める）

## セットアップ手順

### 1. Google Service Account の作成

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを作成（または既存を使用）
2. 「APIとサービス」→「ライブラリ」で以下の2つのAPIを有効化
   - **Google Drive API**
   - **Google Sheets API**
3. 「APIとサービス」→「認証情報」→「サービスアカウントを作成」
4. サービスアカウントを作成後、「キー」タブ→「鍵を追加」→「JSON」で鍵ファイルをダウンロード

> ⚠️ **最小権限の原則**: Service Account には必要最小限の権限のみ付与してください。
> Drive 全体のオーナー権限は**与えないでください**。
> 対象スプレッドシートと各 Drive フォルダに対する「編集者」権限のみで動作します。

### 2. Google スプレッドシートの準備

1. 新しいスプレッドシートを作成
2. 1行目にヘッダーを入力（任意）
3. 2行目以降に対応情報を入力:

| A列: GitHubリポジトリURL | B列: GDriveフォルダ名（参照用） | C列: GDriveフォルダID | D列: 同期ファイルパターン | E列: 有効 |
|---|---|---|---|---|
| https://github.com/org/project-a | プロジェクトAマニュアル | 1BxiMVs...（フォルダURLの末尾） | README.md,docs/*.md | TRUE |

> **フォルダIDの取得方法**: Google DriveでフォルダをブラウザUCで開き、URLの末尾の文字列がフォルダIDです。  
> 例: `https://drive.google.com/drive/folders/`**`1BxiMVs0XRA5nFMdKvBd`** ← この部分

4. 作成したサービスアカウントのメールアドレス（例: `xxx@yyy.iam.gserviceaccount.com`）を  
   スプレッドシートの「共有」に**編集者**として追加
5. 各対象フォルダにも同じサービスアカウントを**編集者**として共有

### 3. 各対象リポジトリへの設定

#### GitHub Secrets の設定

対象リポジトリの「Settings」→「Secrets and variables」→「Actions」で以下を追加:

| Secret名 | 値 |
|---|---|
| `GOOGLE_CREDENTIALS` | ダウンロードしたService AccountのJSONファイルの**中身**（テキスト全体） |
| `GDRIVE_SPREADSHEET_ID` | 対応表スプレッドシートのID（URLの`/d/`と`/edit`の間の文字列）|

> **スプレッドシートIDの取得方法**: スプレッドシートのURLを確認してください。  
> `https://docs.google.com/spreadsheets/d/`**`1BxiMVs0XRA5nFMdKv`**`/edit` ← 太字部分がID

> `GDRIVE_SPREADSHEET_ID` の値は全リポジトリで同じです。

#### ワークフローファイルの追加

このリポジトリにある `workflow-template.yml` を対象リポジトリの  
`.github/workflows/sync-to-gdrive.yml` としてコピーしてコミットします。

```bash
# 対象リポジトリで実行
mkdir -p .github/workflows
curl -o .github/workflows/sync-to-gdrive.yml \
  https://raw.githubusercontent.com/ga-t-nishimura/github-to-gdrive/main/workflow-template.yml
git add .github/workflows/sync-to-gdrive.yml
git commit -m "ci: Google Drive同期ワークフローを追加"
git push
```

### 4. 動作確認

GitHubのActionsタブから「Sync docs to Google Drive」→「Run workflow」で手動実行できます。  
ログで `Done. X file(s) synced to Google Drive folder '...'` と表示されれば成功です。

---

## セキュリティについて

### Service Account の最小権限

Service Account には以下の権限**のみ**を付与してください（Drive全体への権限は不要）:

- 対応表スプレッドシート → **閲覧者**（読み取りのみ）
- 各同期先 Drive フォルダ → **編集者**（ファイル作成・更新に必要）

### 鍵のローテーション

`GOOGLE_CREDENTIALS` に登録した Service Account の鍵は定期的にローテーションすることを推奨します:

1. Google Cloud Console でサービスアカウントに新しい鍵を追加
2. 全対象リポジトリの `GOOGLE_CREDENTIALS` Secret を新しい鍵で更新
3. 旧い鍵を Google Cloud Console で削除

### バージョン固定（本番運用推奨）

`workflow-template.yml` の `uses` は `@main` を参照していますが、  
本番環境ではタグや SHA で固定することを推奨します:

```yaml
- uses: ga-t-nishimura/github-to-gdrive@v1  # タグで固定
```

---

## 費用について

### 基本的に無料

| コンポーネント | 費用 | 備考 |
|---|---|---|
| Google Sheets API | **無料** | 読み込み頻度がAPI上限（100リクエスト/100秒）に届かない |
| Google Drive API | **無料** | ドキュメントアップロードは無料枠内に収まる |
| Google Cloud Service Account | **無料** | Drive・Sheets APIは課金不要 |
| Google Drive ストレージ | **無料（実質）** | Markdownを変換したドキュメントは数KB〜数十KB程度 |

### 注意が必要な点: GitHub Actions 実行時間（privateリポジトリの場合）

| プラン | 月間無料枠 | 超過時の費用 |
|---|---|---|
| GitHub Free | 2,000分/月 | $0.008/分 |
| GitHub Team | 3,000分/月 | $0.008/分 |

- 1回の同期実行: 約1〜2分
- 目安: 10リポジトリ × 1日5回push = 月500〜1,000分程度 → **無料枠内に収まる見込み**
- **publicリポジトリは完全無料・無制限**

**結論**: ほぼ無料で運用できます。

---

## 同期ファイルパターンの書き方

| パターン例 | 対象ファイル |
|---|---|
| `README.md` | ルート直下のREADME.mdのみ |
| `docs/*.md` | docsフォルダ直下のすべての.mdファイル |
| `README.md,docs/*.md` | 上記2つを組み合わせ |
| `**/*.md` | すべてのフォルダのすべての.mdファイル |

> **Google Doc 名について**: サブディレクトリ内のファイルは `docs / guide` のようにパスを含めた名前で保存されます（同名ファイルの衝突を防ぐため）。
