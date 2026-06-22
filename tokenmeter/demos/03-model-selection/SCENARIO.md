# Demo 03 — Picking the cheapest model that fits (`compare`)

**Where the data came from.** `classifier_prompt.txt` is a production intent
classifier prompt for a support inbox. The completion is tiny (one label, so
~5 output tokens), but you run it on *every* inbound message — millions a
month — so the per-call cost dominates your LLM bill. You want the cheapest
model for a short, well-specified task.

**What to expect.** `compare` estimates the same prompt across every known
model and prints them **cheapest first**. For this short-output workload the
input price dominates, so `gpt-4o-mini` lands at the top and `claude-opus` at
the bottom — often a 50–100x spread for identical work.

## Run

```bash
# Rank every model for a 5-token classification answer:
python -m tokenmeter compare \
    -f tokenmeter/demos/03-model-selection/classifier_prompt.txt -o 5
```

```bash
# Compare only the models you are actually allowed to use, as CSV for a sheet:
python -m tokenmeter compare \
    -f tokenmeter/demos/03-model-selection/classifier_prompt.txt -o 5 \
    --models gpt-4o-mini,claude-haiku,gpt-4o --format csv
```

## How to act

- For a cheap, deterministic task like classification, take the cheapest model
  whose quality you have validated — usually the mini/haiku tier.
- Re-run `compare` after any vendor price change (prices are data in
  `tokenmeter`, so the ranking updates the moment you edit the model table).
- Multiply the top row's `total_cost_usd` by monthly volume for a budget line.
