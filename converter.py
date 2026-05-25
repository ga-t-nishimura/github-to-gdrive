import re
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
    html = md_lib.markdown(
        markdown_content,
        extensions=["tables", "fenced_code"],
    )
    # Normalize code tags by removing language class attributes
    html = re.sub(r'<code[^>]*>', '<code>', html)
    return html
