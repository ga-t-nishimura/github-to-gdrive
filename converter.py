import re

from markdown_it import MarkdownIt

# CommonMark 準拠パーサー + GitHub Flavored Markdown の table 拡張を有効化。
# Python の標準 markdown ライブラリは blockquote 内の fenced code block を
# 正しくパースできず、`> # コメント` 行が見出しタグに化けるバグがあるため、
# CommonMark 準拠の markdown-it-py に切り替えた。
_md = MarkdownIt("commonmark").enable("table")

# 各見出しレベルのフォントサイズ定義（Google Docs での表示基準）
_HEADING_SIZES: dict[str, str] = {
    "1": "26pt",
    "2": "20pt",
    "3": "16pt",
    "4": "14pt",
    "5": "12pt",
    "6": "11pt",
}

# <style> タグ用 CSS（一部の Google Docs 環境向けフォールバック）
_HEADING_CSS = "".join(
    f"h{n}{{font-size:{size};font-weight:bold;}}"
    for n, size in _HEADING_SIZES.items()
)


def _add_inline_heading_styles(html: str) -> str:
    """<h1>〜<h6> タグにインラインスタイルを付与する。

    Google Docs の HTML import は <style> タグを部分的にしか解釈しない場合があるため、
    インラインスタイルを各タグへ直接付与して確実に適用されるようにする。

    Args:
        html: 変換後の HTML 文字列

    Returns:
        各見出しタグにインラインスタイルが付与された HTML 文字列
    """
    def replace(m: re.Match) -> str:
        level = m.group(1)
        size = _HEADING_SIZES.get(level, "")
        return f'<h{level} style="font-size:{size};font-weight:bold;">'

    return re.sub(r"<h([1-6])>", replace, html)


def markdown_to_html(markdown_content: str) -> str:
    """Markdown テキストをフル HTML ドキュメントに変換する。

    CommonMark 準拠のパーサーを使用することで、blockquote 内の
    fenced code block も正しく変換される（bash コメント行が見出しに
    化けるバグを防ぐ）。

    Google Drive API が HTML→Google Docs に変換する際に見出しサイズを正しく
    解釈できるよう、以下の両方を適用する:
    1. <style> タグで H1〜H6 のフォントサイズを CSS 定義（フォールバック）
    2. 各見出しタグへインラインスタイルを付与（より確実に適用される）

    Args:
        markdown_content: 変換元の Markdown テキスト

    Returns:
        変換後の HTML 文字列。入力が空の場合は空文字列を返す。
    """
    if not markdown_content:
        return ""
    body = _md.render(markdown_content)
    body_with_styles = _add_inline_heading_styles(body)
    return (
        f"<html><head><style>{_HEADING_CSS}</style></head>"
        f"<body>{body_with_styles}</body></html>"
    )
