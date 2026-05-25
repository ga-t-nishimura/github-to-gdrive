# GitHub → Google Drive 自動同期システム 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** mainブランチへのpushをトリガーに、スプレッドシートの対応表を参照してMarkdownドキュメントをGoogle DocsとしてGoogle Driveへ自動同期するGitHub Composite Actionを構築する。

**Architecture:** GitHub Composite Actionとして`ga-t-nishimura/github-to-gdrive`リポジトリを公開し、各対象リポジトリのワークフローから`uses:`で呼び出す。Action内でPythonスクリプト（sync.py）が起動し、Google Sheets APIで対応表を参照、MarkdownをHTMLに変換後Google Drive APIでアップロードする。

**Tech Stack:** Python 3.11, google-api-python-client, google-auth, markdown（Python library）, pytest, pytest-mock

> **Codex レビュー反映済み（v2）**: ファイル名衝突修正・URL正規化・クエリエスケープ・main()統合テスト・最小権限設定を追加

---

## ファイル構成

```
github-to-gdrive/
├── action.yml                 # GitHub Composite Action 定義（エントリポイント）
├── sync.py                    # メイン同期オーケストレーション
├── spreadsheet.py             # Google Sheets 読み込みロジック
├── converter.py               # Markdown → HTML 変換ロジック
├── drive.py                   # Google Drive アップロードロジック
├── requirements.txt           # Python 依存パッケージ
├── workflow-template.yml      # 対象リポジトリ用ワークフローテンプレート（コピー用）
├── README.md                  # セットアップ手順・費用説明
├── .gitignore
└── tests/
    ├── __init__.py
    ├── test_converter.py      # converter.py の単体テスト（5件）
    ├── test_spreadsheet.py    # spreadsheet.py の単体テスト（7件）
    ├── test_drive.py          # drive.py の単体テスト（4件）
    └── test_sync.py           # sync.py のテスト（10件）
```

---

## Task 1: プロジェクトのスキャフォールディング

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `tests/__init__.py`

- [ ] **Step 1: `requirements.txt` を作成する**

```
# requirements.txt
google-api-python-client>=2.100.0
google-auth>=2.20.0
markdown>=3.4.0
pytest>=7.4.0
pytest-mock>=3.11.0
```

- [ ] **Step 2: `.gitignore` を作成する**

```
# .gitignore
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/
dist/
.env
credentials.json
.superpowers/
```

- [ ] **Step 3: `tests/__init__.py` を作成する（空ファイル）**

```python
# tests/__init__.py
```

- [ ] **Step 4: 依存パッケージをインストールしてコマンドが通ることを確認する**

Run: `pip install -r requirements.txt`
Expected: `Successfully installed ...` でエラーなし

- [ ] **Step 5: pytest が動くことを確認する**

Run: `pytest tests/ -v`
Expected: `no tests ran` （テストはまだないため）

- [ ] **Step 6: コミット**

```bash
git add requirements.txt .gitignore tests/__init__.py
git commit -m "chore: プロジェクトのスキャフォールディング"
```

---

## Task 2: Markdown → HTML コンバーターの実装（TDD）

**Files:**
- Create: `tests/test_converter.py`
- Create: `converter.py`

- [ ] **Step 1: テストファイルを作成する**

```python
# tests/test_converter.py
from converter import markdown_to_html


def test_converts_h1_heading():
    result = markdown_to_html("# Hello World")
    assert "<h1>Hello World</h1>" in result


def test_converts_bold():
    result = markdown_to_html("This is **bold** text")
    assert "<strong>bold</strong>" in result


def test_converts_table():
    md = "| A | B |\n|---|---|\n| 1 | 2 |"
    result = markdown_to_html(md)
    assert "<table>" in result


def test_converts_fenced_code_block():
    md = "```python\nprint('hello')\n```"
    result = markdown_to_html(md)
    assert "<code>" in result


def test_empty_input_returns_empty_string():
    result = markdown_to_html("")
    assert result == ""
```

