"""Scenario 6 - conversational / chatbot products.

A chat product pays for the *whole* transcript on every turn, because each new
user message re-sends the accumulated history. This demo measures a real
multi-turn conversation, then shows the compounding cost of carrying full
history vs. a windowed / summarized context.

Audience: teams shipping chat assistants who need to reason about history cost.
"""
from _common import rule, read_fixture, usd
from tokenmeter.core import estimate


def main() -> None:
    rule("CHAT TRANSCRIPT COST  -  you re-pay for history on every turn")

    convo = read_fixture("05-chat-transcript", "conversation.txt")
    model = "claude-haiku"

    # Full transcript resent each turn, ~150-token reply.
    full = estimate(convo, model=model, output_tokens=150)
    d = full.to_dict()
    print(f"\nFull transcript on {model} (150-token reply):")
    print(f"  history_tokens={d['input_tokens']}  per_turn={usd(d['total_cost_usd'])}")

    # A 10-turn session where history grows linearly: turn k pays ~k/N of the
    # full history. Approximate the running cost.
    turns = 10
    running = sum(
        estimate(convo, model=model, input_tokens=int(full.input_tokens * (k + 1) / turns),
                 output_tokens=150).total_cost
        for k in range(turns)
    )
    print(f"  {turns}-turn session (history grows each turn): {usd(running)}")

    # Windowed alternative: cap history at a third of the transcript.
    windowed = estimate(model=model, input_tokens=full.input_tokens // 3, output_tokens=150)
    saved = full.total_cost - windowed.total_cost
    print(f"\nCap history to 1/3 the transcript: {usd(windowed.total_cost)}/turn "
          f"({usd(saved)} saved/turn).")
    print("Windowing or summarizing history is the biggest lever on chat cost.")


if __name__ == "__main__":
    main()
