"""Edge-case and error-path coverage for tokenmeter.core.

Complements the happy-path smoke suite: these probe the boundaries of the
estimator, the pricing table, budget gates, model comparison, and aggregation
— including the malformed / adversarial inputs that a budgeting tool has to
reject cleanly rather than silently produce a wrong (e.g. negative) number.

Stdlib + package only. No network.
"""
from __future__ import annotations

import math

import pytest

from tokenmeter.core import (
    MODELS,
    ModelPricing,
    add_model,
    aggregate,
    check_budget,
    compare_models,
    count_tokens,
    estimate,
    get_pricing,
    list_models,
)


# --------------------------------------------------------------------------- #
# count_tokens                                                                 #
# --------------------------------------------------------------------------- #
class TestCountTokens:
    def test_empty_is_zero(self):
        assert count_tokens("") == 0

    def test_none_is_zero(self):
        # None is tolerated (behaves like empty) — the CLI can hand us None.
        assert count_tokens(None) == 0

    def test_non_string_raises_type_error(self):
        with pytest.raises(TypeError):
            count_tokens(12345)

    def test_pure_whitespace_no_newline_is_zero(self):
        # Spaces/tabs merge into adjacent words; alone they cost nothing.
        assert count_tokens("     ") == 0
        assert count_tokens("\t\t") == 0

    def test_single_newline_counts_one(self):
        assert count_tokens("\n") == 1

    def test_multiple_newlines_count_each(self):
        assert count_tokens("\n\n\n") == 3

    def test_windows_newlines_count(self):
        # \r\n contains one \n each -> two newline tokens for two lines.
        assert count_tokens("a\r\nb\r\nc") >= 2

    def test_single_char_word_is_one_token(self):
        assert count_tokens("a") == 1

    def test_four_char_word_is_one_token(self):
        assert count_tokens("abcd") == 1

    def test_five_char_word_is_two_tokens(self):
        # ceil(5/4) == 2
        assert count_tokens("abcde") == 2

    def test_long_word_ceildiv(self):
        assert count_tokens("a" * 16) == 4  # ceil(16/4)
        assert count_tokens("a" * 17) == 5  # ceil(17/4)

    def test_digits_grouped_by_three(self):
        assert count_tokens("1") == 1
        assert count_tokens("123") == 1
        assert count_tokens("1234") == 2  # ceil(4/3)
        assert count_tokens("123456") == 2

    def test_each_symbol_is_a_token(self):
        assert count_tokens("!@#") == 3

    def test_punctuation_spacing(self):
        # "a, b. c!" -> a , b . c ! => at least 5 tokens (words + punctuation)
        assert count_tokens("a, b. c!") >= 5

    def test_monotonic_with_length(self):
        short = count_tokens("hello")
        long = count_tokens("hello world this is a longer sentence")
        assert long > short

    def test_unicode_letters_and_emoji(self):
        # Should not crash on non-ASCII; produces a positive count.
        assert count_tokens("café résumé 北京 🚀") > 0

    def test_prose_ratio_is_reasonable(self):
        text = " ".join(["word"] * 200)
        toks = count_tokens(text)
        assert 100 <= toks <= 400

    def test_mixed_alnum_symbols_split(self):
        # A code-ish token: identifiers, digits and symbols split on boundaries.
        n = count_tokens("foo_bar123 = baz(42);")
        assert n > 5


# --------------------------------------------------------------------------- #
# pricing table                                                                #
# --------------------------------------------------------------------------- #
class TestPricing:
    def test_all_known_models_have_positive_context(self):
        for m in list_models():
            assert m.context_window > 0
            assert m.input_per_1k >= 0
            assert m.output_per_1k >= 0

    def test_list_models_sorted(self):
        names = [m.name for m in list_models()]
        assert names == sorted(names)

    def test_get_unknown_raises_keyerror_with_hint(self):
        with pytest.raises(KeyError) as ei:
            get_pricing("nope-not-real")
        # the message should list the known models to help the user
        assert "known" in str(ei.value)

    def test_pricing_cost_math(self):
        p = ModelPricing("x", 0.01, 0.02, 1000)
        # 2000 in, 1000 out => 0.02 + 0.02 = 0.04
        assert math.isclose(p.cost(2000, 1000), 0.04, rel_tol=1e-9)

    def test_pricing_zero_tokens_is_zero(self):
        p = get_pricing("claude-opus")
        assert p.cost(0, 0) == 0.0


