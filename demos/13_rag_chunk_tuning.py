"""Scenario 13 - RAG retriever tuning (top-k sweep).

The retriever's top-k directly drives context size and cost. This demo sweeps k
by measuring what a growing slice of retrieved context costs and where it starts
eating dangerous fractions of the window.

Audience: RAG engineers picking a top-k / chunk budget.
"""
from _common import rule, read_fixture, usd
from tokenmeter.core import estimate, get_pricing


def main() -> None:
    rule("RAG CHUNK TUNING  -  sweep top-k against cost and window")

    context = read_fixture("02-rag-context", "retrieved_context.txt")
    model = "claude-sonnet"
    full_tokens = estimate(context, model=model).input_tokens
    window = get_pricing(model).context_window

    print(f"\nRetrieved-context budget on {model} (window {window:,}), 300-token answer:\n")
    print(f"  {'k (fraction)':<14}{'in_tok':>8}{'cost':>14}{'window_%':>12}")
    for frac in (0.25, 0.5, 0.75, 1.0, 1.5):
        in_tok = int(full_tokens * frac)
        est = estimate(model=model, input_tokens=in_tok, output_tokens=300)
        d = est.to_dict()
        print(f"  {frac:<14}{in_tok:>8}{usd(d['total_cost_usd']):>14}{d['context_used_pct']:>12}")

    print("\nPick the smallest k that answers well; each extra chunk is paid on every query.")


if __name__ == "__main__":
    main()
