from unittest.mock import MagicMock, patch
from drive import upload_or_update_file, _escape_drive_query_value


def _make_mock_service(existing_files=None):
    """Google Drive API サービスのモックを生成するヘルパー。

    nextPageToken なし（単一ページ）のレスポンスを返す。
    """
    mock_service = MagicMock()
    files_list = existing_files if existing_files is not None else []
    (
        mock_service.files.return_value
        .list.return_value
        .execute.return_value
    ) = {"files": files_list}  # nextPageToken なし → ループが1回で終了
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


def test_escape_drive_query_value_backslash():
    """バックスラッシュは先にエスケープされる。"""
    assert _escape_drive_query_value("a\\b") == "a\\\\b"


def test_escape_drive_query_value_backslash_before_quote():
    """バックスラッシュはシングルクォートより先にエスケープされる（二重エスケープ防止）。"""
    assert _escape_drive_query_value("a\\'b") == "a\\\\\\'b"
