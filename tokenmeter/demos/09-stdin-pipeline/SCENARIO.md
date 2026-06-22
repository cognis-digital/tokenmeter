# Demo 09 — Measure anything from a pipe (stdin)

**Where the data came from.** `sample_diff.txt` is a real-shaped `git diff`
hunk. A common workflow is "summarize this PR with an LLM" or "ask the model to
review this diff" — and you want to know the cost *before* you pipe it in. Both
`count` and `budget` read stdin when you give no `-t`/`-f`, so `tokenmeter`
drops into any Unix pipeline.

**What to expect.** Whatever you pipe in is measured. This lets you gate
LLM-in-CI steps on the size of live artifacts (diffs, logs, command output)
without writing them to a file first.

## Run

```bash
# Cost to have a model review this diff (≈400-token review), via stdin:
cat tokenmeter/demos/09-stdin-pipeline/sample_diff.txt \
  | python -m tokenmeter count -m claude-sonnet -o 400
```

```bash
# Real CI use: gate "LLM review of the staged diff" on a per-call budget.
# (Outside this demo you'd use `git diff --staged` instead of the sample file.)
cat tokenmeter/demos/09-stdin-pipeline/sample_diff.txt \
  | python -m tokenmeter budget -m claude-haiku -o 400 --max-cost 0.01
echo "exit: $?"
```

```bash
# Pipe the whole README through the cheapest model estimate:
cat README.md | python -m tokenmeter count -m gpt-4o-mini
```

## How to act

- In a pre-commit or CI hook, pipe `git diff --staged` through `budget` to skip
  the LLM review (or warn) when a diff is too large to review cheaply.
- Because it reads stdin, `tokenmeter` composes with `grep`, `jq`, `sed`, and
  any tool that emits text — no temp files needed.
