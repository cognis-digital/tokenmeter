"""TOKENMETER - Token and cost counter / budgeter for LLM apps, CI-ready.

Standard-library-only, zero-install tool to estimate token counts and dollar
cost for LLM prompts/completions, and to enforce budgets in CI pipelines.
"""

from .core import (
    MODELS,
    BudgetResult,
    Estimate,
    ModelPricing,
    add_model,
    count_tokens,
    estimate,
    get_pricing,
    list_models,
)

TOOL_NAME = "tokenmeter"
TOOL_VERSION = "1.0.0"

__all__ = [
    "TOOL_NAME",
    "TOOL_VERSION",
    "MODELS",
    "BudgetResult",
    "Estimate",
    "ModelPricing",
    "add_model",
    "count_tokens",
    "estimate",
    "get_pricing",
    "list_models",
]
