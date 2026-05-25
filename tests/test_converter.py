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
    assert "<code>" in result


def test_empty_input_returns_empty_string():
    result = markdown_to_html("")
    assert result == ""
