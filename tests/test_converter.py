from converter import markdown_to_html


def test_converts_h1_heading():
    result = markdown_to_html("# Hello World")
    # インラインスタイルが付与されるため、style 属性付きの h1 タグを確認
    assert 'style="font-size:26pt' in result
    assert "Hello World" in result


def test_converts_h2_heading():
    result = markdown_to_html("## Section")
    assert 'style="font-size:20pt' in result
    assert "Section" in result


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
    assert "font-size" in result


def test_heading_inline_styles_all_levels():
    """H1〜H6 すべてのレベルにインラインスタイルが付与されること。"""
    md = "# H1\n## H2\n### H3\n#### H4\n##### H5\n###### H6"
    result = markdown_to_html(md)
    assert 'style="font-size:26pt' in result  # h1
    assert 'style="font-size:20pt' in result  # h2
    assert 'style="font-size:16pt' in result  # h3
    assert 'style="font-size:14pt' in result  # h4
    assert 'style="font-size:12pt' in result  # h5
    assert 'style="font-size:11pt' in result  # h6


def test_heading_styles_do_not_affect_empty_check():
    """空文字列入力では空文字列を返し、HTML ラッパーを追加しないこと。"""
    assert markdown_to_html("") == ""


def test_bold_heading_has_inline_style():
    """# **bold heading** のようにMarkdown内で太字指定された見出しにもインラインスタイルが付与されること。"""
    result = markdown_to_html("# **cuticomi-app**")
    # <h1 style="..."> が付与されているか確認
    assert '<h1 style="font-size:26pt;font-weight:bold;">' in result
    assert "<strong>cuticomi-app</strong>" in result
