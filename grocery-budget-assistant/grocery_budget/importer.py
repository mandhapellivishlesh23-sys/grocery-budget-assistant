import csv
from datetime import datetime

from . import validation as v
from .config import ERROR_LOG

REQUIRED = ["name", "category", "price", "quantity", "date"]


class ImportProblem(Exception):
    """Raised when the file as a whole can't be used."""


def import_csv(path, tracker, error_log=ERROR_LOG):
    """Adds valid rows to the tracker. Bad rows are logged, not fatal."""
    added, duplicates, errors = 0, 0, []

    try:
        f = open(path, newline="", encoding="utf-8-sig")
    except OSError as err:
        raise ImportProblem(f"can't open file: {err.strerror or err}") from None

    with f:
        try:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise ImportProblem("file is empty")
            headers = {h.strip().lower(): h for h in reader.fieldnames if h}
            missing = [c for c in REQUIRED if c not in headers]
            if missing:
                raise ImportProblem("missing column(s): " + ", ".join(missing))

            for line_no, row in enumerate(reader, start=2):   # line 1 = header
                get = lambda col: row.get(headers[col])
                try:
                    name = v.clean_name(get("name"))
                    cat = v.clean_category(get("category"))
                    price = v.clean_price(get("price"))
                    qty = v.clean_quantity(get("quantity"))
                    day = v.clean_date(get("date"))
                except ValueError as err:
                    errors.append((line_no, str(err)))
                    continue
                if tracker.has_duplicate(name, price, qty, day):
                    duplicates += 1
                    continue
                tracker.add(name, cat, price, qty, day)
                added += 1
        except csv.Error as err:
            raise ImportProblem(f"file isn't valid CSV: {err}") from None

    if errors:
        try:
            with open(error_log, "a", encoding="utf-8") as log:
                log.write(f"--- import of {path} at {datetime.now():%Y-%m-%d %H:%M:%S} ---\n")
                for line_no, msg in errors:
                    log.write(f"row {line_no}: {msg}\n")
        except OSError:
            pass   # the log is a nice-to-have

    return {"added": added, "duplicates": duplicates, "errors": errors}
