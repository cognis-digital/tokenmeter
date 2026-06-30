"""Scenario 2 - FinOps / platform engineering.

Finance does not care which model is "best" in the abstract; they care what each
candidate would charge for *your* workload. tokenmeter estimates one workload
across every model and ranks them cheapest-first, so model selection becomes a
line item you can defend, and the CSV drops straight into a spreadsheet.

Audience: FinOps, platform / infra owners doing cost allocation.
"""
from _common import rule, read_fixture, usd
from tokenmeter.core import compare_models


def main() -> None:
    rule("FINOPS MODEL SELECTION  -  rank one workload by cost, cheapest first")

    step = read_fixture("08-csv-finops", "agent_step_prompt.txt")
    print("\nOne autonomous-agent planning step (~120-token JSON action) priced everywhere:\n")

    ranking = compare_models(step, output_tokens=120)
    cheapest = ranking[0]
    dearest = ranking[-1]

    print(f"  {'model':<14}{'total_cost_usd':>16}{'ctx_used_%':>12}")
    for e in ranking:
        d = e.to_dict()
        print(f"  {d['model']:<14}{usd(d['total_cost_usd']):>16}{d['context_used_pct']:>12}")

    factor = dearest.total_cost / cheapest.total_cost if cheapest.total_cost else 0
    print(
        f"\nCheapest: {cheapest.model} ({usd(cheapest.total_cost)})  |  "
        f"dearest: {dearest.model} ({usd(dearest.total_cost)})  ->  {factor:.0f}x spread."
    )
    # Agents call the model many times per task; show the forecast that matters.
    steps_per_task, tasks_per_day = 8, 2_000
    fc_cheap = cheapest.total_cost * steps_per_task * tasks_per_day
    fc_dear = dearest.total_cost * steps_per_task * tasks_per_day
    print(
        f"At {steps_per_task} steps/task x {tasks_per_day:,} tasks/day: "
        f"${fc_cheap:,.2f}/day on {cheapest.model} vs ${fc_dear:,.2f}/day on {dearest.model}."
    )


if __name__ == "__main__":
    main()
