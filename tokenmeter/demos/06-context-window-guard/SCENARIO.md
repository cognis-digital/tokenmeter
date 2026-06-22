# Demo 06 — Catching a context-window overflow before the API rejects it

**Where the data came from.** `document_dump.txt` is a synthetic "evidence
bundle" (400 numbered sections) of the kind a naive pipeline produces when it
concatenates every retrieved/scraped document into one prompt. It is ~28,000
tokens — far past the 8,192-token window of a small model. If you send this you
get a hard API error and a wasted round-trip.

**What to expect.** `budget` fails with exit code **1** purely on the context
check, *even with no `--max-cost` or `--max-tokens` set*: a prompt that can't
fit the window is always over budget. The violation line names the window.

## Run

```bash
# No ceilings given — it still fails because the prompt exceeds the window:
python -m tokenmeter budget \
    -f tokenmeter/demos/06-context-window-guard/document_dump.txt -m generic-1k
echo "exit: $?"     # -> 1
```

```bash
# The same bundle DOES fit a 200k-window model, so this passes:
python -m tokenmeter budget \
    -f tokenmeter/demos/06-context-window-guard/document_dump.txt \
    -m claude-haiku --max-cost 1.00
echo "exit: $?"     # -> 0
```

## How to act

- Run `budget` as a guard *before* dispatching to the model — fail fast instead
  of paying for a request the provider will reject.
- An overflow means your retriever/assembler is dumping too much. Add chunk
  caps, summarization, or a larger-window model — `budget` tells you which.
