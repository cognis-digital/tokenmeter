"""Scenario 11 - autonomous agents.

An agent loops: think -> act -> observe, many LLM calls per task. Runaway loops
are a real cost incident. This demo prices one agent step and enforces a
per-task budget gate that would halt the agent before it overspends.

Audience: teams running autonomous / tool-using agents.
"""
from _common import rule, read_fixture, usd
from tokenmeter.core import estimate, check_budget


def main() -> None:
    rule("AGENT STEP BUDGET  -  cap the loop before it runs away")

    step = read_fixture("08-csv-finops", "agent_step_prompt.txt")
    model = "claude-sonnet"
    per_step = estimate(step, model=model, output_tokens=120)
    print(f"\nOne agent step on {model}: {usd(per_step.total_cost)} "
          f"({per_step.input_tokens} in / {per_step.output_tokens} out)")

    max_task_cost = 0.05
    max_steps = int(max_task_cost / per_step.total_cost) if per_step.total_cost else 0
    print(f"\nPer-task budget {usd(max_task_cost)} => at most ~{max_steps} steps.")

    for n_steps in (10, max_steps, max_steps + 20):
        projected = estimate(model=model,
                             input_tokens=per_step.input_tokens * n_steps,
                             output_tokens=per_step.output_tokens * n_steps)
        res = check_budget(projected, max_cost_usd=max_task_cost)
        status = "OK" if res.ok else "HALT"
        print(f"  {n_steps:>3} steps -> {usd(projected.total_cost)}  [{status}]")

    print("Gate cumulative task cost each step; halt the agent when the ceiling is hit.")


if __name__ == "__main__":
    main()
