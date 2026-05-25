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
    # Convert path separators (both / and \) to " / "
    path_str = str(rel.with_suffix("")).replace("\\", "/")
    return path_str.replace("/", " / ")


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
