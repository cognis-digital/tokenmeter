"""Smoke tests for TOKENMETER."""
import contextlib
import io
import pytest

from tokenmeter.core import TOOL_NAME, TOOL_VERSION, add_model, count_tokens, estimate
from tokenmeter import cli


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
    assert callable(cli.main)


# ---------------------------------------------------------------------------
# Hardening: edge cases and invalid inputs
# ---------------------------------------------------------------------------

def _run_cli(argv):
    """Run CLI and capture stdout; return (exit_code, stdout_text)."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = cli.main(argv)
    return code, out.getvalue()


def test_count_tokens_none_safe():
    # count_tokens must not crash on None; treat as empty string.
    assert count_tokens(None) == 0  # type: ignore[arg-type]


def test_count_tokens_empty():
    assert count_tokens("") == 0


def test_add_model_negative_price_raises():
    with pytest.raises(ValueError, match="input_per_1k"):
        add_model("bad-price", -0.001, 0.002, 4096)


def test_add_model_zero_context_raises():
    with pytest.raises(ValueError, match="context_window"):
        add_model("bad-ctx", 0.001, 0.002, 0)


def test_add_model_empty_name_raises():
    with pytest.raises(ValueError, match="name"):
        add_model("", 0.001, 0.002, 4096)


def test_estimate_negative_output_tokens_raises():
    with pytest.raises(ValueError, match="output_tokens"):
        estimate("hello", model="claude-sonnet", output_tokens=-1)


def test_estimate_negative_input_tokens_raises():
    with pytest.raises(ValueError, match="input_tokens"):
        estimate("", model="claude-sonnet", input_tokens=-5)


def test_cli_missing_file_returns_exit_2(tmp_path):
    # Pointing --file at a nonexistent path should exit 2 (not traceback).
    missing = str(tmp_path / "does_not_exist.txt")
    with pytest.raises(SystemExit) as exc_info:
        _run_cli(["count", "-f", missing])
    assert exc_info.value.code == 2


def test_cli_negative_output_tokens_returns_exit_2():
    code, _ = _run_cli(["count", "-t", "hello", "-o", "-5"])
    assert code == 2


def test_cli_budget_negative_max_cost_returns_exit_2():
    code, _ = _run_cli(["budget", "-t", "hello", "--max-cost", "-1.0"])
    assert code == 2


def test_cli_budget_negative_max_tokens_returns_exit_2():
    code, _ = _run_cli(["budget", "-t", "hello", "--max-tokens", "-10"])
    assert code == 2


def test_cli_unknown_model_returns_exit_2():
    code, _ = _run_cli(["count", "-t", "hello", "-m", "not-a-real-model"])
    assert code == 2


def test_mcp_server_importable():
    # mcp_server must import cleanly (the broken scan/to_json import is fixed).
    from tokenmeter import mcp_server  # noqa: F401
    assert callable(mcp_server.serve)
