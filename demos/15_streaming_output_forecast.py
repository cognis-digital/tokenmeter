"""Scenario 15 - output-length sensitivity.

Output tokens are usually the most expensive tokens (output price > input price).
This demo holds the prompt fixed and sweeps expected output length, showing how
much a chatty model or an unbounded max_tokens costs you.

Audience: engineers setting max_tokens / controlling verbosity.
"""
from _common import rule, read_fixture, usd
from tokenmeter.core import estimate, get_pricing


def main() -> None:
    rule("OUTPUT LENGTH FORECAST  -  output tokens are the pricey ones")

    prompt = read_fixture("01-basic", "prompt.txt")
    model = "claude-opus"
    p = get_pricing(model)
    print(f"\n{model}: input ${p.input_per_1k}/1k, output ${p.output_per_1k}/1k "
          f"(output is {p.output_per_1k / p.input_per_1k:.0f}x input)\n")

    print(f"  {'max output tok':<16}{'total cost':>14}")
    base = None
    for out in (100, 500, 1000, 2000, 4000):
        est = estimate(prompt, model=model, output_tokens=out)
        if base is None:
            base = est.total_cost
        print(f"  {out:<16}{usd(est.total_cost):>14}")

    big = estimate(prompt, model=model, output_tokens=4000)
    print(f"\nGoing from 100 to 4000 output tokens is {big.total_cost / base:.1f}x the cost. "
          "Cap max_tokens and ask for concise answers where you can.")


if __name__ == "__main__":
    main()
