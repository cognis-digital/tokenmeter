"""Scenario 12 - prompt optimization ("prompt diet").

Trimming boilerplate from a system prompt cuts cost on every single call. This
demo measures a verbose prompt, a trimmed version, and reports the savings both
per-call and at scale — the ROI of the editing work.

Audience: anyone optimizing a high-volume prompt.
"""
from _common import rule, read_fixture, usd
from tokenmeter.core import estimate, count_tokens


def main() -> None:
    rule("PROMPT DIET  -  measure the ROI of trimming a prompt")

    verbose = read_fixture("01-basic", "prompt.txt")
    # A trimmed variant: drop the trailing half (simulates removing boilerplate).
    lines = verbose.splitlines()
    trimmed = "\n".join(lines[: max(1, len(lines) // 2)])

    model = "claude-sonnet"
    v = estimate(verbose, model=model, output_tokens=200)
    t = estimate(trimmed, model=model, output_tokens=200)
    saved = v.total_cost - t.total_cost

    print(f"\nOn {model} (200-token answer):")
    print(f"  verbose: {count_tokens(verbose):>4} tok  {usd(v.total_cost)}")
    print(f"  trimmed: {count_tokens(trimmed):>4} tok  {usd(t.total_cost)}")
    print(f"  saved per call: {usd(saved)}")

    daily = 200_000
    print(f"\nAt {daily:,} calls/day the trim saves ${saved * daily:,.2f}/day "
          f"(${saved * daily * 30:,.2f}/mo).")
    print("A 10-minute edit can pay for itself many times over at volume.")


if __name__ == "__main__":
    main()
