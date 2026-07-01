"""Scenario 20 - end-to-end monthly forecast.

Ties the pieces together: take a real prompt, price it on a chosen model, apply a
traffic profile (weekday vs weekend), and produce a defensible monthly forecast
with a per-model comparison — the number you take to a budget meeting.

Audience: anyone owning an LLM cost line and forecasting spend.
"""
from _common import rule, read_fixture, usd
from tokenmeter.core import estimate, compare_models


def main() -> None:
    rule("FULL MONTH FORECAST  -  the number for the budget meeting")

    prompt = read_fixture("02-rag-context", "retrieved_context.txt")
    weekday_calls, weekend_calls = 300_000, 90_000
    weekdays, weekend_days = 22, 8
    monthly_calls = weekday_calls * weekdays + weekend_calls * weekend_days

    print(f"\nTraffic: {weekday_calls:,}/weekday x {weekdays}d + "
          f"{weekend_calls:,}/weekend x {weekend_days}d = {monthly_calls:,} calls/mo\n")

    ranking = compare_models(
        prompt, output_tokens=300,
        models=["claude-haiku", "gpt-4o-mini", "claude-sonnet", "gpt-4o", "claude-opus"],
    )
    print(f"  {'model':<14}{'$/call':>12}{'$/month':>16}")
    for e in ranking:
        monthly = e.total_cost * monthly_calls
        print(f"  {e.model:<14}{usd(e.total_cost):>12}{('$%s' % format(monthly, ',.2f')):>16}")

    cheap, dear = ranking[0], ranking[-1]
    spread = dear.total_cost * monthly_calls - cheap.total_cost * monthly_calls
    print(f"\nModel choice alone swings this budget by ${spread:,.2f}/month "
          f"({cheap.model} vs {dear.model}). Forecast before you commit.")


if __name__ == "__main__":
    main()