- [ ] **Step 2: テストが失敗することを確認する**

Run: `pytest tests/test_converter.py -v`
Expected: `ModuleNotFoundError: No module named 'converter'` で FAIL

- [ ] **Step 3: `converter.py` を実装する**

```python
# converter.py
import markdown as md_lib


def markdown_to_html(markdown_content: str) -> str:
    """Markdown テキストを HTML 文字列に変換する。

    Args:
        markdown_content: 変換元の Markdown テキスト

    Returns:
        変換後の HTML 文字列。入力が空の場合は空文字列を返す。
    """
    if not markdown_content:
        return ""
    return md_lib.markdown(
        markdown_content,
        extensions=["tables", "fenced_code"],
    )
```

- [ ] **Step 4: テストが全件パスすることを確認する**

Run: `pytest tests/test_converter.py -v`
Expected: 5 passed

- [ ] **Step 5: コミット**

```bash
git add tests/test_converter.py converter.py
git commit -m "feat: Markdown → HTML コンバーターを実装"
```

---

## Task 3: Google Spreadsheet 読み込みの実装（TDD）

**Files:**
- Create: `tests/test_spreadsheet.py`
- Create: `spreadsheet.py`

> **修正点（Codex レビュー）**: TypedDict 導入・URL正規化・空パターンフィルタリングを追加

- [ ] **Step 1: テストファイルを作成する**

```python
# tests/test_spreadsheet.py
from unittest.mock import MagicMock, patch
from spreadsheet import get_repo_config, normalize_repo_url

# スプレッドシートのサンプルデータ（1行目はヘッダー）
SAMPLE_VALUES = [
    ["GitHubリポジトリURL", "フォルダ名", "フォルダID", "ファイルパターン", "有効"],
    [
        "https://github.com/org/project-a",
        "プロジェクトAマニュアル",
        "folder-id-abc",
        "README.md,docs/*.md",
        "TRUE",
    ],
    [
        "https://github.com/org/project-b",
        "プロジェクトBマニュアル",
        "folder-id-def",
        "README.md",
        "FALSE",
    ],
]


def _make_mock_service(values):
    """Google Sheets API サービスのモックを生成するヘルパー。"""
    mock_service = MagicMock()
    (
        mock_service.spreadsheets.return_value
        .values.return_value
        .get.return_value
        .execute.return_value
    ) = {"values": values}
    return mock_service


@patch("spreadsheet.build")
@patch("spreadsheet._get_credentials")
def test_returns_config_for_known_repo(mock_creds, mock_build):
    mock_build.return_value = _make_mock_service(SAMPLE_VALUES)

    config = get_repo_config("sheet-id", "https://github.com/org/project-a", "{}")

    assert config is not None
    assert config["folder_id"] == "folder-id-abc"
    assert config["folder_name"] == "プロジェクトAマニュアル"
    assert config["file_patterns"] == ["README.md", "docs/*.md"]
    assert config["enabled"] is True


@patch("spreadsheet.build")
@patch("spreadsheet._get_credentials")
def test_returns_none_for_unknown_repo(mock_creds, mock_build):
    mock_build.return_value = _make_mock_service(SAMPLE_VALUES)

    config = get_repo_config("sheet-id", "https://github.com/org/unknown", "{}")

    assert config is None


@patch("spreadsheet.build")
@patch("spreadsheet._get_credentials")
def test_returns_none_for_disabled_repo(mock_creds, mock_build):
    mock_build.return_value = _make_mock_service(SAMPLE_VALUES)

    config = get_repo_config("sheet-id", "https://github.com/org/project-b", "{}")

    assert config is None


@patch("spreadsheet.build")
@patch("spreadsheet._get_credentials")
def test_handles_empty_spreadsheet(mock_creds, mock_build):
    mock_build.return_value = _make_mock_service([])

    config = get_repo_config("sheet-id", "https://github.com/org/any", "{}")

    assert config is None


@patch("spreadsheet.build")
@patch("spreadsheet._get_credentials")
def test_matches_url_with_trailing_slash(mock_creds, mock_build):
    """スプレッドシートのURLに末尾スラッシュがあっても一致する。"""
    values = [
        ["https://github.com/org/project-a/", "テスト", "folder-id", "README.md", "TRUE"],
    ]
    mock_build.return_value = _make_mock_service(values)

    config = get_repo_config("sheet-id", "https://github.com/org/project-a", "{}")
    assert config is not None
    assert config["folder_id"] == "folder-id"


@patch("spreadsheet.build")
@patch("spreadsheet._get_credentials")
def test_matches_url_with_git_suffix(mock_creds, mock_build):
    """スプレッドシートのURLに .git サフィックスがあっても一致する。"""
    values = [
        ["https://github.com/org/project-a.git", "テスト", "folder-id", "README.md", "TRUE"],
    ]
    mock_build.return_value = _make_mock_service(values)

    config = get_repo_config("sheet-id", "https://github.com/org/project-a", "{}")
    assert config is not None


@patch("spreadsheet.build")
@patch("spreadsheet._get_credentials")
def test_filters_empty_patterns_from_trailing_comma(mock_creds, mock_build):
    """末尾カンマなどで生じる空のパターンは除去される。"""
    values = [
        [
            "https://github.com/org/project-a",
            "テスト",
            "folder-id",
            "README.md,,docs/*.md,",
            "TRUE",
        ],
    ]
    mock_build.return_value = _make_mock_service(values)

    config = get_repo_config("sheet-id", "https://github.com/org/project-a", "{}")
    assert config["file_patterns"] == ["README.md", "docs/*.md"]
```

