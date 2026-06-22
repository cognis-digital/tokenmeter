# Demo 02 — Sizing a RAG prompt before you send it

**Where the data came from.** A retrieval-augmented-generation (RAG) pipeline
assembled a prompt by stitching a system instruction together with four
retrieved documentation chunks and the user question. `retrieved_context.txt`
is exactly what the pipeline would hand to the model. Before paying for the
call you want to know how big the assembled prompt is and what the call costs.

**What to expect.** The assembled context is a few hundred tokens — cheap on
small models, more on Opus. The point is to *measure the real assembled
artifact*, not guess.

## Run

```bash
# Cost of one call with a ~300-token answer, on Haiku:
python -m tokenmeter count \
    -f tokenmeter/demos/02-rag-context/retrieved_context.txt \
    -m claude-haiku -o 300
```

```bash
# Same prompt, machine-readable, to log per-request cost in your tracing:
python -m tokenmeter --format json count \
    -f tokenmeter/demos/02-rag-context/retrieved_context.txt \
    -m claude-haiku -o 300 | jq '{tokens: .total_tokens, usd: .total_cost_usd}'
```

## How to act

- If `context_used_pct` is climbing toward 100%, your retriever is pulling too
  many / too large chunks — cap `k` or chunk size.
- Multiply `total_cost_usd` by your expected request volume to get a daily
  spend estimate before you ship the feature.
