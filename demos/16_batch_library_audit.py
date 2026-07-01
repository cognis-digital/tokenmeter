"""Scenario 16 - prompt-library audit with a per-prompt ceiling.

An engineering org enforces a per-prompt token ceiling in review. This demo
audits the whole prompt library, flags any prompt over the ceiling, and returns
the same aggregate the CLI `batch` command produces — a governance gate.

Audience: platform / governance teams enforcing prompt hygiene.
"""
import os

from _common import rule, fixture, usd
from tokenmeter.core import estimate, aggregate, check_budget


def main() -> None:
    rule("PROMPT LIBRARY AUDIT  -  flag prompts over the token ceiling")

    lib = fixture("04-batch-prompt-library", "prompts")
    paths = sorted(os.path.join(lib, f) for f in os.listdir(lib) if f.endswith(".txt"))
    model = "claude-sonnet"
    ceiling = 60  # per-prompt input-token ceiling for this fixture set

    ests = []
    flagged = []
    print(f"\nAuditing {len(paths)} prompts on {model} (ceiling {ceiling} tok):\n")
    for p in paths:
        with open(p, "r", encoding="utf-8", errors="replace") as fh:
            est = estimate(fh.read(), model=model)
        ests.append(est)
        res = check_budget(est, max_tokens=ceiling)
        mark = "OK " if res.ok else "OVER"
        if not res.ok:
            flagged.append(os.path.basename(p))
        print(f"  [{mark}] {os.path.basename(p):<24} {est.input_tokens:>4} tok  {usd(est.total_cost)}")

    roll = aggregate(ests)
    print(f"\n  library total: {roll['total_tokens']} tok  {usd(roll['total_cost_usd'])}")
    if flagged:
        print(f"  FLAGGED (trim before merge): {', '.join(flagged)}")
    else:
        print("  all prompts within ceiling.")
    print("Wire this as a review gate so oversized prompts never land silently.")


if __name__ == "__main__":
    main()
