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
