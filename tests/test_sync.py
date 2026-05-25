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
