import csv

from .config import CURRENCY, EXPORT_DIR
from .logic import items_in_month


def money(x):
    return f"{CURRENCY}{x:,.2f}"


def bar(pct, width=24):
    filled = min(width, int(round(pct / 100 * width)))
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def render_text(s):
    lines = [
        f"GROCERY BUDGET REPORT - {s['month']}",
        "=" * 44,
        f"Budget        : {money(s['budget'])}",
        f"Spent         : {money(s['spent'])} ({s['pct']:.1f}%)",
        f"Remaining     : {money(s['remaining'])}",
        f"Status        : {s['level']}",
        f"Items bought  : {s['item_count']}",
        f"Avg per item  : {money(s['avg_item_total'])}",
        f"Avg per day   : {money(s['avg_per_day'])}",
        "",
        "Spending by category",
        "-" * 44,
    ]
    for cat, total in s["by_category"]:
        share = total / s["spent"] * 100 if s["spent"] else 0
        lines.append(f"  {cat:<12} {money(total):>14}  {share:5.1f}%")
    lines += ["", "Biggest purchases", "-" * 44]
    for it in s["top_items"]:
        lines.append(f"  {it.date}  {it.name:<22} {money(it.total):>12}")
    lines += ["", "Monthly trend", "-" * 44]
    for m, t in s["trend"]:
        lines.append(f"  {m}  {money(t):>14}")
    lines.append("  " + s["trend_note"])

    if s["overspend_point"]:
        it, running = s["overspend_point"]
        lines += ["", f"!! Budget was crossed on {it.date} by buying {it.name} "
                      f"(running total {money(running)})."]
    if s["projection"]:
        p = s["projection"]
        verdict = "that is OVER budget" if p["will_exceed"] else "that fits the budget"
        lines.append(f"Projected month-end spend: {money(p['projected'])} - {verdict}.")
    if s["anomalies"]:
        lines += ["", "Things worth a second look", "-" * 44]
        for it, why in s["anomalies"]:
            lines.append(f"  #{it.id} {it.name}: {why}")
    return "\n".join(lines) + "\n"


def render_markdown(s):
    out = [
        f"# Grocery Budget Report - {s['month']}", "",
        f"**Status: {s['level']}**", "",
        "| Metric | Value |", "|---|---|",
        f"| Budget | {money(s['budget'])} |",
        f"| Spent | {money(s['spent'])} ({s['pct']:.1f}%) |",
        f"| Remaining | {money(s['remaining'])} |",
        f"| Items bought | {s['item_count']} |",
        f"| Average per item | {money(s['avg_item_total'])} |",
        f"| Average per day | {money(s['avg_per_day'])} |", "",
        "## Spending by category", "",
        "| Category | Total | Share |", "|---|---|---|",
    ]
    for cat, total in s["by_category"]:
        share = total / s["spent"] * 100 if s["spent"] else 0
        out.append(f"| {cat} | {money(total)} | {share:.1f}% |")
    out += ["", "## Biggest purchases", "", "| Date | Item | Total |", "|---|---|---|"]
    for it in s["top_items"]:
        out.append(f"| {it.date} | {it.name} | {money(it.total)} |")
    out += ["", "## Trend", ""]
    for m, t in s["trend"]:
        out.append(f"- {m}: {money(t)}")
    out += ["", s["trend_note"]]
    if s["overspend_point"]:
        it, running = s["overspend_point"]
        out += ["", f"> Budget crossed on **{it.date}** when buying *{it.name}* "
                    f"(running total {money(running)})."]
    if s["anomalies"]:
        out += ["", "## Flags", ""]
        for it, why in s["anomalies"]:
            out.append(f"- #{it.id} {it.name}: {why}")
    return "\n".join(out) + "\n"


def export_all(summary, items):
    """Writes .md, .txt and .csv for the summary's month. Returns the paths."""
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    month = summary["month"]
    paths = {
        "markdown": EXPORT_DIR / f"report_{month}.md",
        "text": EXPORT_DIR / f"audit_{month}.txt",
        "csv": EXPORT_DIR / f"report_{month}.csv",
    }
    paths["markdown"].write_text(render_markdown(summary), encoding="utf-8")
    paths["text"].write_text(render_text(summary), encoding="utf-8")

    with open(paths["csv"], "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "date", "name", "category", "unit_price", "quantity", "total"])
        for it in sorted(items_in_month(items, month), key=lambda i: (i.date, i.id)):
            w.writerow([it.id, it.date, it.name, it.category, it.price, it.quantity, it.total])
        w.writerow([])
        w.writerow(["", "", "MONTH TOTAL", "", "", "", summary["spent"]])
        w.writerow(["", "", "BUDGET", "", "", "", summary["budget"]])
    return paths
