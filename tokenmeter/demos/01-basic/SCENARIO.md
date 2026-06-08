# Demo 01 — Budgeting an LLM prompt in CI

You maintain a service that sends a fixed system prompt to an LLM on every
request. Before shipping a prompt change you want to (a) see what each call
will cost and (b) fail the build if the prompt blows past your per-call budget.

`prompt.txt` is a realistic system prompt for a support-triage assistant.

## 1. Count tokens and estimate cost

```bash
# From the build_out directory:
python -m tokenmeter count -f tokenmeter/demos/01-basic/prompt.txt \
    -m claude-sonnet -o 400
```

This prints the input token count, the expected output cost for a 400-token
completion, the combined cost, and how much of the context window is used.

For machine-readable output (e.g. to post a comment on a PR):

```bash
python -m tokenmeter --format json count \
    -f tokenmeter/demos/01-basic/prompt.txt -m gpt-4o -o 400
```

## 2. Gate the build on a budget

Fail the pipeline (exit code 1) if a single call would cost more than
`$0.01` *or* exceed 1,500 total tokens:

```bash
python -m tokenmeter budget -f tokenmeter/demos/01-basic/prompt.txt \
    -m claude-opus -o 400 --max-cost 0.01 --max-tokens 1500
echo "exit: $?"
```

Because the opus output price is high, this prompt plus 400 output tokens trips
the cost ceiling and the command exits non-zero — exactly what you want a CI
step to do. Switch the model to `claude-sonnet` or `gpt-4o-mini` and it passes.

## 3. Compare models

```bash
python -m tokenmeter models --format json
```

## 4. Roll up a whole prompt library

```bash
python -m tokenmeter batch tokenmeter/demos/01-basic/prompt.txt \
    -m claude-haiku --max-cost 0.05
```

## Piping

`count` and `budget` also read stdin, so you can measure anything:

```bash
cat README.md | python -m tokenmeter count -m gpt-4o-mini
```
