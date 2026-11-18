import os
import sys
import webbrowser
from datetime import date
from pathlib import Path

from . import logic, plotting, reports, storage
from . import validation as v
from .config import CURRENCY, PAGE_SIZE, SAMPLE_CSV
from .importer import ImportProblem, import_csv
from .models import CATEGORIES

# ---------- colours (turned off if the terminal can't handle them) ----------

USE_COLOUR = False
CODES = {"red": "31", "green": "32", "yellow": "33", "cyan": "36", "bold": "1", "dim": "2"}


def setup_colour():
    global USE_COLOUR
    if os.environ.get("NO_COLOR") or not sys.stdout.isatty():
        return
    if os.name == "nt":
        os.system("")            # nudges Windows 10+ consoles into ANSI mode
    USE_COLOUR = True


def paint(text, colour):
    if not USE_COLOUR:
        return text
    return f"\033[{CODES[colour]}m{text}\033[0m"


def say_error(msg):
    print(paint("  ! " + msg, "red"))


def say_ok(msg):
    print(paint("  OK " + msg, "green"))


LEVEL_COLOUR = {"OK": "green", "WARNING": "yellow", "OVER": "red"}

# ---------- input helpers ----------


def ask(label, cleaner, default=None):
    """Keeps asking until cleaner() accepts the answer."""
    while True:
        raw = input(f"  {label}: ").strip()
        if raw == "" and default is not None:
            return default
        try:
            return cleaner(raw)
        except ValueError as err:
            say_error(str(err))


def ask_optional(label, cleaner):
    """Blank is allowed (means 'skip'); anything else must be valid."""
    while True:
        raw = input(f"  {label}: ").strip()
        if raw == "":
            return ""
        try:
            return cleaner(raw)
        except ValueError as err:
            say_error(str(err))


def confirm(question):
    return input(f"  {question} (y/n): ").strip().lower() in ("y", "yes")


def pick_month(tracker):
    today_month = date.today().strftime("%Y-%m")
    months = logic.months_present(tracker.items)
    default = today_month if today_month in months or not months else months[-1]
    return ask(f"Month (YYYY-MM) [{default}]", v.clean_month, default=default)


# ---------- display helpers ----------

def banner():
    line = "=" * 46
    print(paint(line, "cyan"))
    print(paint("   GROCERY BUDGET ASSISTANT", "bold"))
    print("   track it, cap it, stop overspending")
    print(paint(line, "cyan"))


def print_table(items):
    head = f"{'ID':>3}  {'Date':<10}  {'Item':<22} {'Category':<10} {'Price':>9} {'Qty':>4} {'Total':>11}"
    print(paint(head, "bold"))
    print("-" * len(head))
    for it in items:
        name = it.name if len(it.name) <= 22 else it.name[:21] + "~"
        print(f"{it.id:>3}  {it.date:<10}  {name:<22} {it.category:<10} "
              f"{it.price:>9,.2f} {it.quantity:>4} {it.total:>11,.2f}")


def show_paged(items):
    if not items:
        print("  Nothing to show.")
        return
    for start in range(0, len(items), PAGE_SIZE):
        print_table(items[start:start + PAGE_SIZE])
        shown = min(start + PAGE_SIZE, len(items))
        print(f"  ({shown} of {len(items)})")
        if shown < len(items):
            if input("  Enter = next page, q = stop: ").strip().lower() == "q":
                break


def print_status(s):
    colour = LEVEL_COLOUR[s["level"]]
    print(f"  Budget : {reports.money(s['budget'])}")
    print(f"  Spent  : {reports.money(s['spent'])}  ({s['pct']:.1f}%)")
    print(f"  Left   : {reports.money(s['remaining'])}")
    print("  " + paint(reports.bar(s["pct"]), colour))
    if s["level"] == "OVER":
        print(paint(f"  OVER BUDGET by {reports.money(-s['remaining'])}", "red"))
    elif s["level"] == "WARNING":
        print(paint("  Careful - you've used most of this month's budget.", "yellow"))
    else:
        print(paint("  On track.", "green"))


# ---------- menu actions ----------

def add_item(tracker):
    print("\n  -- Add an item --")
    name = ask("Item name", v.clean_name)
    print("  Categories: " + ", ".join(f"{n}={c}" for n, c in enumerate(CATEGORIES, 1)))
    category = ask("Category (name or number)", v.clean_category)
    price = ask("Price per unit", v.clean_price)
    qty = ask("Quantity [1]", v.clean_quantity, default=1)
    today = date.today().isoformat()
    day = ask(f"Date YYYY-MM-DD [{today}]", v.clean_date, default=today)

    if tracker.has_duplicate(name, price, qty, day):
        if not confirm("Looks like you already entered this exact item that day. Add anyway?"):
            print("  Skipped.")
            return
    item = tracker.add(name, category, price, qty, day)
    say_ok(f"Added #{item.id}: {item.name} = {reports.money(item.total)}")

    status = logic.budget_status(tracker.items, tracker.budget, item.month)
    if status["level"] == "OVER":
        print(paint(f"  WARNING: {item.month} is now over budget by "
                    f"{reports.money(-status['remaining'])}!", "red"))
    elif status["level"] == "WARNING":
        print(paint(f"  Heads up: {status['pct']:.0f}% of the {item.month} budget used.", "yellow"))
    storage.save_state(tracker)


def view_items(tracker):
    print()
    show_paged(sorted(tracker.items, key=lambda i: (i.date, i.id)))


