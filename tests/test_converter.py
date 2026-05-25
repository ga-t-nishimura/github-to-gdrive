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
    assert "<code" in result


def test_empty_input_returns_empty_string():
    result = markdown_to_html("")
    assert result == ""


def test_html_wraps_with_heading_styles():
    """変換結果がフル HTML ドキュメント構造でラップされ、見出しスタイルを含むこと。"""
    result = markdown_to_html("# Title\n## Section")
    assert "<html>" in result
    assert "<style>" in result
    assert "h1" in result
    assert "h2" in result
    assert "font-size" in result


def test_heading_styles_do_not_affect_empty_check():
    """空文字列入力では空文字列を返し、HTML ラッパーを追加しないこと。"""
    assert markdown_to_html("") == ""