- [ ] **Step 2: テストが失敗することを確認する**

Run: `pytest tests/test_spreadsheet.py -v`
Expected: `ModuleNotFoundError: No module named 'spreadsheet'` で FAIL

- [ ] **Step 3: `spreadsheet.py` を実装する**

```python
# spreadsheet.py
import json
from typing import Optional, TypedDict

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


class RepoConfig(TypedDict):
    """スプレッドシートから取得したリポジトリ同期設定。"""
    folder_id: str
    folder_name: str
    file_patterns: list[str]
    enabled: bool


def _get_credentials(credentials_json: str):
    """Service Account JSON 文字列から認証情報オブジェクトを生成する。"""
    info = json.loads(credentials_json)
    return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)


def normalize_repo_url(url: str) -> str:
    """GitHub リポジトリ URL を正規化する。

    末尾スラッシュ・.git サフィックスを除去し、前後の空白をトリムする。
    スプレッドシート入力のゆらぎに対応するために使用する。

    Args:
        url: 正規化する URL 文字列

    Returns:
        正規化後の URL 文字列
    """
    return url.strip().removesuffix(".git").rstrip("/")


def get_repo_config(
    spreadsheet_id: str,
    repo_url: str,
    credentials_json: str,
) -> Optional[RepoConfig]:
    """スプレッドシートからリポジトリの同期設定を取得する。

    スプレッドシートの列構成:
        A列: GitHub リポジトリ URL
        B列: Google Drive フォルダ名（参照用）
        C列: Google Drive フォルダ ID
        D列: 同期ファイルパターン（カンマ区切り、例: README.md,docs/*.md）
        E列: 有効フラグ（TRUE / FALSE）

    Args:
        spreadsheet_id: 対応表スプレッドシートの ID
        repo_url: 検索する GitHub リポジトリの URL
        credentials_json: Google Service Account の JSON 鍵文字列

    Returns:
        RepoConfig dict（folder_id, folder_name, file_patterns, enabled）。
        リポジトリが見つからない場合、または有効フラグが FALSE の場合は None。
    """
    credentials = _get_credentials(credentials_json)
    service = build("sheets", "v4", credentials=credentials)

    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range="A:E")
        .execute()
    )

    rows = result.get("values", [])
    normalized_url = normalize_repo_url(repo_url)

    for row in rows:
        if len(row) < 5:
            continue
        row_url, folder_name, folder_id, patterns, enabled = (
            row[0], row[1], row[2], row[3], row[4]
        )
        if normalize_repo_url(row_url) != normalized_url:
            continue
        if enabled.strip().upper() != "TRUE":
            return None
        file_patterns = [p.strip() for p in patterns.split(",") if p.strip()]
        return {
            "folder_id": folder_id.strip(),
            "folder_name": folder_name.strip(),
            "file_patterns": file_patterns,
            "enabled": True,
        }

    return None
```

