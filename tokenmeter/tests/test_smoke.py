"""Smoke tests for TOKENMETER. No network, stdlib + package only."""

import json
import os
import sys
import unittest

# Make the package importable when run directly from anywhere.
_HERE = os.path.dirname(os.path.abspath(__file__))
_BUILD_OUT = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _BUILD_OUT not in sys.path:
    sys.path.insert(0, _BUILD_OUT)

import io
import contextlib

from tokenmeter import (
    TOOL_NAME,
    TOOL_VERSION,
    count_tokens,
    estimate,
    get_pricing,
    list_models,
)
from tokenmeter.core import add_model, aggregate, check_budget, compare_models
from tokenmeter import cli


class TestTokenizer(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(count_tokens(""), 0)

    def test_monotonic(self):
        a = count_tokens("hello")
        b = count_tokens("hello world this is longer")
        self.assertGreater(b, a)

    def test_long_word_subwords(self):
        # A 20-char alpha run should be > 1 token (subword splitting).
        self.assertGreater(count_tokens("a" * 20), 1)

    def test_punctuation_counts(self):
        self.assertGreaterEqual(count_tokens("a, b. c!"), 5)

    def test_newlines_count(self):
        self.assertGreater(count_tokens("a\n\nb"), count_tokens("a b"))

    def test_roughly_word_ratio(self):
        # ~ tokens should be within 0.5x..2x of word count for prose.
        text = " ".join(["word"] * 100)
        toks = count_tokens(text)
        self.assertTrue(50 <= toks <= 200, toks)


class TestPricing(unittest.TestCase):
    def test_known_model(self):
        p = get_pricing("claude-sonnet")
        self.assertGreater(p.input_per_1k, 0)
        self.assertGreater(p.context_window, 0)

    def test_unknown_model_raises(self):
        with self.assertRaises(KeyError):
            get_pricing("does-not-exist")

    def test_add_model(self):
        add_model("test-model", 0.001, 0.002, 4096)
        p = get_pricing("test-model")
        self.assertEqual(p.context_window, 4096)


class TestEstimate(unittest.TestCase):
    def test_cost_scales_with_output(self):
        e1 = estimate("hello world", model="gpt-4o", output_tokens=0)
        e2 = estimate("hello world", model="gpt-4o", output_tokens=1000)
        self.assertGreater(e2.total_cost, e1.total_cost)
        self.assertEqual(e1.input_tokens, e2.input_tokens)

    def test_explicit_input_tokens(self):
        e = estimate(model="gpt-4o", input_tokens=1000, output_tokens=0)
        # gpt-4o input is 0.0025/1k -> 1000 tokens == $0.0025
        self.assertAlmostEqual(e.input_cost, 0.0025, places=6)

    def test_to_dict_shape(self):
        d = estimate("hi", model="claude-haiku").to_dict()
        for key in ("model", "input_tokens", "total_cost_usd", "context_used_pct"):
            self.assertIn(key, d)


class TestBudget(unittest.TestCase):
    def test_pass(self):
        e = estimate("short text", model="gpt-4o-mini", output_tokens=10)
        r = check_budget(e, max_cost_usd=1.0, max_tokens=1_000_000)
        self.assertTrue(r.ok)
        self.assertEqual(r.violations, [])

    def test_cost_fail(self):
        e = estimate(model="claude-opus", input_tokens=100000, output_tokens=10000)
        r = check_budget(e, max_cost_usd=0.01)
        self.assertFalse(r.ok)
        self.assertTrue(any("cost" in v for v in r.violations))

    def test_context_window_fail(self):
        e = estimate(model="gpt-4o", input_tokens=200000, output_tokens=0)
        r = check_budget(e)
        self.assertFalse(r.ok)

    def test_aggregate(self):
        ests = [estimate("a b c", model="gpt-4o") for _ in range(3)]
        roll = aggregate(ests)
        self.assertEqual(roll["files"], 3)
        self.assertEqual(roll["total_tokens"], 3 * ests[0].input_tokens)


class TestCompare(unittest.TestCase):
    def test_ranked_cheapest_first(self):
        ests = compare_models("hello world this is a prompt", output_tokens=500)
        costs = [e.total_cost for e in ests]
        self.assertEqual(costs, sorted(costs))
        # every known model is represented
        self.assertEqual(len(ests), len(list_models()))

    def test_same_input_tokens_across_models(self):
        ests = compare_models("the quick brown fox", output_tokens=0)
        self.assertEqual(len({e.input_tokens for e in ests}), 1)

    def test_subset(self):
        ests = compare_models(
            "x y z", output_tokens=10, models=["claude-opus", "gpt-4o-mini"]
        )
        names = {e.model for e in ests}
        self.assertEqual(names, {"claude-opus", "gpt-4o-mini"})
        # cheapest first => gpt-4o-mini before claude-opus
        self.assertEqual(ests[0].model, "gpt-4o-mini")

    def test_unknown_model_raises(self):
        with self.assertRaises(KeyError):
            compare_models("x", models=["totally-fake"])


class TestCLI(unittest.TestCase):
    def _run(self, argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cli.main(argv)
        return code, out.getvalue()

    def test_version_constants(self):
        self.assertEqual(TOOL_NAME, "tokenmeter")
        self.assertTrue(TOOL_VERSION)

    def test_count_json(self):
        code, out = self._run(
            ["--format", "json", "count", "-t", "hello world", "-m", "gpt-4o"]
        )
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["model"], "gpt-4o")
        self.assertGreater(data["input_tokens"], 0)

    def test_format_after_subcommand(self):
        code, out = self._run(["count", "-t", "hi", "--format", "json"])
        self.assertEqual(code, 0)
        json.loads(out)  # must be valid JSON

    def test_budget_exit_codes(self):
        ok, _ = self._run(
            ["budget", "-t", "hello", "-m", "gpt-4o-mini", "--max-cost", "1.0"]
        )
        self.assertEqual(ok, 0)
        bad, _ = self._run(["budget", "-t", "a b c d e", "--max-tokens", "1"])
        self.assertEqual(bad, 1)

    def test_models_json(self):
        code, out = self._run(["--format", "json", "models"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertTrue(any(m["name"] == "claude-sonnet" for m in data["models"]))

    def test_unknown_model_exit_2(self):
        code, _ = self._run(["count", "-t", "x", "-m", "nope"])
        self.assertEqual(code, 2)

    def test_compare_json_ranked(self):
        code, out = self._run(
            ["compare", "-t", "hello world", "-o", "100", "--format", "json"]
        )
        self.assertEqual(code, 0)
        data = json.loads(out)
        ranking = data["ranking"]
        costs = [r["total_cost_usd"] for r in ranking]
        self.assertEqual(costs, sorted(costs))

    def test_compare_subset_csv(self):
        code, out = self._run(
            [
                "compare",
                "-t",
                "hi there",
                "-o",
                "50",
                "--models",
                "claude-opus,gpt-4o-mini",
                "--format",
                "csv",
            ]
        )
        self.assertEqual(code, 0)
        lines = [ln for ln in out.strip().splitlines() if ln]
        self.assertEqual(lines[0], "model,in_tok,out_tok,total_cost_usd,ctx_used_%")
        self.assertEqual(len(lines), 3)  # header + 2 models

    def test_compare_unknown_model_exit_2(self):
        code, _ = self._run(["compare", "-t", "x", "--models", "nope"])
        self.assertEqual(code, 2)

    def test_models_csv(self):
        code, out = self._run(["models", "--format", "csv"])
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("model,in/1k,out/1k,context"))

    def test_count_csv(self):
        code, out = self._run(["count", "-t", "hello world", "--format", "csv"])
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("metric,value"))
        self.assertIn("input_tokens", out)


if __name__ == "__main__":
    unittest.main()
