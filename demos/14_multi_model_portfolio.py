"""Scenario 14 - portfolio cost allocation.

A platform runs several workloads on different models. This demo builds a
portfolio (each workload = a prompt fixture + a model + a daily volume) and rolls
up the projected daily and monthly spend, so finance sees one defensible number.

Audience: platform owners doing chargeback / showback.
"""
from _common import rule, read_fixture, usd
from tokenmeter.core import estimate


WORKLOADS = [
    ("support-triage",   ("01-basic", "prompt.txt"),                 "claude-haiku",  200_000, 300),
    ("rag-answers",      ("02-rag-context", "retrieved_context.txt"), "claude-sonnet",  50_000, 300),
    ("agent-planning",   ("08-csv-finops", "agent_step_prompt.txt"),  "gpt-4o",        400_000, 120),
    ("code-review",      ("09-stdin-pipeline", "sample_diff.txt"),    "claude-opus",     5_000, 600),
]


def main() -> None:
    rule("MULTI-MODEL PORTFOLIO  -  one rollup for finance")

    print(f"\n  {'workload':<18}{'model':<14}{'calls/day':>11}{'$/day':>14}")
    total_day = 0.0
    for name, fx, model, volume, out in WORKLOADS:
        est = estimate(read_fixture(*fx), model=model, output_tokens=out)
        day = est.total_cost * volume
        total_day += day
        print(f"  {name:<18}{model:<14}{volume:>11,}{usd(day):>14}")

    print(f"  {'-' * 55}")
    print(f"  {'TOTAL':<18}{'':<14}{'':>11}{usd(total_day):>14}")
    print(f"\nProjected spend: ${total_day:,.2f}/day  ->  ${total_day * 30:,.2f}/mo. "
          "Re-run when a prompt or volume changes to catch cost drift early.")


if __name__ == "__main__":
    main()