- [ ] **Step 4: テストが全件パスすることを確認する**

Run: `pytest tests/test_spreadsheet.py -v`
Expected: 7 passed

- [ ] **Step 5: コミット**

```bash
git add tests/test_spreadsheet.py spreadsheet.py
git commit -m "feat: Google Spreadsheet読み込みを実装（URL正規化・TypedDict対応）"
```

---

## Task 4: Google Drive アップロードの実装（TDD）

**Files:**
- Create: `tests/test_drive.py`
- Create: `drive.py`

> **修正点（Codex レビュー）**: `_escape_drive_query_value` 追加・`fields="id"` 指定を追加

- [ ] **Step 1: テストファイルを作成する**

```python
# tests/test_drive.py
from unittest.mock import MagicMock, patch
from drive import upload_or_update_file, _escape_drive_query_value


def _make_mock_service(existing_files=None):
    """Google Drive API サービスのモックを生成するヘルパー。"""
    mock_service = MagicMock()
    files_list = existing_files if existing_files is not None else []
    (
        mock_service.files.return_value
        .list.return_value
        .execute.return_value
    ) = {"files": files_list}
    (
        mock_service.files.return_value
        .create.return_value
        .execute.return_value
    ) = {"id": "new-file-id"}
    return mock_service


@patch("drive.build")
@patch("drive._get_credentials")
def test_creates_new_file_when_not_exists(mock_creds, mock_build):
    mock_service = _make_mock_service(existing_files=[])
    mock_build.return_value = mock_service

    file_id = upload_or_update_file("folder-123", "README", "<h1>Hello</h1>", "{}")

    mock_service.files.return_value.create.assert_called_once()
    assert file_id == "new-file-id"


@patch("drive.build")
@patch("drive._get_credentials")
def test_updates_existing_file_when_found(mock_creds, mock_build):
    mock_service = _make_mock_service(
        existing_files=[{"id": "existing-id", "name": "README"}]
    )
    mock_build.return_value = mock_service

    file_id = upload_or_update_file("folder-123", "README", "<h1>Updated</h1>", "{}")

    mock_service.files.return_value.update.assert_called_once()
    mock_service.files.return_value.create.assert_not_called()
    assert file_id == "existing-id"


@patch("drive.build")
@patch("drive._get_credentials")
def test_create_includes_correct_metadata(mock_creds, mock_build):
    mock_service = _make_mock_service(existing_files=[])
    mock_build.return_value = mock_service

    upload_or_update_file("folder-xyz", "ガイド", "<p>内容</p>", "{}")

    create_call_kwargs = mock_service.files.return_value.create.call_args.kwargs
    body = create_call_kwargs["body"]
    assert body["name"] == "ガイド"
    assert body["parents"] == ["folder-xyz"]
    assert body["mimeType"] == "application/vnd.google-apps.document"


@patch("drive.build")
@patch("drive._get_credentials")
def test_query_escapes_single_quote_in_filename(mock_creds, mock_build):
    """シングルクォートを含むファイル名が Drive クエリで正しくエスケープされる。"""
    mock_service = _make_mock_service(existing_files=[])
    mock_build.return_value = mock_service

    upload_or_update_file("folder-123", "Bob's Guide", "<p>content</p>", "{}")

    q = mock_service.files.return_value.list.call_args.kwargs["q"]
    assert "Bob\\'s Guide" in q
```

- [ ] **Step 2: テストが失敗することを確認する**

