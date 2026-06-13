"""Smoke tests for TOKENMETER."""
from tokenmeter.core import TOOL_NAME, TOOL_VERSION, count_tokens, estimate, check_budget


def test_identity():
    assert TOOL_NAME and TOOL_VERSION


def test_count_tokens_basic(tmp_path):
    # Write a file with known text and confirm token counting works on the text.
    f = tmp_path / "x.txt"
    f.write_text("hello world this is a test\n")
    text = f.read_text()
    result = count_tokens(text)
    assert result >= 1
    assert isinstance(result, int)


def test_cli_importable():
    from tokenmeter.cli import main
    assert callable(main)
