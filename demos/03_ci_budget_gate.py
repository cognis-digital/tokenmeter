"""Scenario 3 - CI / release engineering.

A prompt change that quietly doubles cost or overflows the context window should
break the build, not production. tokenmeter's budget check returns a non-zero
exit on any violation, so it drops into a pipeline like a linter. This demo runs
three gates and shows exactly which fail and why — without exiting the process,
so it composes cleanly inside run_all.

Audience: release / build engineers wiring cost gates into CI.
"""
from _common import rule, read_fixture, usd
from tokenmeter.core import estimate, check_budget


def _gate(label: str, text: str, *, model: str, output_tokens: int,
          max_cost=None, max_tokens=None) -> None:
    est = estimate(text, model=model, output_tokens=output_tokens)
    res = check_budget(est, max_cost_usd=max_cost, max_tokens=max_tokens)
    status = "PASS (exit 0)" if res.ok else "FAIL (exit 1)"
    print(f"\n  {label}")
    print(f"    model={model}  total={usd(est.total_cost)}  tokens={est.input_tokens + est.output_tokens}")
    print(f"    budget: max_cost={max_cost}  max_tokens={max_tokens}  ->  {status}")
    for v in res.violations:
        print(f"      ! {v}")


def main() -> None:
    rule("CI BUDGET GATE  -  fail the build before the bill, like a linter")

    prompt = read_fixture("01-basic", "prompt.txt")
    overflow = read_fixture("06-context-window-guard", "document_dump.txt")

    # 1) A reasonable prompt on a cheap model: passes.
    _gate("Gate A: per-call cost ceiling on a cheap model",
          prompt, model="gpt-4o-mini", output_tokens=400,
          max_cost=0.01, max_tokens=1500)

    # 2) The same prompt on Opus trips the cost ceiling: fails.
    _gate("Gate B: same prompt on claude-opus blows the same ceiling",
          prompt, model="claude-opus", output_tokens=400,
          max_cost=0.01, max_tokens=1500)

    # 3) A document dump that cannot fit an 8k window: fails on the window alone,
    #    even with no explicit ceilings — fail fast before the API rejects it.
    _gate("Gate C: context overflow fails with NO ceilings set",
          overflow, model="generic-1k", output_tokens=0)

    print("\nWire `tokenmeter budget ... --max-cost X` as a CI step; a red gate is a blocked merge.")


if __name__ == "__main__":
    main()
