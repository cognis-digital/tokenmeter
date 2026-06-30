"""Run every demo scenario as a smoke test. Stdlib + package only, no network."""
from __future__ import annotations

import importlib
import io
import os
import sys
import contextlib

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEMOS = os.path.join(REPO_ROOT, "demos")
for p in (REPO_ROOT, DEMOS):
    if p not in sys.path:
        sys.path.insert(0, p)

SCENARIOS = [
    "01_ai_app_prompt_cost",
    "02_finops_model_selection",
    "03_ci_budget_gate",
    "04_eng_manager_prompt_library",
    "05_rag_context_budget",
]


@pytest.mark.parametrize("name", SCENARIOS)
def test_scenario_runs_and_prints(name):
    mod = importlib.import_module(name)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        mod.main()
    out = buf.getvalue()
    assert out.strip(), f"{name} produced no output"
    assert "$" in out, f"{name} printed no cost figure"


def test_run_all_completes():
    runner = importlib.import_module("run_all")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        runner.main()
    assert "All demo scenarios completed." in buf.getvalue()