class TestAddModel:
    def test_add_and_override(self):
        add_model("edge-tmp", 0.001, 0.002, 4096)
        assert get_pricing("edge-tmp").context_window == 4096
        add_model("edge-tmp", 0.005, 0.006, 8192)
        assert get_pricing("edge-tmp").input_per_1k == 0.005

    def test_blank_name_rejected(self):
        with pytest.raises(ValueError):
            add_model("", 0.001, 0.002, 4096)
        with pytest.raises(ValueError):
            add_model("   ", 0.001, 0.002, 4096)

    def test_non_numeric_price_rejected(self):
        with pytest.raises(ValueError):
            add_model("bad", "abc", 0.002, 4096)

    def test_negative_price_rejected(self):
        with pytest.raises(ValueError):
            add_model("neg", -0.001, 0.002, 4096)
        with pytest.raises(ValueError):
            add_model("neg", 0.001, -0.002, 4096)

    def test_nonpositive_context_rejected(self):
        with pytest.raises(ValueError):
            add_model("zero-ctx", 0.001, 0.002, 0)
        with pytest.raises(ValueError):
            add_model("neg-ctx", 0.001, 0.002, -100)

    def test_zero_price_allowed(self):
        p = add_model("free", 0.0, 0.0, 1024)
        assert p.input_per_1k == 0.0


# --------------------------------------------------------------------------- #
# estimate                                                                     #
# --------------------------------------------------------------------------- #
class TestEstimate:
    def test_explicit_input_tokens_override_text(self):
        e = estimate("this text is ignored", model="gpt-4o", input_tokens=1000)
        assert e.input_tokens == 1000

    def test_negative_input_tokens_rejected(self):
        with pytest.raises(ValueError):
            estimate(model="gpt-4o", input_tokens=-1)

    def test_negative_output_tokens_rejected(self):
        with pytest.raises(ValueError):
            estimate("hi", model="gpt-4o", output_tokens=-5)

    def test_zero_tokens_zero_cost(self):
        e = estimate("", model="claude-opus", output_tokens=0)
        assert e.total_cost == 0.0
        assert e.input_tokens == 0

    def test_unknown_model_raises(self):
        with pytest.raises(KeyError):
            estimate("hi", model="ghost-model")

    def test_context_pct_computed(self):
        e = estimate(model="generic-1k", input_tokens=4096, output_tokens=0)
        # 4096 / 8192 == 50%
        assert math.isclose(e.context_used_pct, 50.0, rel_tol=1e-6)

    def test_context_pct_over_100_when_overflowing(self):
        e = estimate(model="generic-1k", input_tokens=16384, output_tokens=0)
        assert e.context_used_pct > 100

    def test_to_dict_keys_and_rounding(self):
        d = estimate(model="claude-opus", input_tokens=1000, output_tokens=1000).to_dict()
        for k in (
            "model", "input_tokens", "output_tokens", "total_tokens",
            "input_cost_usd", "output_cost_usd", "total_cost_usd",
            "context_window", "context_used_pct",
        ):
            assert k in d
        assert d["total_tokens"] == 2000
        # opus: 0.015 in + 0.075 out per 1k => 0.015 + 0.075 = 0.09
        assert math.isclose(d["total_cost_usd"], 0.09, rel_tol=1e-6)

    def test_input_cost_matches_pricing(self):
        e = estimate(model="gpt-4o", input_tokens=1000, output_tokens=0)
        assert math.isclose(e.input_cost, 0.0025, rel_tol=1e-9)

    def test_output_cost_scales(self):
        lo = estimate("x", model="gpt-4o", output_tokens=100)
        hi = estimate("x", model="gpt-4o", output_tokens=1000)
        assert hi.output_cost > lo.output_cost
        assert lo.input_tokens == hi.input_tokens

    def test_float_tokens_coerced_to_int(self):
        e = estimate(model="gpt-4o", input_tokens=100, output_tokens=0)
        assert isinstance(e.input_tokens, int)


