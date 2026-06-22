# Demo 04 — Costing a whole prompt library in one pass (`batch`)

**Where the data came from.** `prompts/` holds three real system prompts from a
single product: a meeting summarizer, an invoice extractor, and a read-only SQL
assistant. As the library grows you want a single rolled-up number: how many
tokens does the whole catalog represent, and what does one call of each cost?

**What to expect.** `batch` measures every file, prints a per-file row, and a
`TOTAL` row. The longest prompt (the invoice extractor or SQL assistant)
contributes the most tokens. With `--max-cost` it doubles as a CI gate.

## Run

```bash
# Roll up the whole library on Haiku:
python -m tokenmeter batch \
    tokenmeter/demos/04-batch-prompt-library/prompts/*.txt -m claude-haiku
```

```bash
# As a CI gate: fail if the catalog's combined per-call cost tops $0.01.
python -m tokenmeter batch \
    tokenmeter/demos/04-batch-prompt-library/prompts/*.txt \
    -m claude-sonnet --max-cost 0.01
echo "exit: $?"
```

```bash
# Export the per-file breakdown to CSV for a spreadsheet / dashboard:
python -m tokenmeter batch \
    tokenmeter/demos/04-batch-prompt-library/prompts/*.txt \
    -m gpt-4o-mini --format csv > prompt_costs.csv
```

## How to act

- A prompt that is far larger than its siblings is a refactor candidate — move
  static instructions to a shared preamble or trim few-shot examples.
- Wire the `--max-cost` gate into CI so a careless prompt edit can't silently
  inflate every request.