Run: `pytest tests/test_drive.py -v`
Expected: `ModuleNotFoundError: No module named 'drive'` で FAIL

- [ ] **Step 3: `drive.py` を実装する**

```python
# drive.py
import io
import json
from typing import Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]


def _get_credentials(credentials_json: str):
    """Service Account JSON 文字列から認証情報オブジェクトを生成する。"""
    info = json.loads(credentials_json)
    return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)


def _escape_drive_query_value(value: str) -> str:
    """Google Drive API クエリの値フィールドに使える形式にエスケープする。

    バックスラッシュを先にエスケープし、次にシングルクォートをエスケープする。

    Args:
        value: エスケープする文字列

    Returns:
        エスケープ済み文字列
    """
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _find_existing_file(service, folder_id: str, filename: str) -> Optional[str]:
    """フォルダ内に同名の Google Doc が存在すればそのファイル ID を返す。

    Args:
        service: Google Drive API サービスオブジェクト
        folder_id: 検索対象フォルダの ID
        filename: 検索するファイル名

    Returns:
        ファイル ID 文字列、見つからない場合は None。
    """
    safe_name = _escape_drive_query_value(filename)
    safe_folder_id = _escape_drive_query_value(folder_id)
    query = (
        f"name = '{safe_name}' and "
        f"'{safe_folder_id}' in parents and "
        f"mimeType = 'application/vnd.google-apps.document' and "
        f"trashed = false"
    )
    result = service.files().list(q=query, fields="files(id, name)").execute()
    files = result.get("files", [])
    return files[0]["id"] if files else None


def upload_or_update_file(
    folder_id: str,
    filename: str,
    html_content: str,
    credentials_json: str,
) -> str:
    """HTML コンテンツを Google Doc として指定フォルダにアップロードまたは上書き更新する。

    Args:
        folder_id: アップロード先 Google Drive フォルダの ID
        filename: Google Drive 上でのファイル名（拡張子なし）
        html_content: アップロードする HTML 文字列
        credentials_json: Google Service Account の JSON 鍵文字列

    Returns:
        アップロードまたは更新したファイルの ID。
    """
    credentials = _get_credentials(credentials_json)
    service = build("drive", "v3", credentials=credentials)

    media = MediaIoBaseUpload(
        io.BytesIO(html_content.encode("utf-8")),
        mimetype="text/html",
        resumable=False,
    )

    existing_id = _find_existing_file(service, folder_id, filename)

    if existing_id:
        service.files().update(
            fileId=existing_id, media_body=media, fields="id"
        ).execute()
        return existing_id
    else:
        metadata = {
            "name": filename,
            "parents": [folder_id],
            "mimeType": "application/vnd.google-apps.document",
        }
        result = service.files().create(
            body=metadata, media_body=media, fields="id"
        ).execute()
        return result["id"]
```

- [ ] **Step 4: テストが全件パスすることを確認する**

Run: `pytest tests/test_drive.py -v`
Expected: 4 passed

- [ ] **Step 5: コミット**

```bash
git add tests/test_drive.py drive.py
git commit -m "feat: Google Driveアップロードを実装（クエリエスケープ・fields指定）"
```

---

## Task 5: メイン同期スクリプトの実装（TDD）

**Files:**
- Create: `tests/test_sync.py`
- Create: `sync.py`

> **修正点（Codex レビュー）**: `make_doc_name`（ファイル名衝突防止）・`require_env`・`main()` 統合テストを追加

- [ ] **Step 1: テストファイルを作成する**

