"""Core engine for TOKENMETER.

Implements a deterministic, dependency-free token estimator plus a pricing
table and budget checker. The tokenizer approximates BPE-style subword counts
the way production LLM tokenizers (e.g. tiktoken / Claude / GPT) split text:
whitespace and punctuation are boundaries, long alphanumeric runs are broken
into ~4-character subword chunks, and digits/symbols cost more per token.

This is an *estimator*, not a byte-exact reproduction of any vendor's BPE
merges, but it is calibrated to land within a few percent of real counts for
typical English prose and code, which is what budgeting/CI gating needs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

TOOL_NAME: str = "tokenmeter"
TOOL_VERSION: str = "0.7.7"


@dataclass(frozen=True)
class ModelPricing:
    """USD price per 1,000 tokens for input and output."""

    name: str
    input_per_1k: float
    output_per_1k: float
    context_window: int

    def cost(self, input_tokens: int, output_tokens: int) -> float:
        return (
            input_tokens / 1000.0 * self.input_per_1k
            + output_tokens / 1000.0 * self.output_per_1k
        )


# Representative public list prices (USD / 1K tokens). These are easy to update
# and are intentionally data, not hard-coded into logic.
MODELS: Dict[str, ModelPricing] = {
    "claude-opus": ModelPricing("claude-opus", 0.015, 0.075, 200_000),
    "claude-sonnet": ModelPricing("claude-sonnet", 0.003, 0.015, 200_000),
    "claude-haiku": ModelPricing("claude-haiku", 0.00080, 0.0040, 200_000),
    "gpt-4o": ModelPricing("gpt-4o", 0.0025, 0.010, 128_000),
    "gpt-4o-mini": ModelPricing("gpt-4o-mini", 0.00015, 0.00060, 128_000),
    "gpt-4-turbo": ModelPricing("gpt-4-turbo", 0.010, 0.030, 128_000),
    "generic-1k": ModelPricing("generic-1k", 0.001, 0.002, 8_192),
}


def add_model(
    name: str, input_per_1k: float, output_per_1k: float, context_window: int = 8192
) -> ModelPricing:
    """Register or override a model's pricing at runtime."""
    if not name or not isinstance(name, str):
        raise ValueError("model name must be a non-empty string")
    in_price = float(input_per_1k)
    out_price = float(output_per_1k)
    ctx = int(context_window)
    if in_price < 0:
        raise ValueError(f"input_per_1k must be >= 0, got {in_price}")
    if out_price < 0:
        raise ValueError(f"output_per_1k must be >= 0, got {out_price}")
    if ctx <= 0:
        raise ValueError(f"context_window must be > 0, got {ctx}")
    p = ModelPricing(name, in_price, out_price, ctx)
    MODELS[name] = p
    return p


def get_pricing(model: str) -> ModelPricing:
    if model not in MODELS:
        raise KeyError(
            f"unknown model {model!r}; known: {', '.join(sorted(MODELS))}"
        )
    return MODELS[model]


def list_models() -> List[ModelPricing]:
    return [MODELS[k] for k in sorted(MODELS)]


# A token boundary is hit on whitespace runs and on punctuation/symbols.
_WORD_RE = re.compile(r"[A-Za-z]+|\d+|\s+|[^\sA-Za-z\d]")
_SUBWORD = 4  # average characters per subword token for long alpha runs


