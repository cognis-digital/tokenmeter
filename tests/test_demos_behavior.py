"""Behavioral assertions for the demo scenarios beyond 'it prints something'.

Each demo drives the real API; here we assert the *shape* of what a few of them
produce (idempotence, exit code, cost figure) so a regression in the estimator
or a broken fixture is caught at the demo layer too.
"""
from __future__ import annotations

import contextlib
import importlib
import io
import os
import sys

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEMOS = os.path.join(REPO_ROOT, "demos")
for p in (REPO_ROOT, DEMOS):
    if p not in sys.path:
        sys.path.insert(0, p)

ALL_SCENARIOS = [
    "01_ai_app_prompt_cost", "02_finops_model_selection", "03_ci_budget_gate",
    "04_eng_manager_prompt_library", "05_rag_context_budget",
    "06_chat_transcript_cost", "07_context_window_guard", "08_diff_review_cost",
    "09_fewshot_tax", "10_classifier_router", "11_agent_step_budget",
    "12_prompt_diet", "13_rag_chunk_tuning", "14_multi_model_portfolio",
    "15_streaming_output_forecast", "16_batch_library_audit",
    "17_custom_model_pricing", "18_json_output_pipeline", "19_regression_guard",
    "20_full_month_forecast",
]


def _capture(name):
    mod = importlib.import_module(name)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        mod.main()
    return buf.getvalue()


@pytest.mark.parametrize("name", ALL_SCENARIOS)
def test_every_demo_prints_cost(name):
    out = _capture(name)
    assert "$" in out, f"{name} printed no cost figure"
    assert out.strip()


@pytest.mark.parametrize("name", ALL_SCENARIOS)
def test_every_demo_is_idempotent(name):
    # Running twice must not raise (e.g. add_model overrides cleanly, no state
    # leaks between runs).
    a = _capture(name)
    b = _capture(name)
    assert a and b


def test_run_all_lists_twenty_scenarios():
    runner = importlib.import_module("run_all")
    assert len(runner.SCENARIOS) == 20


def test_run_all_completes():
    runner = importlib.import_module("run_all")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        runner.main()
    assert "All demo scenarios completed." in buf.getvalue()


def test_json_pipeline_demo_emits_valid_json():
    import json
    out = _capture("18_json_output_pipeline")
    # extract the JSON block (between first '{' and matching structure); the
    # demo prints a full record, so find a parseable object.
    start = out.index("{")
    # find the end by scanning for the last closing brace before "Parsed"
    end = out.rindex("}") + 1
    obj = json.loads(out[start:end])
    assert obj["estimate"]["model"] == "claude-sonnet"