# --------------------------------------------------------------------------- #
# check_budget                                                                 #
# --------------------------------------------------------------------------- #
class TestCheckBudget:
    def test_pass_within_all_limits(self):
        e = estimate("short", model="gpt-4o-mini", output_tokens=10)
        r = check_budget(e, max_cost_usd=1.0, max_tokens=1_000_000)
        assert r.ok and r.violations == []

    def test_no_limits_passes_when_in_window(self):
        e = estimate("short", model="gpt-4o-mini")
        r = check_budget(e)
        assert r.ok

    def test_cost_violation(self):
        e = estimate(model="claude-opus", input_tokens=100_000, output_tokens=10_000)
        r = check_budget(e, max_cost_usd=0.01)
        assert not r.ok
        assert any("cost" in v for v in r.violations)

    def test_token_violation(self):
        e = estimate(model="gpt-4o", input_tokens=5000, output_tokens=0)
        r = check_budget(e, max_tokens=1000)
        assert not r.ok
        assert any("tokens" in v and "budget" in v for v in r.violations)

    def test_context_window_violation_without_ceilings(self):
        e = estimate(model="gpt-4o", input_tokens=200_000, output_tokens=0)
        r = check_budget(e)
        assert not r.ok
        assert any("context window" in v for v in r.violations)

    def test_multiple_violations_reported(self):
        e = estimate(model="generic-1k", input_tokens=100_000, output_tokens=0)
        r = check_budget(e, max_cost_usd=0.0, max_tokens=1)
        # cost + token + context window all trip
        assert len(r.violations) == 3

    def test_boundary_exactly_at_limit_passes(self):
        # tokens exactly equal to max_tokens is NOT a violation (strictly >)
        e = estimate(model="gpt-4o", input_tokens=100, output_tokens=0)
        r = check_budget(e, max_tokens=100)
        assert r.ok

    def test_to_dict_shape(self):
        e = estimate("hi", model="gpt-4o")
        d = check_budget(e, max_cost_usd=1.0).to_dict()
        assert set(d) >= {"ok", "max_cost_usd", "max_tokens", "violations", "estimate"}
        assert isinstance(d["estimate"], dict)


# --------------------------------------------------------------------------- #
# compare_models                                                               #
# --------------------------------------------------------------------------- #
class TestCompareModels:
    def test_ranked_cheapest_first(self):
        ests = compare_models("hello world prompt", output_tokens=500)
        costs = [e.total_cost for e in ests]
        assert costs == sorted(costs)

    def test_covers_all_models_by_default(self):
        ests = compare_models("x", output_tokens=0)
        assert len(ests) == len(MODELS)

    def test_same_input_tokens_across_all(self):
        ests = compare_models("the quick brown fox jumps", output_tokens=0)
        assert len({e.input_tokens for e in ests}) == 1

    def test_subset_only(self):
        ests = compare_models("x y", output_tokens=10, models=["claude-opus", "gpt-4o-mini"])
        assert {e.model for e in ests} == {"claude-opus", "gpt-4o-mini"}
        assert ests[0].model == "gpt-4o-mini"  # cheaper first

    def test_empty_models_returns_empty(self):
        assert compare_models("x", models=[]) == []

    def test_unknown_model_in_subset_raises(self):
        with pytest.raises(KeyError):
            compare_models("x", models=["gpt-4o", "does-not-exist"])

    def test_explicit_input_tokens(self):
        ests = compare_models(input_tokens=1000, output_tokens=1000, models=["gpt-4o"])
        assert ests[0].input_tokens == 1000

    def test_tie_break_by_name(self):
        add_model("tie-a", 0.001, 0.001, 4096)
        add_model("tie-b", 0.001, 0.001, 4096)
        ests = compare_models(input_tokens=100, output_tokens=100, models=["tie-b", "tie-a"])
        # equal cost -> sorted by model name ascending
        assert [e.model for e in ests] == ["tie-a", "tie-b"]


# --------------------------------------------------------------------------- #
# aggregate                                                                    #
# --------------------------------------------------------------------------- #
class TestAggregate:
    def test_empty_rollup(self):
        r = aggregate([])
        assert r["files"] == 0
        assert r["total_tokens"] == 0
        assert r["total_cost_usd"] == 0

    def test_single(self):
        e = estimate(model="gpt-4o", input_tokens=1000, output_tokens=500)
        r = aggregate([e])
        assert r["files"] == 1
        assert r["input_tokens"] == 1000
        assert r["output_tokens"] == 500
        assert r["total_tokens"] == 1500

    def test_sum_of_many(self):
        ests = [estimate("a b c", model="gpt-4o") for _ in range(5)]
        r = aggregate(ests)
        assert r["files"] == 5
        assert r["total_tokens"] == 5 * ests[0].input_tokens

    def test_accepts_generator(self):
        gen = (estimate("x", model="gpt-4o") for _ in range(3))
        r = aggregate(gen)
        assert r["files"] == 3

    def test_cost_rounded_six_places(self):
        ests = [estimate(model="claude-opus", input_tokens=333, output_tokens=333)]
        r = aggregate(ests)
        # value should be a float rounded to <= 6 decimals
        assert round(r["total_cost_usd"], 6) == r["total_cost_usd"]