def search_items(tracker):
    print("\n  -- Search (leave a field blank to skip it) --")
    keyword = input("  Keyword in name: ").strip()
    category = ask_optional("Category", v.clean_category)
    start = ask_optional("From date YYYY-MM-DD", v.clean_date)
    end = ask_optional("To date YYYY-MM-DD", v.clean_date)
    if start and end and start > end:
        start, end = end, start
        print("  (dates were the wrong way round, swapped them)")
    results = logic.search(tracker.items, keyword, category, start, end)
    print(f"\n  {len(results)} match(es)")
    show_paged(results)
    if results:
        print(f"  Combined total: {reports.money(sum(i.total for i in results))}")


def remove_item(tracker):
    item_id = ask("Id of the item to remove", v.clean_item_id)
    target = next((i for i in tracker.items if i.id == item_id), None)
    if target is None:
        say_error(f"no item with id {item_id}")
        return
    print_table([target])
    if confirm("Delete this?"):
        tracker.remove(item_id)
        storage.save_state(tracker)
        say_ok("Removed.")


def set_budget(tracker):
    print(f"\n  Current monthly budget: {reports.money(tracker.budget)}")
    tracker.budget = ask("New monthly budget", v.clean_budget)
    storage.save_state(tracker)
    say_ok(f"Budget is now {reports.money(tracker.budget)}")


def budget_check(tracker):
    month = pick_month(tracker)
    s = logic.budget_status(tracker.items, tracker.budget, month)
    print(f"\n  -- Budget check for {month} --")
    print_status(s)
    hit = logic.overspend_point(tracker.items, tracker.budget, month)
    if hit:
        it, running = hit
        print(f"  The budget was crossed on {it.date} when '{it.name}' pushed the total to "
              f"{reports.money(running)}.")
    proj = logic.projection(tracker.items, tracker.budget, month)
    if proj:
        msg = f"  At this pace you'll spend about {reports.money(proj['projected'])} this month."
        print(paint(msg, "red" if proj["will_exceed"] else "green"))
    for it, why in logic.find_anomalies(tracker.items, tracker.budget):
        if it.month == month:
            print(paint(f"  ? #{it.id} {it.name}: {why}", "yellow"))


def summary_report(tracker):
    if not tracker.items:
        print("  No items yet.")
        return
    month = pick_month(tracker)
    s = logic.summarize(tracker.items, tracker.budget, month)
    print()
    print(reports.render_text(s))


def charts(tracker):
    month = pick_month(tracker)
    paths, err = plotting.make_charts(tracker.items, tracker.budget, month)
    if err:
        say_error(err)
        return
    for p in paths:
        say_ok(f"saved {p}")
    if confirm("Open the first chart now?"):
        webbrowser.open(Path(paths[0]).resolve().as_uri())


def export_report(tracker):
    if not tracker.items:
        print("  No items yet.")
        return
    month = pick_month(tracker)
    s = logic.summarize(tracker.items, tracker.budget, month)
    paths = reports.export_all(s, tracker.items)
    for kind, p in paths.items():
        say_ok(f"{kind:<8} -> {p}")


def import_file(tracker, path=None):
    if path is None:
        raw = input("  Path to CSV file: ").strip().strip('"').strip("'")
        path = Path(raw)
    try:
        result = import_csv(path, tracker)
    except ImportProblem as err:
        say_error(str(err))
        return
    say_ok(f"{result['added']} added, {result['duplicates']} duplicate(s) skipped, "
           f"{len(result['errors'])} row(s) rejected")
    for line_no, msg in result["errors"][:8]:
        print(f"    row {line_no}: {msg}")
    if len(result["errors"]) > 8:
        print(f"    ...and {len(result['errors']) - 8} more (see data/import_errors.log)")
    if result["added"]:
        storage.save_state(tracker)


def load_sample(tracker):
    if not SAMPLE_CSV.exists():
        say_error("sample file is missing from the data folder")
        return
    import_file(tracker, SAMPLE_CSV)


MENU = [
    ("1", "Add grocery item", add_item),
    ("2", "View all items", view_items),
    ("3", "Search / filter", search_items),
    ("4", "Remove an item", remove_item),
    ("5", "Set monthly budget", set_budget),
    ("6", "Budget check", budget_check),
    ("7", "Summary report", summary_report),
    ("8", "Make charts (PNG)", charts),
    ("9", "Export report (md / txt / csv)", export_report),
    ("10", "Import items from CSV", import_file),
    ("11", "Load sample data", load_sample),
    ("0", "Exit", None),
]


def run():
    setup_colour()
    tracker, notes = storage.load_state()
    banner()
    for n in notes:
        print(paint("  note: " + n, "dim"))
    today_month = date.today().strftime("%Y-%m")
    if tracker.items:
        s = logic.budget_status(tracker.items, tracker.budget, today_month)
        print(f"\n  This month so far: {reports.money(s['spent'])} of "
              f"{reports.money(tracker.budget)}  ->  "
              + paint(s["level"], LEVEL_COLOUR[s["level"]]))

    actions = {key: fn for key, _, fn in MENU}
    while True:
        print()
        for key, label, _ in MENU:
            print(f"  {key:>2}) {label}")
        try:
            choice = input("\n  Choose: ").strip()
            if choice == "0":
                break
            action = actions.get(choice)
            if action is None:
                say_error("pick a number from the menu")
                continue
            action(tracker)
        except (KeyboardInterrupt, EOFError):
            print()
            break
        except Exception as err:     # last line of defence, never lose the session
            say_error(f"something went wrong ({type(err).__name__}: {err}). Your data is safe.")
    storage.save_state(tracker)
    print("\n  Saved. See you next time!")
