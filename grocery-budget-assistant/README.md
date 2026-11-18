# Grocery Budget Assistant

A terminal app that tracks grocery purchases against a fixed monthly budget and
tells you when you're overspending. Built for the Campus Catalyst hackathon
(Project #18).

## What it does

- Menu-driven terminal interface (colours switch off automatically if your terminal can't show them)
- Strict input validation: bad prices, quantities, dates, categories and blank names are rejected with a reason, and you're asked again
- Compares each month's spending with your budget: **OK / WARNING (80%+) / OVER**
- Shows *which purchase* pushed you over budget, and projects your month-end spend
- Flags odd entries (unit price far above its category's median, huge quantities, suspiciously low prices)
- Saves everything to `data/grocery_data.json` after every change
- A damaged or missing data file never crashes the app: it's backed up and a clean one is created
- Search by keyword, category and date range
- Summary with totals, averages, category split, top purchases and monthly trend
- Charts (Matplotlib PNGs) and exports to Markdown, plain-text audit log and CSV
- Bulk CSV import with a row-by-row error log

## Setup

Needs Python 3.10+.

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

The app works without Matplotlib too; only the chart option is disabled.

## Quick demo

1. Start the app and choose **11** to load the 47 sample entries
2. **6** (Budget check) shows November in the warning zone and flags a few odd entries
3. **1** add an item and type some nonsense first to see validation catch it
4. **10** and enter `data/sample_messy.csv` to see bad rows rejected and logged
5. **7**, **8**, **9** for the summary, charts and exports (saved in `exports/`)
6. Choose **0**, start the app again, and choose **2**: your data is still there

## Project layout

```
main.py                    entry point
grocery_budget/
    config.py              paths, currency symbol, budget defaults
    models.py              Item dataclass and Tracker
    validation.py          every input rule in one place
    storage.py             JSON load/save with corruption handling
    logic.py               budget maths, anomalies, search, summary
    importer.py            CSV import with row-level errors
    reports.py             text / markdown / csv exports
    plotting.py            Matplotlib charts
    ui.py                  menu and prompts
tests/                     unittest suite (23 tests)
data/                      sample CSV/JSON files
make_sample_data.py        regenerates the sample files
```

## Tests

```bash
python -m unittest -v
```

## Settings

Edit `grocery_budget/config.py` to change the currency symbol, default budget,
warning threshold (default 80%) or page size.

## Data format

```json
{"version": 1, "budget": 6000.0,
 "items": [{"id": 1, "name": "Milk 1L", "category": "dairy",
            "price": 62.0, "quantity": 4, "date": "2026-09-02"}]}
```
`price` is per unit. Item total = price x quantity.
