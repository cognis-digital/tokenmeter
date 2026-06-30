"""Scenario 1 - AI application developers.

You ship a feature that sends a fixed system prompt to an LLM on every request.
Before you merge a prompt change you want one number you can reason about: what
does *one call* cost, and how much of the context window does it eat? tokenmeter
answers that from the real assembled prompt artifact, not a guess.

Audience: teams building LLM-backed apps / agents.
"""
from _common import rule, read_fixture, usd
from tokenmeter.core import estimate


def main() -> None:
    rule("AI APP PROMPT COST  -  what does one call actually cost?")

    prompt = read_fixture("01-basic", "prompt.txt")
    print("\nMeasuring the real support-triage system prompt with a 400-token answer.\n")

    # The exact call path the CLI's `count` uses.
    for model in ("claude-haiku", "claude-sonnet", "gpt-4o", "claude-opus"):
        est = estimate(prompt, model=model, output_tokens=400)
        d = est.to_dict()
        print(
            f"  {model:<14} in={d['input_tokens']:>4}  out={d['output_tokens']:>4}  "
            f"total={usd(d['total_cost_usd'])}  ctx={d['context_used_pct']}%"
        )

    base = estimate(prompt, model="claude-sonnet", output_tokens=400)
    daily = base.total_cost * 50_000
    print(
        f"\nAt 50,000 requests/day on claude-sonnet that single prompt is "
        f"{usd(base.total_cost)}/call -> ~${daily:,.2f}/day."
    )
    print("Measure the artifact you actually send; multiply by volume before you ship.")


if __name__ == "__main__":
    main()
