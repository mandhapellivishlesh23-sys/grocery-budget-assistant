"""The actual budget maths: compare spending to the budget, flag problems."""
import calendar
import statistics
from collections import defaultdict
from datetime import date

from .config import WARN_AT


def items_in_month(items, month):
    return [i for i in items if i.month == month]


def months_present(items):
    return sorted({i.month for i in items})


def budget_status(items, budget, month):
    spent = round(sum(i.total for i in items_in_month(items, month)), 2)
    pct = (spent / budget * 100) if budget else 0.0
    if spent > budget:
        level = "OVER"
    elif pct >= WARN_AT * 100:
        level = "WARNING"
    else:
        level = "OK"
    return {
        "month": month, "budget": budget, "spent": spent,
        "remaining": round(budget - spent, 2), "pct": pct, "level": level,
    }


def overspend_point(items, budget, month):
    """The purchase that pushed the month over budget (or None)."""
    running = 0.0
    ordered = sorted(items_in_month(items, month), key=lambda i: (i.date, i.id))
    for it in ordered:
        running += it.total
        if running > budget:
            return it, round(running, 2)
    return None


def projection(items, budget, month, today=None):
    """Rough end-of-month estimate based on the daily pace so far.
    Only makes sense for the month that is still running."""
    today = today or date.today()
    if month != today.strftime("%Y-%m"):
        return None
    year, mon = int(month[:4]), int(month[5:])
    days_in_month = calendar.monthrange(year, mon)[1]
    spent = sum(i.total for i in items_in_month(items, month))
    if spent == 0:
        return None
    projected = spent / today.day * days_in_month
    return {"projected": round(projected, 2), "will_exceed": projected > budget}


def spend_by_category(items):
    totals = defaultdict(float)
    for it in items:
        totals[it.category] += it.total
    return sorted(((c, round(t, 2)) for c, t in totals.items()),
                  key=lambda pair: pair[1], reverse=True)


def spend_by_month(items):
    totals = defaultdict(float)
    for it in items:
        totals[it.month] += it.total
    return [(m, round(totals[m], 2)) for m in sorted(totals)]


def top_items(items, n=5):
    return sorted(items, key=lambda i: i.total, reverse=True)[:n]


def find_anomalies(items, budget):
    """Returns a list of (item, reason). Deliberately simple rules."""
    by_cat = defaultdict(list)
    for it in items:
        by_cat[it.category].append(it.price)

    flags = []
    for it in items:
        reasons = []
        prices = by_cat[it.category]
        if len(prices) >= 5:
            med = statistics.median(prices)
            if med > 0 and it.price > 2.5 * med:
                reasons.append(f"unit price is {it.price / med:.1f}x the {it.category} median")
        if it.price < 1:
            reasons.append("suspiciously low price")
        if it.quantity >= 20:
            reasons.append(f"large quantity ({it.quantity})")
        if budget and it.total > 0.2 * budget:
            reasons.append("one purchase is over 20% of the monthly budget")
        for r in reasons:
            flags.append((it, r))
    return flags


def search(items, keyword="", category="", start="", end=""):
    keyword = keyword.strip().lower()
    out = []
    for it in items:
        if keyword and keyword not in it.name.lower():
            continue
        if category and it.category != category:
            continue
        if start and it.date < start:
            continue
        if end and it.date > end:
            continue
        out.append(it)
    return sorted(out, key=lambda i: (i.date, i.id))


def summarize(items, budget, month, today=None):
    today = today or date.today()
    month_items = items_in_month(items, month)
    status = budget_status(items, budget, month)

    if month == today.strftime("%Y-%m"):
        days = today.day
    else:
        days = calendar.monthrange(int(month[:4]), int(month[5:]))[1]

    trend = spend_by_month(items)
    trend_note = "Not enough history for a trend yet."
    months = [m for m, _ in trend]
    if month in months and months.index(month) > 0:
        prev_month, prev_total = trend[months.index(month) - 1]
        if prev_total > 0:
            # compare per-day pace so a half-finished month isn't judged against a full one
            prev_days = calendar.monthrange(int(prev_month[:4]), int(prev_month[5:]))[1]
            now_pace = status["spent"] / days
            prev_pace = prev_total / prev_days
            change = (now_pace - prev_pace) / prev_pace * 100
            word = "faster" if change >= 0 else "slower"
            trend_note = (f"Daily spending pace is {abs(change):.1f}% {word} "
                          f"than in {prev_month}.")

    return {
        **status,
        "item_count": len(month_items),
        "avg_item_total": round(status["spent"] / len(month_items), 2) if month_items else 0.0,
        "avg_per_day": round(status["spent"] / days, 2) if days else 0.0,
        "by_category": spend_by_category(month_items),
        "top_items": top_items(month_items),
        "trend": trend,
        "trend_note": trend_note,
        "anomalies": [(i, r) for i, r in find_anomalies(items, budget) if i.month == month],
        "overspend_point": overspend_point(items, budget, month),
        "projection": projection(items, budget, month, today),
    }
