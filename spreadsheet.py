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
