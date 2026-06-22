# Demo 07 — What do few-shot examples actually cost?

**Where the data came from.** Two variants of the same sentiment classifier:
`zeroshot.txt` (instructions only) and `fewshot.txt` (the same instructions plus
six in-context examples). Few-shot examples usually improve accuracy, but they
ride along in the prompt on **every single call** — a recurring tax you pay
forever. This demo quantifies that tax so you can decide if it's worth it.

**What to expect.** `batch` shows the few-shot prompt costing several times the
zero-shot prompt per call. The `compare`/`count` numbers let you put a dollar
figure on "six examples" at your real traffic volume.

## Run

```bash
# Side-by-side token + cost for both variants:
python -m tokenmeter batch \
    tokenmeter/demos/07-fewshot-vs-zeroshot/zeroshot.txt \
    tokenmeter/demos/07-fewshot-vs-zeroshot/fewshot.txt \
    -m gpt-4o-mini
```

```bash
# Cost of the few-shot prompt alone, on Sonnet, with a 5-token answer:
python -m tokenmeter count \
    -f tokenmeter/demos/07-fewshot-vs-zeroshot/fewshot.txt \
    -m claude-sonnet -o 5
```

## How to act

- Take the per-call delta (few-shot minus zero-shot input tokens), multiply by
  your monthly call volume and the model's input price — that's the annual cost
  of those examples.
- If accuracy gains don't justify the recurring cost, prune examples, or move
  them into a fine-tune / cached prefix so they aren't re-billed each call.