```python
# tests/test_sync.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from sync import get_repo_url, get_matching_files, make_doc_name, require_env, main


# ── require_env ──────────────────────────────────────────────

def test_require_env_returns_value_when_set(monkeypatch):
    monkeypatch.setenv("TEST_VAR", "hello")
    assert require_env("TEST_VAR") == "hello"


def test_require_env_raises_when_missing(monkeypatch):
    monkeypatch.delenv("TEST_VAR", raising=False)
    with pytest.raises(RuntimeError, match="TEST_VAR"):
        require_env("TEST_VAR")


# ── get_repo_url ─────────────────────────────────────────────

def test_get_repo_url(monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "org/my-repo")
    assert get_repo_url() == "https://github.com/org/my-repo"


# ── make_doc_name ────────────────────────────────────────────

def test_make_doc_name_root_file(tmp_path):
    """ルート直下のファイルはファイル名のみ（拡張子なし）になる。"""
    file_path = tmp_path / "README.md"
    file_path.write_text("# Hello", encoding="utf-8")
    assert make_doc_name(str(tmp_path), file_path) == "README"


def test_make_doc_name_subdirectory_file(tmp_path):
    """サブディレクトリのファイルはパスを ' / ' で区切った名前になる。"""
    docs = tmp_path / "docs"
    docs.mkdir()
    file_path = docs / "guide.md"
    file_path.write_text("# Guide", encoding="utf-8")
    assert make_doc_name(str(tmp_path), file_path) == "docs / guide"


# ── get_matching_files ───────────────────────────────────────

def test_get_matching_files_single_file(tmp_path):
    (tmp_path / "README.md").write_text("# Hello", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text("# Changes", encoding="utf-8")

    files = get_matching_files(str(tmp_path), ["README.md"])

    assert len(files) == 1
    assert files[0].name == "README.md"


def test_get_matching_files_glob_pattern(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "guide.md").write_text("# Guide", encoding="utf-8")
    (docs / "api.md").write_text("# API", encoding="utf-8")

    files = get_matching_files(str(tmp_path), ["docs/*.md"])

    assert len(files) == 2
    names = {f.name for f in files}
    assert names == {"guide.md", "api.md"}


def test_get_matching_files_deduplicates(tmp_path):
    (tmp_path / "README.md").write_text("# Hello", encoding="utf-8")

    files = get_matching_files(str(tmp_path), ["README.md", "*.md"])

    assert len(files) == 1


def test_get_matching_files_no_match(tmp_path):
    (tmp_path / "README.md").write_text("# Hello", encoding="utf-8")

    files = get_matching_files(str(tmp_path), ["docs/*.md"])

    assert files == []


# ── main() 統合テスト ─────────────────────────────────────────

@patch("sync.upload_or_update_file")
@patch("sync.markdown_to_html")
@patch("sync.get_repo_config")
def test_main_syncs_files(mock_config, mock_convert, mock_upload, tmp_path, monkeypatch):
    """正常系: get_repo_config → markdown_to_html → upload_or_update_file が連携する。"""
    monkeypatch.setenv("GITHUB_REPOSITORY", "org/project-a")
    monkeypatch.setenv("GOOGLE_CREDENTIALS", '{"type": "service_account"}')
    monkeypatch.setenv("SPREADSHEET_ID", "sheet-id")
    monkeypatch.setenv("GITHUB_WORKSPACE", str(tmp_path))

    (tmp_path / "README.md").write_text("# Hello", encoding="utf-8")

    mock_config.return_value = {
        "folder_id": "folder-123",
        "folder_name": "テストフォルダ",
        "file_patterns": ["README.md"],
        "enabled": True,
    }
    mock_convert.return_value = "<h1>Hello</h1>"
    mock_upload.return_value = "doc-id"

    main()

    mock_config.assert_called_once_with(
        "sheet-id", "https://github.com/org/project-a", '{"type": "service_account"}'
    )
    mock_convert.assert_called_once_with("# Hello")
    mock_upload.assert_called_once()


@patch("sync.get_repo_config")
def test_main_skips_when_repo_not_in_spreadsheet(mock_config, monkeypatch, capsys):
    """リポジトリがスプレッドシートにない場合は WARNING を出して正常終了する。"""
    monkeypatch.setenv("GITHUB_REPOSITORY", "org/unknown")
    monkeypatch.setenv("GOOGLE_CREDENTIALS", '{"type": "service_account"}')
    monkeypatch.setenv("SPREADSHEET_ID", "sheet-id")

    mock_config.return_value = None

    main()  # 例外を投げないこと

    captured = capsys.readouterr()
    assert "WARNING" in captured.out
```

