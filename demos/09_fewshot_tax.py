"""Scenario 9 - prompt engineering trade-offs.

Few-shot examples improve quality but you pay for them on *every* call, forever.
This demo quantifies the recurring "few-shot tax" against the zero-shot baseline
and shows the break-even volume where trimming examples pays for itself.

Audience: prompt engineers deciding how many examples to carry.
"""
from _common import rule, read_fixture, usd
from tokenmeter.core import estimate


def main() -> None:
    rule("FEW-SHOT TAX  -  the recurring cost of carrying examples")

    fewshot = read_fixture("07-fewshot-vs-zeroshot", "fewshot.txt")
    zeroshot = read_fixture("07-fewshot-vs-zeroshot", "zeroshot.txt")
    model = "claude-sonnet"

    fs = estimate(fewshot, model=model, output_tokens=80)
    zs = estimate(zeroshot, model=model, output_tokens=80)
    delta = fs.total_cost - zs.total_cost

    print(f"\nOn {model} (80-token answer):")
    print(f"  zero-shot: {zs.input_tokens:>4} tok  {usd(zs.total_cost)}")
    print(f"  few-shot:  {fs.input_tokens:>4} tok  {usd(fs.total_cost)}")
    print(f"  per-call few-shot premium: {usd(delta)}")

    for volume in (10_000, 100_000, 1_000_000):
        print(f"  at {volume:>9,} calls: ${delta * volume:,.2f} extra")
    print("If few-shot doesn't lift quality enough to justify that tax, move examples "
          "to a fine-tune or a retrieval step.")


if __name__ == "__main__":
    main()
