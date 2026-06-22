# Demo 05 — How much did this conversation cost?

**Where the data came from.** `conversation.txt` is a multi-turn chat session
(system + 4 user turns + 3 assistant turns) from a coding-assistant product,
exported in a plain `role: text` transcript format. Multi-turn chat is the
sneaky cost driver: each turn re-sends the **entire** prior history as input, so
a long thread is far more expensive than its latest message suggests.

**What to expect.** Treat the whole transcript as the input for the *next* turn
(the worst case, since the model re-reads everything). The token count is the
full conversation, not just the last message.

## Run

```bash
# What the next turn costs on Sonnet, assuming a ~250-token reply:
python -m tokenmeter count \
    -f tokenmeter/demos/05-chat-transcript/conversation.txt \
    -m claude-sonnet -o 250
```

```bash
# Compare what continuing this thread costs on every model:
python -m tokenmeter compare \
    -f tokenmeter/demos/05-chat-transcript/conversation.txt -o 250
```

## How to act

- If `input_tokens` for the full thread is large, add history truncation or a
  rolling summary so old turns don't get re-billed on every message.
- For long-lived chats, route to a cheaper model once the thread crosses a
  token threshold — `compare` shows you the savings.
