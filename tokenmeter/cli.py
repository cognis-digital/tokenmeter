"""Command-line interface for TOKENMETER."""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from typing import List, Optional

from . import TOOL_NAME, TOOL_VERSION
from .core import (
    aggregate,
    check_budget,
    compare_models,
    estimate,
    get_pricing,
    list_models,
)


def _csv(rows: List[tuple]) -> None:
    """Write rows (first row = header) as CSV to stdout."""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    for r in rows:
        writer.writerow(r)
    sys.stdout.write(buf.getvalue())


def _read_input(args: argparse.Namespace) -> str:
    if getattr(args, "text", None) is not None:
        return args.text
    if getattr(args, "file", None):
        with open(args.file, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    # No explicit source: read stdin if piped.
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return ""


def _emit(payload: dict, fmt: str, rows: Optional[List[tuple]] = None) -> None:
    if fmt == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    if fmt == "csv" and rows is not None:
        _csv(rows)
        return
    # table
    if rows is not None:
        widths = [max(len(str(r[i])) for r in rows) for i in range(len(rows[0]))]
        for r in rows:
            print("  ".join(str(c).ljust(widths[i]) for i, c in enumerate(r)))
        return
    for k, v in payload.items():
        print(f"{k:<20} {v}")


def _cmd_count(args: argparse.Namespace) -> int:
    text = _read_input(args)
    est = estimate(
        text,
        model=args.model,
        output_tokens=args.output_tokens,
    )
    d = est.to_dict()
    rows = [
        ("metric", "value"),
        ("model", d["model"]),
        ("input_tokens", d["input_tokens"]),
        ("output_tokens", d["output_tokens"]),
        ("total_tokens", d["total_tokens"]),
        ("input_cost_usd", f"{d['input_cost_usd']:.6f}"),
        ("output_cost_usd", f"{d['output_cost_usd']:.6f}"),
        ("total_cost_usd", f"{d['total_cost_usd']:.6f}"),
        ("context_used_pct", f"{d['context_used_pct']}%"),
    ]
    _emit(d, args.format, rows)
    return 0


def _cmd_budget(args: argparse.Namespace) -> int:
    text = _read_input(args)
    est = estimate(text, model=args.model, output_tokens=args.output_tokens)
    result = check_budget(
        est, max_cost_usd=args.max_cost, max_tokens=args.max_tokens
    )
    d = result.to_dict()
    if args.format == "json":
        print(json.dumps(d, indent=2, sort_keys=True))
    else:
        ed = result.estimate.to_dict()
        print(f"model            {ed['model']}")
        print(f"total_tokens     {ed['total_tokens']}")
        print(f"total_cost_usd   {ed['total_cost_usd']:.6f}")
        print(f"max_cost_usd     {result.max_cost_usd}")
        print(f"max_tokens       {result.max_tokens}")
        print(f"status           {'OK' if result.ok else 'OVER BUDGET'}")
        for v in result.violations:
            print(f"  ! {v}")
    return 0 if result.ok else 1


def _cmd_models(args: argparse.Namespace) -> int:
    models = list_models()
    payload = {
        "models": [
            {
                "name": m.name,
                "input_per_1k": m.input_per_1k,
                "output_per_1k": m.output_per_1k,
                "context_window": m.context_window,
            }
            for m in models
        ]
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        rows = [("model", "in/1k", "out/1k", "context")]
        for m in models:
            rows.append(
                (m.name, f"{m.input_per_1k:.5f}", f"{m.output_per_1k:.5f}", m.context_window)
            )
        _emit(payload, args.format, rows)
    return 0


def _cmd_batch(args: argparse.Namespace) -> int:
    estimates = []
    per_file = []
    for path in args.files:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError as exc:
            print(f"error: cannot read {path}: {exc}", file=sys.stderr)
            return 2
        est = estimate(text, model=args.model)
        estimates.append(est)
        per_file.append((path, est))

    roll = aggregate(estimates)
    payload = {
        "rollup": roll,
        "files": [
            {"path": p, **e.to_dict()} for p, e in per_file
        ],
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        rows = [("file", "tokens", "cost_usd")]
        for p, e in per_file:
            rows.append((p, e.input_tokens, f"{e.total_cost:.6f}"))
        rows.append(("TOTAL", roll["total_tokens"], f"{roll['total_cost_usd']:.6f}"))
        _emit(payload, args.format, rows)

    if args.max_cost is not None and roll["total_cost_usd"] > args.max_cost:
        print(
            f"error: batch cost ${roll['total_cost_usd']:.6f} exceeds "
            f"${args.max_cost:.6f}",
            file=sys.stderr,
        )
        return 1
    return 0


def _cmd_compare(args: argparse.Namespace) -> int:
    text = _read_input(args)
    models = args.models.split(",") if getattr(args, "models", None) else None
    try:
        ests = compare_models(
            text, output_tokens=args.output_tokens, models=models
        )
    except (KeyError, ValueError) as exc:
        print(f"error: {exc.args[0] if exc.args else exc}", file=sys.stderr)
        return 2
    if not ests:
        print("error: no models to compare", file=sys.stderr)
        return 2
    payload = {
        "output_tokens": args.output_tokens,
        "input_tokens": ests[0].input_tokens if ests else 0,
        "ranking": [e.to_dict() for e in ests],
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    rows = [("model", "in_tok", "out_tok", "total_cost_usd", "ctx_used_%")]
    for e in ests:
        d = e.to_dict()
        rows.append(
            (
                d["model"],
                d["input_tokens"],
                d["output_tokens"],
                f"{d['total_cost_usd']:.6f}",
                f"{d['context_used_pct']}",
            )
        )
    _emit(payload, args.format, rows)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog=TOOL_NAME,
        description="Token and cost counter / budgeter for LLM apps (CI-ready).",
    )
    p.add_argument(
        "--version", action="version", version=f"{TOOL_NAME} {TOOL_VERSION}"
    )
    p.add_argument(
        "--format",
        choices=("table", "json", "csv"),
        default=None,
        help="output format (default: table)",
    )
    sub = p.add_subparsers(dest="command", required=True)

    def add_format(sp):
        sp.add_argument(
            "--format",
            dest="sub_format",
            choices=("table", "json", "csv"),
            default=None,
            help="output format (default: table)",
        )

    def add_source(sp):
        add_format(sp)
        g = sp.add_mutually_exclusive_group()
        g.add_argument("-t", "--text", help="literal text to measure")
        g.add_argument("-f", "--file", help="read text from a file")
        sp.add_argument(
            "-m", "--model", default="claude-sonnet", help="pricing model id"
        )
        sp.add_argument(
            "-o",
            "--output-tokens",
            type=int,
            default=0,
            help="expected completion tokens (for cost)",
        )

    c = sub.add_parser("count", help="count tokens and estimate cost")
    add_source(c)
    c.set_defaults(func=_cmd_count)

    b = sub.add_parser("budget", help="fail (exit 1) if over a cost/token budget")
    add_source(b)
    b.add_argument("--max-cost", type=float, help="max total USD allowed")
    b.add_argument("--max-tokens", type=int, help="max total tokens allowed")
    b.set_defaults(func=_cmd_budget)

    m = sub.add_parser("models", help="list known models and pricing")
    add_format(m)
    m.set_defaults(func=_cmd_models)

    bt = sub.add_parser("batch", help="estimate many files and roll up")
    add_format(bt)
    bt.add_argument("files", nargs="+", help="files to measure")
    bt.add_argument("-m", "--model", default="claude-sonnet", help="pricing model id")
    bt.add_argument("--max-cost", type=float, help="max total USD for the batch")
    bt.set_defaults(func=_cmd_batch)

    cmp = sub.add_parser(
        "compare", help="estimate one workload across all models, cheapest first"
    )
    add_format(cmp)
    g = cmp.add_mutually_exclusive_group()
    g.add_argument("-t", "--text", help="literal text to measure")
    g.add_argument("-f", "--file", help="read text from a file")
    cmp.add_argument(
        "-o",
        "--output-tokens",
        type=int,
        default=0,
        help="expected completion tokens (for cost)",
    )
    cmp.add_argument(
        "--models",
        help="comma-separated subset of models to compare (default: all)",
    )
    cmp.set_defaults(func=_cmd_compare)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    # --format may be given before or after the subcommand; subcommand wins,
    # then top-level, then the table default.
    sub_fmt = getattr(args, "sub_format", None)
    if sub_fmt is not None:
        args.format = sub_fmt
    elif getattr(args, "format", None) is None:
        args.format = "table"
    try:
        return args.func(args)
    except KeyError as exc:
        print(f"error: {exc.args[0] if exc.args else exc}", file=sys.stderr)
        return 2
    except (ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except BrokenPipeError:
        return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
