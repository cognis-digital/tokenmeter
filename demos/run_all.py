"""Run every demo scenario end to end.

    python demos/run_all.py

Each scenario is independent and drives the real tokenmeter API against the
bundled offline fixtures, so they can be run in any order or on their own. The
process exits 0 when all scenarios complete, so this doubles as a smoke test.
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SCENARIOS = [
    "01_ai_app_prompt_cost",
    "02_finops_model_selection",
    "03_ci_budget_gate",
    "04_eng_manager_prompt_library",
    "05_rag_context_budget",
]


def main() -> None:
    for name in SCENARIOS:
        mod = importlib.import_module(name)
        mod.main()
    print("\n" + "=" * 70)
    print("  All demo scenarios completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
