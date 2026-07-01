"""CLI edge cases, exit codes, formats, stdin and error paths for tokenmeter.cli.

Drives ``cli.main(argv)`` directly (no subprocess) and asserts on exit codes and
emitted text. Covers all subcommands (count / budget / models / batch / compare),
all three output formats (table / json / csv), stdin piping, malformed input, and
the documented non-zero exit codes (1 = over budget, 2 = usage/bad input).

Stdlib + package only. No network.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile

import pytest

from tokenmeter import cli


def run(argv, stdin_text=None):
    """Invoke the CLI, capturing stdout/stderr and any SystemExit code."""
    out, err = io.StringIO(), io.StringIO()
    old_stdin = sys.stdin
    if stdin_text is not None:
        sys.stdin = io.StringIO(stdin_text)
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = cli.main(argv)
            except SystemExit as e:  # argparse errors raise SystemExit
                code = e.code if isinstance(e.code, int) else 2
    finally:
        sys.stdin = old_stdin
    return code, out.getvalue(), err.getvalue()


@pytest.fixture
def tmpfile():
    created = []

    def _make(content):
        fd, path = tempfile.mkstemp(suffix=".txt")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        created.append(path)
        return path

    yield _make
    for p in created:
        try:
            os.remove(p)
        except OSError:
            pass


# --------------------------------------------------------------------------- #
# count                                                                        #
# --------------------------------------------------------------------------- #
class TestCount:
    def test_count_table_default(self):
        code, out, _ = run(["count", "-t", "hello world"])
        assert code == 0
        assert "input_tokens" in out and "total_cost_usd" in out

    def test_count_json(self):
        code, out, _ = run(["--format", "json", "count", "-t", "hello", "-m", "gpt-4o"])
        assert code == 0
        d = json.loads(out)
        assert d["model"] == "gpt-4o" and d["input_tokens"] > 0

    def test_count_csv(self):
        code, out, _ = run(["count", "-t", "hi", "--format", "csv"])
        assert code == 0
        assert out.startswith("metric,value")

    def test_count_from_file(self, tmpfile):
        p = tmpfile("some prompt text here")
        code, out, _ = run(["--format", "json", "count", "-f", p])
        assert code == 0
        assert json.loads(out)["input_tokens"] > 0

    def test_count_from_stdin(self):
        code, out, _ = run(["--format", "json", "count"], stdin_text="piped prompt text")
        assert code == 0
        assert json.loads(out)["input_tokens"] > 0

    def test_count_empty_stdin_is_zero(self):
        code, out, _ = run(["--format", "json", "count"], stdin_text="")
        assert code == 0
        assert json.loads(out)["input_tokens"] == 0

    def test_count_unknown_model_exit_2(self):
        code, _, err = run(["count", "-t", "x", "-m", "nope"])
        assert code == 2
        assert "error" in err.lower()

    def test_count_negative_output_tokens_exit_2(self):
        code, _, err = run(["count", "-t", "x", "-o", "-5"])
        assert code == 2
        assert "output_tokens" in err

    def test_count_missing_file_exit_2(self):
        code, _, err = run(["count", "-f", os.path.join(tempfile.gettempdir(), "no_such_tm.txt")])
        assert code == 2
        assert "error" in err.lower()

    def test_text_and_file_mutually_exclusive(self, tmpfile):
        p = tmpfile("x")
        code, _, _ = run(["count", "-t", "hi", "-f", p])
        assert code == 2  # argparse mutually-exclusive error


# --------------------------------------------------------------------------- #
# budget                                                                       #
# --------------------------------------------------------------------------- #
class TestBudget:
    def test_pass_exit_0(self):
        code, out, _ = run(["budget", "-t", "hi", "-m", "gpt-4o-mini", "--max-cost", "1.0"])
        assert code == 0
        assert "OK" in out

    def test_over_cost_exit_1(self):
        code, out, _ = run(
            ["budget", "-m", "claude-opus", "-t", "x", "-o", "1", "--max-cost", "0.0"]
        )
        assert code == 1
        assert "OVER BUDGET" in out

    def test_over_tokens_exit_1(self):
        code, out, _ = run(["budget", "-t", "a b c d e f g", "--max-tokens", "1"])
        assert code == 1

    def test_json_output(self):
        code, out, _ = run(["--format", "json", "budget", "-t", "hi", "--max-cost", "1.0"])
        assert code == 0
        d = json.loads(out)
        assert d["ok"] is True and "estimate" in d

    def test_context_overflow_exit_1(self):
        # 8k window model, force > window via explicit big text is hard; use a
        # large file instead.
        big = " ".join(["word"] * 10000)
        code, out, _ = run(["budget", "-t", big, "-m", "generic-1k"])
        assert code == 1
        assert "context window" in out

    def test_unknown_model_exit_2(self):
        code, _, err = run(["budget", "-t", "x", "-m", "ghost", "--max-cost", "1"])
        assert code == 2


# --------------------------------------------------------------------------- #
# models                                                                       #
# --------------------------------------------------------------------------- #
class TestModels:
    def test_table(self):
        code, out, _ = run(["models"])
        assert code == 0
        assert "claude-sonnet" in out

    def test_json(self):
        code, out, _ = run(["--format", "json", "models"])
        assert code == 0
        d = json.loads(out)
        assert any(m["name"] == "claude-opus" for m in d["models"])

    def test_csv_header(self):
        code, out, _ = run(["models", "--format", "csv"])
        assert code == 0
        assert out.startswith("model,in/1k,out/1k,context")


# --------------------------------------------------------------------------- #
# batch                                                                        #
# --------------------------------------------------------------------------- #
class TestBatch:
    def test_two_files_rollup(self, tmpfile):
        a, b = tmpfile("hello world"), tmpfile("another prompt here")
        code, out, _ = run(["--format", "json", "batch", a, b])
        assert code == 0
        d = json.loads(out)
        assert d["rollup"]["files"] == 2
        assert len(d["files"]) == 2

    def test_batch_table_has_total(self, tmpfile):
        a = tmpfile("hi")
        code, out, _ = run(["batch", a])
        assert code == 0
        assert "TOTAL" in out

    def test_batch_max_cost_exceeded_exit_1(self, tmpfile):
        a = tmpfile(" ".join(["word"] * 500))
        code, _, err = run(["batch", a, "--max-cost", "0.0", "-m", "claude-opus"])
        assert code == 1
        assert "exceeds" in err

    def test_batch_missing_file_exit_2(self):
        missing = os.path.join(tempfile.gettempdir(), "definitely_missing_tm.txt")
        code, _, err = run(["batch", missing])
        assert code == 2
        assert "cannot read" in err

    def test_batch_requires_at_least_one_file(self):
        code, _, _ = run(["batch"])
        assert code == 2  # argparse: nargs="+" requires one


# --------------------------------------------------------------------------- #
# compare                                                                      #
# --------------------------------------------------------------------------- #
class TestCompare:
    def test_json_ranked(self):
        code, out, _ = run(["compare", "-t", "hello world", "-o", "100", "--format", "json"])
        assert code == 0
        costs = [r["total_cost_usd"] for r in json.loads(out)["ranking"]]
        assert costs == sorted(costs)

    def test_subset_csv(self):
        code, out, _ = run(
            ["compare", "-t", "hi", "-o", "50", "--models",
             "claude-opus,gpt-4o-mini", "--format", "csv"]
        )
        assert code == 0
        lines = [l for l in out.strip().splitlines() if l]
        assert lines[0].startswith("model,in_tok")
        assert len(lines) == 3  # header + 2

    def test_unknown_model_exit_2(self):
        code, _, err = run(["compare", "-t", "x", "--models", "nope"])
        assert code == 2

    def test_from_stdin(self):
        code, out, _ = run(["compare", "--format", "json"], stdin_text="piped text here")
        assert code == 0
        assert json.loads(out)["ranking"]

    def test_table_output(self):
        code, out, _ = run(["compare", "-t", "hello", "-o", "10"])
        assert code == 0
        assert "claude-opus" in out and "gpt-4o-mini" in out


# --------------------------------------------------------------------------- #
# global / parser                                                              #
# --------------------------------------------------------------------------- #
class TestParser:
    def test_no_command_errors(self):
        code, _, _ = run([])
        assert code == 2  # subparser required

    def test_version(self):
        code, out, _ = run(["--version"])
        assert code == 0
        assert "tokenmeter" in out

    def test_help_exits_zero(self):
        code, _, _ = run(["--help"])
        assert code == 0

    def test_format_before_and_after_subcommand(self):
        # sub-level --format wins over top-level
        code, out, _ = run(["--format", "csv", "count", "-t", "hi", "--format", "json"])
        assert code == 0
        json.loads(out)  # must be JSON, not CSV

    def test_bad_format_choice_exit_2(self):
        code, _, _ = run(["count", "-t", "hi", "--format", "xml"])
        assert code == 2
