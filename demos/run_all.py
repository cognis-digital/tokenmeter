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
    "06_chat_transcript_cost",
    "07_context_window_guard",
    "08_diff_review_cost",
    "09_fewshot_tax",
    "10_classifier_router",
    "11_agent_step_budget",
    "12_prompt_diet",
    "13_rag_chunk_tuning",
    "14_multi_model_portfolio",
    "15_streaming_output_forecast",
    "16_batch_library_audit",
    "17_custom_model_pricing",
    "18_json_output_pipeline",
    "19_regression_guard",
    "20_full_month_forecast",
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
