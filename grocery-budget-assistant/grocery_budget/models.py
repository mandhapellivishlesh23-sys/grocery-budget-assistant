from dataclasses import dataclass

from .config import DEFAULT_BUDGET

CATEGORIES = [
    "produce", "dairy", "meat", "bakery", "pantry",
    "snacks", "beverages", "frozen", "household", "other",
]


@dataclass
class Item:
    id: int
    name: str
    category: str
    price: float      # price of ONE unit
    quantity: int
    date: str         # YYYY-MM-DD

    @property
    def total(self):
        return round(self.price * self.quantity, 2)

    @property
    def month(self):
        return self.date[:7]


class Tracker:
    """Holds the budget and the list of items while the program runs."""

    def __init__(self, budget=DEFAULT_BUDGET, items=None):
        self.budget = budget
        self.items = items if items is not None else []

    def next_id(self):
        return max((i.id for i in self.items), default=0) + 1

    def has_duplicate(self, name, price, quantity, date):
        for it in self.items:
            if (it.name.lower() == name.lower() and it.date == date
                    and it.price == price and it.quantity == quantity):
                return True
        return False

    def add(self, name, category, price, quantity, date):
        item = Item(self.next_id(), name, category, price, quantity, date)
        self.items.append(item)
        return item

    def remove(self, item_id):
        for idx, it in enumerate(self.items):
            if it.id == item_id:
                return self.items.pop(idx)
        return None
