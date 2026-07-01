"""Scenario 7 - platform guardrails.

Before you send an assembled prompt you want to know it will *fit* the model's
context window — a request that overflows is rejected by the API after you have
already paid to build it. This demo takes a document dump and checks it against
each model's window, showing which models can take it and which cannot.

Audience: platform engineers adding pre-flight window checks.
"""
from _common import rule, read_fixture, usd
from tokenmeter.core import estimate, check_budget, list_models


def main() -> None:
    rule("CONTEXT WINDOW GUARD  -  will this prompt even fit?")

    dump = read_fixture("06-context-window-guard", "document_dump.txt")
    print("\nA large document dump checked against every model's window:\n")
    print(f"  {'model':<14}{'window':>10}{'used_%':>10}  fits?")
    for m in list_models():
        est = estimate(dump, model=m.name, output_tokens=500)
        res = check_budget(est)
        fits = "yes" if res.ok else "NO"
        d = est.to_dict()
        print(f"  {m.name:<14}{m.context_window:>10}{d['context_used_pct']:>10}  {fits}")

    smallest = min(list_models(), key=lambda m: m.context_window)
    est = estimate(dump, model=smallest.name, output_tokens=500)
    print(f"\nSmallest window ({smallest.name}, {smallest.context_window}) "
          f"needs {est.input_tokens + est.output_tokens} tokens — "
          f"pre-flight the check, don't pay to be rejected. cost would be {usd(est.total_cost)}.")


if __name__ == "__main__":
    main()
