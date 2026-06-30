"""Shared helpers for the demo scenarios.

Every scenario drives the *real* tokenmeter API (`tokenmeter.core`) against the
bundled, offline fixtures under ``tokenmeter/demos/<name>/``. No network, no
keys, no heavy deps — just the same estimator the CLI uses.
"""
from __future__ import annotations

import os
import sys

# allow `python demos/xx.py` from anywhere
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(REPO_ROOT, "tokenmeter", "demos")


def fixture(*parts: str) -> str:
    """Absolute path to a bundled demo fixture."""
    return os.path.join(FIXTURES, *parts)


def read_fixture(*parts: str) -> str:
    with open(fixture(*parts), "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def rule(title: str) -> None:
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def usd(value: float) -> str:
    return f"${value:.6f}"
