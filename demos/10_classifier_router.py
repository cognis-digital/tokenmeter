"""Scenario 10 - model routing / cascades.

Many workloads (classification, routing, intent detection) are cheap enough to
run on a small model, escalating to a big model only on low confidence. This
demo prices a classifier prompt on a small vs large model and computes the
blended cost of a cascade that escalates 15% of the time.

Audience: engineers designing model cascades / routers.
"""
from _common import rule, read_fixture, usd
from tokenmeter.core import estimate


def main() -> None:
    rule("CLASSIFIER ROUTER  -  small model first, escalate the hard 15%")

    prompt = read_fixture("03-model-selection", "classifier_prompt.txt")
    small = estimate(prompt, model="gpt-4o-mini", output_tokens=20)
    large = estimate(prompt, model="claude-opus", output_tokens=20)

    print(f"\nClassifier prompt (20-token label):")
    print(f"  small (gpt-4o-mini): {usd(small.total_cost)}")
    print(f"  large (claude-opus): {usd(large.total_cost)}")

    escalate = 0.15
    # cascade pays the small model always, and the large model on escalations
    blended = small.total_cost + escalate * large.total_cost
    always_large = large.total_cost
    saved_pct = (1 - blended / always_large) * 100 if always_large else 0
    print(f"\nCascade (small always + large on {escalate:.0%}): {usd(blended)}/call")
    print(f"  vs always-large {usd(always_large)}/call -> {saved_pct:.0f}% cheaper")

    calls = 5_000_000
    print(f"  over {calls:,} calls: ${blended * calls:,.2f} vs ${always_large * calls:,.2f}")
    print("Cascades win when the small model handles the easy majority correctly.")


if __name__ == "__main__":
    main()
