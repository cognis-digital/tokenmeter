"""Scenario 18 - machine-readable output for pipelines.

tokenmeter's estimates are plain dicts, so they drop into any pipeline as JSON.
This demo drives the same API the CLI's `--format json` path uses and prints a
parseable record other tools can consume (dashboards, alerting, chargeback).

Audience: engineers integrating cost telemetry into other systems.
"""
import json

from _common import rule, read_fixture, usd
from tokenmeter.core import estimate, check_budget


def main() -> None:
    rule("JSON OUTPUT PIPELINE  -  emit a parseable cost record")

    prompt = read_fixture("01-basic", "prompt.txt")
    est = estimate(prompt, model="claude-sonnet", output_tokens=400)
    res = check_budget(est, max_cost_usd=0.02, max_tokens=5000)

    record = res.to_dict()
    blob = json.dumps(record, indent=2, sort_keys=True)
    print("\nEmitted record (pipe to jq, a dashboard, or an alerting rule):\n")
    print(blob)

    # Round-trip proves it is valid, parseable JSON.
    parsed = json.loads(blob)
    assert parsed["estimate"]["model"] == "claude-sonnet"
    print(f"\nParsed back OK: cost {usd(parsed['estimate']['total_cost_usd'])}, "
          f"budget_ok={parsed['ok']}.")
    print("Everything tokenmeter returns is a dict -> JSON, so it composes anywhere.")


if __name__ == "__main__":
    main()
