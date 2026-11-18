"""Matplotlib charts. If matplotlib isn't installed the app still works,
it just tells the user the charts are unavailable."""
from .config import CURRENCY, EXPORT_DIR
from .logic import items_in_month, spend_by_category, spend_by_month


def _load_pyplot():
    try:
        import matplotlib
        matplotlib.use("Agg")          # no window needed, we save PNG files
        import matplotlib.pyplot as plt
        return plt
    except ImportError:
        return None


def make_charts(items, budget, month):
    """Returns (list_of_paths, error_message_or_None)."""
    plt = _load_pyplot()
    if plt is None:
        return [], "matplotlib isn't installed. Run: pip install -r requirements.txt"
    if not items:
        return [], "nothing to plot yet, add some items first"

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths = []

    # 1) month by month vs budget
    trend = spend_by_month(items)
    fig, ax = plt.subplots(figsize=(7, 4))
    labels = [m for m, _ in trend]
    values = [t for _, t in trend]
    colours = ["#c0392b" if t > budget else "#2e86c1" for t in values]
    ax.bar(labels, values, color=colours)
    ax.axhline(budget, color="black", linestyle="--", label=f"Budget ({CURRENCY}{budget:,.0f})")
    ax.set_title("Monthly grocery spend vs budget")
    ax.set_ylabel(f"Spent ({CURRENCY.strip()})")
    ax.legend()
    fig.tight_layout()
    p = EXPORT_DIR / "chart_monthly_trend.png"
    fig.savefig(p, dpi=130)
    plt.close(fig)
    paths.append(p)

    month_items = items_in_month(items, month)
    if month_items:
        # 2) category split for the chosen month
        cats = spend_by_category(month_items)
        fig, ax = plt.subplots(figsize=(7, 4))
        names = [c for c, _ in cats][::-1]
        totals = [t for _, t in cats][::-1]
        ax.barh(names, totals, color="#27ae60")
        ax.set_title(f"Where the money went - {month}")
        ax.set_xlabel(f"Spent ({CURRENCY.strip()})")
        fig.tight_layout()
        p = EXPORT_DIR / f"chart_categories_{month}.png"
        fig.savefig(p, dpi=130)
        plt.close(fig)
        paths.append(p)

        # 3) running total through the month
        ordered = sorted(month_items, key=lambda i: (i.date, i.id))
        days, running, total = [], [], 0.0
        for it in ordered:
            total += it.total
            days.append(int(it.date[8:]))
            running.append(total)
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.step(days, running, where="post", color="#8e44ad", linewidth=2)
        ax.axhline(budget, color="#c0392b", linestyle="--", label="Budget")
        ax.set_title(f"Running total - {month}")
        ax.set_xlabel("Day of month")
        ax.set_ylabel(f"Cumulative ({CURRENCY.strip()})")
        ax.legend()
        fig.tight_layout()
        p = EXPORT_DIR / f"chart_running_total_{month}.png"
        fig.savefig(p, dpi=130)
        plt.close(fig)
        paths.append(p)

    return paths, None
