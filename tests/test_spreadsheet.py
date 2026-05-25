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
        ["GitHubリポジトリURL", "フォルダ名", "フォルダID", "ファイルパターン", "有効"],
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
        ["GitHubリポジトリURL", "フォルダ名", "フォルダID", "ファイルパターン", "有効"],
        ["https://github.com/org/project-a.git", "テスト", "folder-id", "README.md", "TRUE"],
    ]
    mock_build.return_value = _make_mock_service(values)

    config = get_repo_config("sheet-id", "https://github.com/org/project-a", "{}")
    assert config is not None


@patch("spreadsheet.build")
@patch("spreadsheet._get_credentials")
def test_matches_url_with_git_suffix_and_trailing_slash(mock_creds, mock_build):
    """.git と末尾スラッシュが両方ある URL でも一致する。"""
    values = [
        ["GitHubリポジトリURL", "フォルダ名", "フォルダID", "ファイルパターン", "有効"],
        ["https://github.com/org/project-a.git/", "テスト", "folder-id", "README.md", "TRUE"],
    ]
    mock_build.return_value = _make_mock_service(values)

    config = get_repo_config("sheet-id", "https://github.com/org/project-a", "{}")
    assert config is not None


@patch("spreadsheet.build")
@patch("spreadsheet._get_credentials")
def test_filters_empty_patterns_from_trailing_comma(mock_creds, mock_build):
    """末尾カンマなどで生じる空のパターンは除去される。"""
    values = [
        ["GitHubリポジトリURL", "フォルダ名", "フォルダID", "ファイルパターン", "有効"],
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
