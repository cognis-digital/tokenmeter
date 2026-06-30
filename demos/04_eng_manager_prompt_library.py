"""Scenario 4 - engineering managers.

You own a growing library of prompts across several features and you want a
single rollup: how many tokens does the whole library represent, what does a
pass over it cost, and which prompt is the heavy one to review first.
tokenmeter batches a set of files into one aggregate, the same path the CLI's
`batch` command takes.

Audience: engineering managers / tech leads tracking prompt-portfolio cost.
"""
import os

from _common import rule, fixture, usd
from tokenmeter.core import estimate, aggregate


def main() -> None:
    rule("PROMPT LIBRARY ROLLUP  -  one number for the whole portfolio")

    lib_dir = fixture("04-batch-prompt-library", "prompts")
    paths = sorted(os.path.join(lib_dir, f) for f in os.listdir(lib_dir) if f.endswith(".txt"))

    model = "claude-haiku"
    per_file = []
    for p in paths:
        with open(p, "r", encoding="utf-8", errors="replace") as fh:
            est = estimate(fh.read(), model=model)
        per_file.append((os.path.basename(p), est))

    print(f"\nLibrary of {len(per_file)} prompts, priced on {model}:\n")
    print(f"  {'prompt':<22}{'tokens':>8}{'cost_usd':>14}")
    for name, est in per_file:
        print(f"  {name:<22}{est.input_tokens:>8}{usd(est.total_cost):>14}")

    roll = aggregate(e for _, e in per_file)
    print(f"  {'-' * 44}")
    print(f"  {'TOTAL':<22}{roll['total_tokens']:>8}{usd(roll['total_cost_usd']):>14}")

    heaviest = max(per_file, key=lambda t: t[1].input_tokens)
    print(
        f"\nHeaviest prompt: {heaviest[0]} ({heaviest[1].input_tokens} tokens) — "
        "review/trim that one first."
    )
    print("Track this rollup over time; a jump means a prompt grew and cost will follow.")


if __name__ == "__main__":
    main()
