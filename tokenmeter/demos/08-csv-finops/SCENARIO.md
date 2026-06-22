# Demo 08 — FinOps: export cost data as CSV for a spreadsheet

**Where the data came from.** `agent_step_prompt.txt` is the planning-step
prompt of an autonomous agent. Agents call the model many times per task
(plan → act → observe → re-plan), so finance wants the per-step cost across
candidate models in a format they can drop straight into a spreadsheet or BI
tool. The `--format csv` output exists for exactly this.

**What to expect.** Clean comma-separated rows with a header — no ANSI, no
box-drawing, no parsing required. Pipe it to a file and open it in Excel /
Sheets, or load it with pandas.

## Run

```bash
# Per-model cost of one agent step (≈120-token JSON action), as CSV:
python -m tokenmeter compare \
    -f tokenmeter/demos/08-csv-finops/agent_step_prompt.txt -o 120 \
    --format csv > agent_step_costs.csv
cat agent_step_costs.csv
```

```bash
# The full price book as CSV, to reconcile against vendor invoices:
python -m tokenmeter models --format csv > price_book.csv
```

```bash
# Load straight into pandas for charts / pivots:
python - <<'PY'
import io, subprocess, csv
out = subprocess.check_output(
    ["python","-m","tokenmeter","compare",
     "-f","tokenmeter/demos/08-csv-finops/agent_step_prompt.txt",
     "-o","120","--format","csv"], text=True)
for row in csv.DictReader(io.StringIO(out)):
    print(row["model"], "->", row["total_cost_usd"])
PY
```

## How to act

- Multiply the per-step cost by the *average steps per task* and your task
  volume to forecast agent spend before you launch.
- Keep `price_book.csv` under version control; diff it after each vendor price
  change to see exactly what moved.
