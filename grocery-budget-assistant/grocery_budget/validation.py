"""All the input checks live here so the menu and the CSV importer
follow exactly the same rules."""
import math
import re
from datetime import date, datetime

from .models import CATEGORIES

MIN_PRICE, MAX_PRICE = 0.01, 100000
MIN_QTY, MAX_QTY = 1, 999
MAX_NAME_LEN = 40


def clean_name(raw):
    name = " ".join(str(raw or "").split())      # squash weird spacing
    if not name:
        raise ValueError("name can't be blank")
    if len(name) > MAX_NAME_LEN:
        raise ValueError(f"name is too long (max {MAX_NAME_LEN} characters)")
    if not any(ch.isalpha() for ch in name):
        raise ValueError("name needs at least one letter")
    return name[0].upper() + name[1:]


def clean_category(raw):
    cat = str(raw or "").strip().lower()
    if cat.isdigit() and 1 <= int(cat) <= len(CATEGORIES):
        return CATEGORIES[int(cat) - 1]          # allow picking by number
    if cat not in CATEGORIES:
        raise ValueError("unknown category '%s' (pick one of: %s)"
                         % (raw, ", ".join(CATEGORIES)))
    return cat


def clean_price(raw):
    text = str(raw or "").strip().lower()
    for junk in ("rs.", "rs", "inr", "₹", "$", ","):
        text = text.replace(junk, "")
    text = text.strip()
    if not text:
        raise ValueError("price can't be blank")
    try:
        value = float(text)
    except ValueError:
        raise ValueError(f"'{raw}' is not a number") from None
    if not math.isfinite(value):
        raise ValueError("price must be a real number")
    if value < MIN_PRICE:
        raise ValueError(f"price must be at least {MIN_PRICE}")
    if value > MAX_PRICE:
        raise ValueError(f"price can't be above {MAX_PRICE:,}")
    return round(value, 2)


def clean_quantity(raw):
    text = str(raw or "").strip()
    if not text:
        raise ValueError("quantity can't be blank")
    try:
        value = float(text)
    except ValueError:
        raise ValueError(f"'{raw}' is not a number") from None
    if not math.isfinite(value) or value != int(value):
        raise ValueError("quantity must be a whole number")
    value = int(value)
    if not MIN_QTY <= value <= MAX_QTY:
        raise ValueError(f"quantity must be between {MIN_QTY} and {MAX_QTY}")
    return value


def clean_date(raw):
    text = str(raw or "").strip()
    try:
        d = datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"'{raw}' isn't a valid date, use YYYY-MM-DD") from None
    if d > date.today():
        raise ValueError("date is in the future")
    if d.year < 2000:
        raise ValueError("date is before 2000, that looks like a typo")
    return d.isoformat()


def clean_month(raw):
    text = str(raw or "").strip()
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", text):
        raise ValueError("month should look like 2026-11")
    return text


def clean_budget(raw):
    value = clean_price(raw)
    if value < 1:
        raise ValueError("budget should be at least 1")
    return value


def clean_item_id(raw):
    text = str(raw or "").strip()
    if not text.isdigit():
        raise ValueError("item id must be a positive whole number")
    return int(text)
