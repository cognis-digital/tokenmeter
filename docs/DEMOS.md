# Demos

Five runnable scenarios in [`../demos/`](../demos/), each targeting a different
audience. Every scenario drives the **real** `tokenmeter` API (`tokenmeter.core`)
against the bundled, offline fixtures under
[`../tokenmeter/demos/`](../tokenmeter/demos) — no network, no API keys, no heavy
deps. Run them in any order or on their own; each exits 0, so they double as
smoke tests.

```bash
python demos/run_all.py                       # all five, end to end
python demos/03_ci_budget_gate.py             # or just one
```

> On Windows set `PYTHONUTF8=1` so the box-rule output renders cleanly.

## 1. AI app prompt cost — *what does one call actually cost?*
**Audience:** teams building LLM-backed apps / agents.
Measure the real support-triage system prompt with a 400-token answer across
four models, then project a single call out to 50k requests/day. The lesson:
price the artifact you actually send and multiply by volume *before* you ship.

## 2. FinOps model selection — *rank one workload by cost*
**Audience:** FinOps, platform / infra owners.
Price one autonomous-agent planning step across every model, cheapest-first,
and surface the cost spread (often >100x) and a day-rate forecast at 8 steps ×
2,000 tasks/day. Model selection becomes a defensible line item.

## 3. CI budget gate — *fail the build before the bill*
**Audience:** release / build engineers.
Three gates: a cheap model passes a cost ceiling, the same prompt on Opus trips
it, and a 28k-token document dump fails on the context window alone — with **no**
ceilings set. `budget` behaves like a linter: a violation is a non-zero exit.

## 4. Prompt library rollup — *one number for the portfolio*
**Audience:** engineering managers / tech leads.
Batch a whole prompt library into one aggregate — total tokens, total cost, and
the heaviest prompt to review first. Track the rollup over time; a jump means a
prompt grew and cost will follow.

## 5. RAG context budget — *measure the assembled prompt*
**Audience:** engineers tuning RAG retrievers / context windows.
Size the real assembled RAG artifact and watch `context_used_pct`, then quantify
the recurring few-shot tax — the per-call premium of carrying examples, scaled
to a million calls.

---

Each demo prints clear, narrated output and exits 0. `tests/test_demos.py`
imports and runs every scenario under `pytest`, so the demos are also covered as
tests.
