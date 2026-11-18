import json
import os
from dataclasses import asdict
from datetime import datetime

from . import validation as v
from .config import DATA_FILE, DEFAULT_BUDGET
from .models import Item, Tracker


def save_state(tracker, path=DATA_FILE):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "budget": tracker.budget,
        "items": [asdict(i) for i in tracker.items],
    }
    # write to a temp file first so a crash mid-save can't wreck the real one
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp, path)


def _start_fresh(path):
    tracker = Tracker()
    save_state(tracker, path)
    return tracker


def load_state(path=DATA_FILE):
    """Returns (tracker, warnings). Never raises on a bad file."""
    warnings = []

    if not path.exists():
        return _start_fresh(path), ["No data file yet, starting fresh."]

    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict) or not isinstance(raw.get("items"), list):
            raise ValueError("unexpected layout")
    except (json.JSONDecodeError, ValueError, OSError):
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = path.with_name(f"{path.stem}.corrupt-{stamp}{path.suffix}")
        try:
            path.rename(backup)
            note = f"Old file kept as {backup.name}."
        except OSError:
            note = "Couldn't back up the old file."
        warnings.append("Data file was unreadable. " + note + " Starting fresh.")
        return _start_fresh(path), warnings

    try:
        budget = v.clean_budget(raw.get("budget", DEFAULT_BUDGET))
    except ValueError:
        budget = DEFAULT_BUDGET
        warnings.append("Saved budget looked wrong, reset to the default.")

    items, bad, seen_ids = [], 0, set()
    for entry in raw["items"]:
        try:
            item_id = int(entry["id"])
            if item_id in seen_ids:
                raise ValueError("duplicate id")
            item = Item(
                id=item_id,
                name=v.clean_name(entry["name"]),
                category=v.clean_category(entry["category"]),
                price=v.clean_price(entry["price"]),
                quantity=v.clean_quantity(entry["quantity"]),
                date=v.clean_date(entry["date"]),
            )
        except (KeyError, TypeError, ValueError):
            bad += 1
            continue
        seen_ids.add(item_id)
        items.append(item)

    if bad:
        warnings.append(f"Skipped {bad} damaged record(s) while loading.")
    return Tracker(budget, items), warnings
