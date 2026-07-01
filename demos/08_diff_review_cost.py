"""Scenario 8 - AI code review in CI.

An automated PR reviewer sends the diff to an LLM on every push. Big diffs cost
more and can blow the window. This demo prices a real diff and projects the
monthly bill for a team's PR volume, then shows the cheap-model alternative.

Audience: dev-tooling teams wiring LLM code review into pipelines.
"""
from _common import rule, read_fixture, usd
from tokenmeter.core import estimate, compare_models


def main() -> None:
    rule("DIFF REVIEW COST  -  what does an AI PR reviewer cost per month?")

    diff = read_fixture("09-stdin-pipeline", "sample_diff.txt")
    print("\nOne PR diff reviewed (~600-token review comment):\n")

    ranking = compare_models(diff, output_tokens=600,
                             models=["claude-haiku", "claude-sonnet", "gpt-4o", "claude-opus"])
    for e in ranking:
        d = e.to_dict()
        print(f"  {d['model']:<14} per_review={usd(d['total_cost_usd'])}  in={d['input_tokens']}")

    prs_per_day, workdays = 40, 21
    monthly = prs_per_day * workdays
    cheap, dear = ranking[0], ranking[-1]
    print(f"\nAt {prs_per_day} PRs/day x {workdays} workdays = {monthly} reviews/month:")
    print(f"  {cheap.model}: {usd(cheap.total_cost * monthly)}/mo   "
          f"{dear.model}: {usd(dear.total_cost * monthly)}/mo")
    print("Route routine reviews to the cheap model; reserve the expensive one for flagged PRs.")


if __name__ == "__main__":
    main()
