# Demos

**Twenty** runnable scenarios in [`../demos/`](../demos/), each targeting a
different audience. Every scenario drives the **real** `tokenmeter` API
(`tokenmeter.core`) against the bundled, offline fixtures under
[`../tokenmeter/demos/`](../tokenmeter/demos) — no network, no API keys, no heavy
deps. Run them in any order or on their own; each exits 0, so they double as
smoke tests.

```bash
python demos/run_all.py                       # all twenty, end to end
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

## 6. Chat transcript cost — *you re-pay for history every turn*
**Audience:** teams shipping chat assistants.
Measure a real multi-turn transcript, model the compounding cost of a 10-turn
session as history grows, and show the saving from windowing history to a third.

## 7. Context window guard — *will this prompt even fit?*
**Audience:** platform engineers adding pre-flight checks.
Check a large document dump against every model's window and print which models
can take it — fail fast before the API rejects a prompt you already paid to build.

## 8. Diff review cost — *what does an AI PR reviewer cost per month?*
**Audience:** dev-tooling teams.
Price one PR diff review across four models and project the monthly bill at 40
PRs/day, then show the cheap-model-first routing that keeps it affordable.

## 9. Few-shot tax — *the recurring cost of carrying examples*
**Audience:** prompt engineers.
Quantify the per-call premium of few-shot vs zero-shot and scale it to 10k / 100k
/ 1M calls, so you can decide whether the quality lift earns the tax.

## 10. Classifier router — *small model first, escalate the hard 15%*
**Audience:** engineers designing model cascades.
Price a classifier prompt on a small vs large model and compute the blended cost
of a cascade that escalates only low-confidence cases.

## 11. Agent step budget — *cap the loop before it runs away*
**Audience:** teams running autonomous agents.
Price one agent step, derive the max steps a per-task budget allows, and gate a
projected multi-step run — halting the agent before it overspends.

## 12. Prompt diet — *the ROI of trimming a prompt*
**Audience:** anyone optimizing a high-volume prompt.
Measure a verbose prompt vs a trimmed variant and show the per-call and monthly
savings — the payback on a few minutes of editing.

## 13. RAG chunk tuning — *sweep top-k against cost and window*
**Audience:** RAG engineers picking a top-k / chunk budget.
Sweep the retrieved-context size and watch cost and `window_%` climb, to pick the
smallest k that still answers well.

## 14. Multi-model portfolio — *one rollup for finance*
**Audience:** platform owners doing chargeback / showback.
Build a portfolio of workloads (prompt + model + daily volume) and roll up the
projected daily and monthly spend into one defensible number.

## 15. Output length forecast — *output tokens are the pricey ones*
**Audience:** engineers setting `max_tokens` / controlling verbosity.
Hold the prompt fixed and sweep expected output length to show how a chatty model
or an unbounded `max_tokens` multiplies cost.

## 16. Prompt library audit — *flag prompts over the token ceiling*
**Audience:** platform / governance teams.
Audit the whole prompt library against a per-prompt token ceiling and flag any
prompt that would need trimming before merge — a governance gate.

## 17. Custom model pricing — *price your self-hosted model in the same table*
**Audience:** infra teams pricing self-hosted models.
Register a custom `$/1k` via `add_model`, compare it against hosted options, and
derive the build-vs-buy break-even call volume.

## 18. JSON output pipeline — *emit a parseable cost record*
**Audience:** engineers integrating cost telemetry.
Produce the same JSON record the CLI's `--format json` path emits and round-trip
it, proving everything tokenmeter returns composes into other tools.

## 19. Cost regression guard — *fail the PR when a prompt gets fatter*
**Audience:** teams treating prompt cost like a performance budget.
Compare a stored baseline cost against the current prompt and fail if growth
exceeds tolerance — a diff-time cost gate that stops silent creep.

## 20. Full month forecast — *the number for the budget meeting*
**Audience:** anyone owning an LLM cost line.
Apply a weekday/weekend traffic profile to a real prompt and produce a monthly
forecast per model, showing how much model choice alone swings the budget.

---

Each demo prints clear, narrated output and exits 0. `tests/test_demos.py` and
`tests/test_demos_behavior.py` import and run every scenario under `pytest`, so
the demos are also covered as tests.
