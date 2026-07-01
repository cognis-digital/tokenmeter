"""Scenario 19 - prompt cost-regression guard.

Cost creep is silent: a prompt grows a little each PR until the bill jumps. This
demo compares a stored baseline cost against the current prompt and fails (like a
regression test) if the increase exceeds a tolerance — a diff-time cost gate.

Audience: teams treating prompt cost like a performance budget.
"""
from _common import rule, read_fixture, usd
from tokenmeter.core import estimate


def main() -> None:
    rule("COST REGRESSION GUARD  -  fail the PR when a prompt gets fatter")

    prompt = read_fixture("01-basic", "prompt.txt")
    model = "claude-sonnet"
    current = estimate(prompt, model=model, output_tokens=400)

    # Simulate a stored baseline (what the prompt cost last release).
    baseline_tokens = int(current.input_tokens * 0.85)  # it grew ~18% since
    baseline = estimate(model=model, input_tokens=baseline_tokens, output_tokens=400)

    tolerance = 0.10  # allow 10% growth
    growth = (current.total_cost - baseline.total_cost) / baseline.total_cost
    print(f"\nOn {model}:")
    print(f"  baseline: {baseline.input_tokens} tok  {usd(baseline.total_cost)}")
    print(f"  current:  {current.input_tokens} tok  {usd(current.total_cost)}")
    print(f"  growth:   {growth:+.1%}  (tolerance {tolerance:.0%})")

    if growth > tolerance:
        print("  -> would FAIL the gate: prompt cost regressed beyond tolerance.")
    else:
        print("  -> within tolerance.")
    print("Store the baseline in the repo; compare on every PR to stop silent drift.")


if __name__ == "__main__":
    main()
