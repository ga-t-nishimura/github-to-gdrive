import markdown as md_lib

# Google Drive が HTML→Google Docs に変換する際に適用される見出しスタイル。
# <style> タグ内の CSS で H1〜H6 のフォントサイズを明示することで、
# デフォルトのサイズ崩れを防ぐ。
_HEADING_CSS = (
    "h1{font-size:26pt;font-weight:bold;}"
    "h2{font-size:20pt;font-weight:bold;}"
    "h3{font-size:16pt;font-weight:bold;}"
    "h4{font-size:14pt;font-weight:bold;}"
    "h5{font-size:12pt;font-weight:bold;}"
    "h6{font-size:11pt;font-weight:bold;}"
)


def markdown_to_html(markdown_content: str) -> str:
    """Markdown テキストをフル HTML ドキュメントに変換する。

    Google Drive API が HTML→Google Docs に変換する際に見出しサイズを正しく
    解釈できるよう、<style> タグ付きのフル HTML 構造でラップして返す。

    Args:
        markdown_content: 変換元の Markdown テキスト

    Returns:
        変換後の HTML 文字列。入力が空の場合は空文字列を返す。
    """
    if not markdown_content:
        return ""
    body = md_lib.markdown(
        markdown_content,
        extensions=["tables", "fenced_code"],
    )
    return (
        f"<html><head><style>{_HEADING_CSS}</style></head>"
        f"<body>{body}</body></html>"
    )