- [ ] **Step 2: テストが失敗することを確認する**

Run: `pytest tests/test_sync.py -v`
Expected: `ModuleNotFoundError: No module named 'sync'` で FAIL

- [ ] **Step 3: `sync.py` を実装する**

```python
# sync.py
import os
import sys
from pathlib import Path
from typing import List

from converter import markdown_to_html
from drive import upload_or_update_file
from spreadsheet import get_repo_config


def require_env(name: str) -> str:
    """環境変数を取得する。未設定または空の場合は分かりやすい RuntimeError を出す。

    Args:
        name: 環境変数名

    Returns:
        環境変数の値

    Raises:
        RuntimeError: 環境変数が未設定または空の場合
    """
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Required environment variable is missing or empty: {name}"
        )
    return value


def get_repo_url() -> str:
    """環境変数 GITHUB_REPOSITORY から GitHub リポジトリの完全 URL を構築する。

    Returns:
        例: "https://github.com/org/my-repo"
    """
    repo = require_env("GITHUB_REPOSITORY")
    return f"https://github.com/{repo}"


def make_doc_name(workspace: str, file_path: Path) -> str:
    """ファイルの相対パスから Google Doc 名を生成する。

    ルート直下と異なるディレクトリに同名ファイルがあっても衝突しないよう、
    サブディレクトリ名をファイル名に含める。

    例:
        workspace/README.md          -> "README"
        workspace/docs/guide.md      -> "docs / guide"
        workspace/docs/api/ref.md    -> "docs / api / ref"

    Args:
        workspace: ワークスペースのルートディレクトリパス
        file_path: 対象ファイルの絶対パス

    Returns:
        Google Doc 名（拡張子なし、パス区切りを " / " に変換）
    """
    rel = file_path.resolve().relative_to(Path(workspace).resolve())
    return str(rel.with_suffix("")).replace("\\", " / ").replace("/", " / ")


def get_matching_files(workspace: str, patterns: List[str]) -> List[Path]:
    """ワークスペース内でグロブパターンに一致するファイルを重複なく返す。

    Args:
        workspace: 検索のベースディレクトリ（GitHub Actions では GITHUB_WORKSPACE）
        patterns: グロブパターンのリスト（例: ["README.md", "docs/*.md"]）

    Returns:
        一致したファイルの Path オブジェクトのリスト（重複なし）。
    """
    seen: dict = {}
    workspace_path = Path(workspace)
    for pattern in patterns:
        for path in workspace_path.glob(pattern):
            if path.is_file():
                key = str(path.resolve())
                if key not in seen:
                    seen[key] = path
    return list(seen.values())


def main() -> None:
    """同期処理のメインエントリポイント。"""
    credentials_json = require_env("GOOGLE_CREDENTIALS")
    spreadsheet_id = require_env("SPREADSHEET_ID")
    workspace = os.environ.get("GITHUB_WORKSPACE", os.getcwd())
    repo_url = get_repo_url()

    print(f"Syncing {repo_url} to Google Drive...")

    config = get_repo_config(spreadsheet_id, repo_url, credentials_json)
    if config is None:
        print(
            f"WARNING: Repository {repo_url} not found in spreadsheet or is disabled. "
            "Skipping."
        )
        return

    folder_id = config["folder_id"]
    folder_name = config["folder_name"]
    patterns = config["file_patterns"]

    files = get_matching_files(workspace, patterns)
    if not files:
        print(f"WARNING: No files matched patterns {patterns}. Skipping.")
        return

    success_count = 0
    for file_path in files:
        try:
            md_content = file_path.read_text(encoding="utf-8")
            html_content = markdown_to_html(md_content)
            doc_name = make_doc_name(workspace, file_path)
            upload_or_update_file(folder_id, doc_name, html_content, credentials_json)
            print(f"  ✓ {file_path.name} → '{doc_name}' (Google Doc)")
            success_count += 1
        except Exception as e:
            print(f"  ✗ Failed to sync {file_path.name}: {e}", file=sys.stderr)
            sys.exit(1)

    print(
        f"Done. {success_count} file(s) synced to Google Drive folder '{folder_name}'."
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: テストが全件パスすることを確認する**

Run: `pytest tests/test_sync.py -v`
Expected: 10 passed

- [ ] **Step 5: 全テストが通ることを確認する**

Run: `pytest tests/ -v`
Expected: 26 passed (converter:5 + spreadsheet:7 + drive:4 + sync:10)

- [ ] **Step 6: コミット**

```bash
git add tests/test_sync.py sync.py
git commit -m "feat: メイン同期スクリプトを実装（ファイル名衝突防止・統合テスト追加）"
```

---

## Task 6: GitHub Composite Action 定義の作成

**Files:**
- Create: `action.yml`
- Create: `workflow-template.yml`

> **修正点（Codex レビュー）**: `workflow_dispatch` と `permissions: contents: read` を追加

- [ ] **Step 1: `action.yml` を作成する**

```yaml
# action.yml
name: 'Sync docs to Google Drive'
description: 'mainブランチへのpushをトリガーに、MarkdownドキュメントをGoogle DriveにGoogle Docs形式で自動同期します'
author: 'ga-t-nishimura'

