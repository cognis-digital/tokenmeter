"""Scenario 17 - self-hosted / custom model pricing.

Running your own model (or a vendor not in the table) means you set the price.
This demo registers a custom "$/1k" for a self-hosted deployment via add_model,
then compares its effective cost against the hosted options — the classic
build-vs-buy break-even.

Audience: infra teams pricing a self-hosted model against APIs.
"""
from _common import rule, read_fixture, usd
from tokenmeter.core import add_model, estimate, compare_models


def main() -> None:
    rule("CUSTOM MODEL PRICING  -  price your self-hosted model in the same table")

    # Amortized GPU cost expressed as $/1k tokens (illustrative).
    add_model("self-hosted-8b", input_per_1k=0.0002, output_per_1k=0.0002, context_window=32_000)
    print("\nRegistered 'self-hosted-8b' at $0.0002/1k in+out, 32k window.")

    prompt = read_fixture("02-rag-context", "retrieved_context.txt")
    ranking = compare_models(
        prompt, output_tokens=300,
        models=["self-hosted-8b", "gpt-4o-mini", "claude-haiku", "claude-sonnet"],
    )
    print("\nSame RAG workload, cheapest first:\n")
    for e in ranking:
        d = e.to_dict()
        print(f"  {d['model']:<18} {usd(d['total_cost_usd'])}  (ctx {d['context_used_pct']}%)")

    sh = next(e for e in ranking if e.model == "self-hosted-8b")
    hosted = next(e for e in ranking if e.model == "claude-haiku")
    per_call_saving = hosted.total_cost - sh.total_cost
    print(f"\nPer-call saving vs claude-haiku: {usd(per_call_saving)}. "
          "Divide your fixed GPU spend by that to get the break-even call volume.")


if __name__ == "__main__":
    main()
