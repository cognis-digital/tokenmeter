"""Package identity, public-API surface, and metadata consistency tests."""
from __future__ import annotations

import importlib

import pytest


def test_tool_name_and_version_from_core():
    core = importlib.import_module("tokenmeter.core")
    assert core.TOOL_NAME == "tokenmeter"
    assert isinstance(core.TOOL_VERSION, str) and core.TOOL_VERSION


def test_package_reexports_identity():
    m = importlib.import_module("tokenmeter")
    assert m.TOOL_NAME == "tokenmeter"
    assert m.__version__ == m.TOOL_VERSION


def test_public_api_symbols_present():
    m = importlib.import_module("tokenmeter")
    for name in (
        "count_tokens", "estimate", "get_pricing", "list_models",
    ):
        assert hasattr(m, name), name


def test_core_public_api_symbols_present():
    core = importlib.import_module("tokenmeter.core")
    for name in (
        "count_tokens", "estimate", "get_pricing", "list_models",
        "add_model", "aggregate", "check_budget", "compare_models",
        "MODELS", "ModelPricing", "Estimate", "BudgetResult",
    ):
        assert hasattr(core, name), name


def test_cli_has_main_and_build_parser():
    cli = importlib.import_module("tokenmeter.cli")
    assert callable(cli.main)
    assert callable(cli.build_parser)


def test_main_module_importable():
    assert importlib.import_module("tokenmeter.__main__") is not None