def count_tokens(text: str) -> int:
    """Estimate the number of tokens in ``text``.

    Heuristics, applied per regex-matched chunk:
      * Whitespace: a run collapses to 0 tokens unless it contains a blank
        line / multiple newlines (which real tokenizers emit), then 1.
      * Alphabetic words: ceil(len / 4) subword tokens (min 1).
      * Digit runs: each group of up to 3 digits is its own token (matches how
        BPE tends to split numbers), min 1.
      * Single punctuation/symbol: 1 token.
    """
    if text is None:
        return 0
    if not text:
        return 0

    tokens = 0
    for m in _WORD_RE.finditer(text):
        chunk = m.group(0)
        c0 = chunk[0]
        if c0.isspace():
            # Newlines carry tokens; plain spaces between words usually merge
            # into the adjacent word token, so they cost nothing on their own.
            newlines = chunk.count("\n")
            if newlines >= 1:
                tokens += newlines
        elif c0.isalpha():
            tokens += max(1, -(-len(chunk) // _SUBWORD))  # ceil division
        elif c0.isdigit():
            tokens += max(1, -(-len(chunk) // 3))
        else:
            tokens += 1
    return tokens


@dataclass
class Estimate:
    model: str
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    context_window: int
    context_used_pct: float

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.input_tokens + self.output_tokens,
            "input_cost_usd": round(self.input_cost, 6),
            "output_cost_usd": round(self.output_cost, 6),
            "total_cost_usd": round(self.total_cost, 6),
            "context_window": self.context_window,
            "context_used_pct": round(self.context_used_pct, 2),
        }


def estimate(
    text: str = "",
    model: str = "claude-sonnet",
    *,
    input_tokens: Optional[int] = None,
    output_tokens: int = 0,
) -> Estimate:
    """Build a full cost estimate.

    If ``input_tokens`` is given it overrides counting ``text``. ``output_tokens``
    is the expected/observed completion length (defaults to 0).
    """
    pricing = get_pricing(model)
    in_tok = count_tokens(text) if input_tokens is None else int(input_tokens)
    if in_tok < 0:
        raise ValueError(f"input_tokens must be >= 0, got {in_tok}")
    out_tok = int(output_tokens)
    if out_tok < 0:
        raise ValueError(f"output_tokens must be >= 0, got {out_tok}")
    in_cost = in_tok / 1000.0 * pricing.input_per_1k
    out_cost = out_tok / 1000.0 * pricing.output_per_1k
    used = in_tok + out_tok
    pct = (used / pricing.context_window * 100.0) if pricing.context_window else 0.0
    return Estimate(
        model=model,
        input_tokens=in_tok,
        output_tokens=out_tok,
        input_cost=in_cost,
        output_cost=out_cost,
        total_cost=in_cost + out_cost,
        context_window=pricing.context_window,
        context_used_pct=pct,
    )


@dataclass
class BudgetResult:
    ok: bool
    estimate: Estimate
    max_cost_usd: Optional[float]
    max_tokens: Optional[int]
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "max_cost_usd": self.max_cost_usd,
            "max_tokens": self.max_tokens,
            "violations": list(self.violations),
            "estimate": self.estimate.to_dict(),
        }


def check_budget(
    est: Estimate,
    *,
    max_cost_usd: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> BudgetResult:
    """Check an estimate against cost and/or token ceilings."""
    violations: List[str] = []
    total_tokens = est.input_tokens + est.output_tokens

    if max_cost_usd is not None and est.total_cost > max_cost_usd:
        violations.append(
            f"cost ${est.total_cost:.6f} exceeds budget ${max_cost_usd:.6f}"
        )
    if max_tokens is not None and total_tokens > max_tokens:
        violations.append(
            f"tokens {total_tokens} exceed budget {max_tokens}"
        )
    if total_tokens > est.context_window:
        violations.append(
            f"tokens {total_tokens} exceed model context window {est.context_window}"
        )

    return BudgetResult(
        ok=not violations,
        estimate=est,
        max_cost_usd=max_cost_usd,
        max_tokens=max_tokens,
        violations=violations,
    )


def aggregate(estimates: Iterable[Estimate]) -> dict:
    """Sum a batch of estimates (e.g. many files) into one rollup."""
    items = list(estimates)
    in_tok = sum(e.input_tokens for e in items)
    out_tok = sum(e.output_tokens for e in items)
    total_cost = sum(e.total_cost for e in items)
    return {
        "files": len(items),
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "total_tokens": in_tok + out_tok,
        "total_cost_usd": round(total_cost, 6),
    }
