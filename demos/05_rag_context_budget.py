"""Scenario 5 - RAG / context engineers.

A retrieval-augmented prompt is assembled at request time from a system
instruction plus retrieved chunks. The risk is silent: the retriever pulls more
context than you think, the prompt creeps toward the window, and cost climbs.
This demo measures the real assembled artifact, then shows how the few-shot
examples you carry on every call add a recurring tax.

Audience: engineers tuning RAG retrievers / context windows.
"""
from _common import rule, read_fixture, usd
from tokenmeter.core import estimate


def main() -> None:
    rule("RAG CONTEXT BUDGET  -  measure the assembled prompt, watch the window")

    assembled = read_fixture("02-rag-context", "retrieved_context.txt")
    model = "claude-haiku"
    est = estimate(assembled, model=model, output_tokens=300)
    d = est.to_dict()
    print(f"\nAssembled RAG prompt on {model} (300-token answer):")
    print(f"  input_tokens={d['input_tokens']}  total={usd(d['total_cost_usd'])}  "
          f"context_used={d['context_used_pct']}%")
    print("  If context_used climbs toward 100%, cap retriever k / chunk size.")

    # The few-shot tax: examples carried on EVERY call.
    fewshot = read_fixture("07-fewshot-vs-zeroshot", "fewshot.txt")
    zeroshot = read_fixture("07-fewshot-vs-zeroshot", "zeroshot.txt")
    fs = estimate(fewshot, model=model, output_tokens=50)
    zs = estimate(zeroshot, model=model, output_tokens=50)
    delta = fs.total_cost - zs.total_cost
    print("\nFew-shot vs zero-shot (same task, same model):")
    print(f"  zero-shot: {zs.input_tokens} tok  {usd(zs.total_cost)}")
    print(f"  few-shot:  {fs.input_tokens} tok  {usd(fs.total_cost)}")
    print(f"  per-call premium for carrying examples: {usd(delta)}")
    print(f"  over 1,000,000 calls that is ${delta * 1_000_000:,.2f} — decide if the lift earns it.")


if __name__ == "__main__":
    main()