inputs:
  google_credentials:
    description: 'Google Service Account の JSON 鍵（GitHub Secrets から渡す: secrets.GOOGLE_CREDENTIALS）'
    required: true
  spreadsheet_id:
    description: 'リポジトリ↔フォルダ対応表の Google スプレッドシート ID（GitHub Secrets から渡す: secrets.GDRIVE_SPREADSHEET_ID）'
    required: true

runs:
  using: 'composite'
  steps:
    - name: Set up Python 3.11
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install dependencies
      shell: bash
      run: pip install -r "${{ github.action_path }}/requirements.txt"

    - name: Sync Markdown docs to Google Drive
      shell: bash
      run: python "${{ github.action_path }}/sync.py"
      env:
        GOOGLE_CREDENTIALS: ${{ inputs.google_credentials }}
        SPREADSHEET_ID: ${{ inputs.spreadsheet_id }}
```

- [ ] **Step 2: 対象リポジトリ用のワークフローテンプレートを作成する**

```yaml
# workflow-template.yml
# ─────────────────────────────────────────────────────────────
# このファイルを対象リポジトリの .github/workflows/sync-to-gdrive.yml
# としてコピーして使用してください。
# ─────────────────────────────────────────────────────────────
name: Sync docs to Google Drive

on:
  push:
    branches: [main]
  workflow_dispatch:  # 手動実行（初回確認・デバッグ用）

permissions:
  contents: read  # リポジトリのファイルを読むためだけに必要な最小権限

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

- [ ] **Step 3: コミット**

```bash
git add action.yml workflow-template.yml
git commit -m "feat: GitHub Composite Action定義とワークフローテンプレートを追加"
```

---

## Task 7: README.md の作成

**Files:**
- Create: `README.md`

> **修正点（Codex レビュー）**: Service Account の最小権限・鍵ローテーション・タグ運用の注記を追加

- [ ] **Step 1: `README.md` を作成する**

````markdown
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
````

- [ ] **Step 2: コミット**

```bash
git add README.md
git commit -m "docs: README.mdを追加（セットアップ手順・セキュリティ・費用説明）"
```

---

## 最終確認

- [ ] **全テストが通ることを確認する**

Run: `pytest tests/ -v`
Expected: 26 passed (converter:5 + spreadsheet:7 + drive:4 + sync:10), 0 failed

- [ ] **ファイル構成を確認する**

Run: `ls -la`
Expected: `action.yml`, `sync.py`, `spreadsheet.py`, `converter.py`, `drive.py`, `requirements.txt`, `workflow-template.yml`, `README.md`, `.gitignore`, `tests/` が存在する
