import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from grocery_budget import logic, storage
from grocery_budget.importer import ImportProblem, import_csv
from grocery_budget.models import Tracker


def make_tracker():
    t = Tracker(budget=1000)
    t.add("Milk", "dairy", 50, 4, "2026-10-02")      # 200
    t.add("Rice", "pantry", 500, 1, "2026-10-05")    # 500
    t.add("Oil", "pantry", 400, 1, "2026-10-09")     # 400 -> crosses 1000
    t.add("Milk", "dairy", 50, 2, "2026-11-02")      # 100
    return t


class BudgetTests(unittest.TestCase):
    def test_over_budget(self):
        t = make_tracker()
        s = logic.budget_status(t.items, 1000, "2026-10")
        self.assertEqual(s["spent"], 1100)
        self.assertEqual(s["level"], "OVER")
        self.assertEqual(s["remaining"], -100)

    def test_ok_and_warning(self):
        t = make_tracker()
        self.assertEqual(logic.budget_status(t.items, 1000, "2026-11")["level"], "OK")
        self.assertEqual(logic.budget_status(t.items, 120, "2026-11")["level"], "WARNING")

    def test_exact_budget_is_not_over(self):
        t = Tracker(budget=100)
        t.add("Thing", "other", 100, 1, "2026-10-01")
        self.assertEqual(logic.budget_status(t.items, 100, "2026-10")["level"], "WARNING")

    def test_overspend_point(self):
        t = make_tracker()
        item, running = logic.overspend_point(t.items, 1000, "2026-10")
        self.assertEqual(item.name, "Oil")
        self.assertEqual(running, 1100)
        self.assertIsNone(logic.overspend_point(t.items, 1000, "2026-11"))

    def test_projection_only_for_current_month(self):
        t = make_tracker()
        self.assertIsNone(logic.projection(t.items, 1000, "2026-10", today=date(2026, 11, 10)))
        p = logic.projection(t.items, 150, "2026-11", today=date(2026, 11, 10))
        self.assertTrue(p["will_exceed"])

    def test_empty_month(self):
        s = logic.summarize([], 1000, "2026-10", today=date(2026, 11, 18))
        self.assertEqual(s["spent"], 0)
        self.assertEqual(s["avg_item_total"], 0)

    def test_search(self):
        t = make_tracker()
        self.assertEqual(len(logic.search(t.items, keyword="milk")), 2)
        self.assertEqual(len(logic.search(t.items, category="pantry")), 2)
        self.assertEqual(len(logic.search(t.items, start="2026-11-01")), 1)

    def test_anomaly_flags(self):
        t = Tracker(budget=6000)
        for d in range(1, 6):
            t.add(f"Item {chr(96 + d)}", "snacks", 20, 1, f"2026-10-0{d}")
        t.add("Fancy box", "snacks", 900, 1, "2026-10-09")
        t.add("Water", "beverages", 40, 24, "2026-10-10")
        reasons = [r for _, r in logic.find_anomalies(t.items, 6000)]
        self.assertTrue(any("median" in r for r in reasons))
        self.assertTrue(any("large quantity" in r for r in reasons))


class StorageTests(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "data.json"
            t = make_tracker()
            storage.save_state(t, path)
            loaded, warns = storage.load_state(path)
            self.assertEqual(len(loaded.items), 4)
            self.assertEqual(loaded.budget, 1000)
            self.assertEqual(warns, [])

    def test_missing_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "nope.json"
            t, warns = storage.load_state(path)
            self.assertEqual(t.items, [])
            self.assertTrue(path.exists())

    def test_corrupt_file_is_backed_up(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "data.json"
            path.write_text("{ this is not json", encoding="utf-8")
            t, warns = storage.load_state(path)
            self.assertEqual(t.items, [])
            self.assertEqual(len(list(Path(d).glob("data.corrupt-*"))), 1)

    def test_damaged_records_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "data.json"
            good = {"id": 1, "name": "Milk", "category": "dairy", "price": 50, "quantity": 1, "date": "2026-10-01"}
            bad = {"id": 2, "name": "", "category": "dairy", "price": -1, "quantity": 1, "date": "nope"}
            path.write_text(json.dumps({"budget": 500, "items": [good, bad]}), encoding="utf-8")
            t, warns = storage.load_state(path)
            self.assertEqual(len(t.items), 1)
            self.assertTrue(warns)


class ImportTests(unittest.TestCase):
    def test_row_errors_and_duplicates(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "in.csv"
            f.write_text(
                "name,category,price,quantity,date\n"
                "Milk,dairy,50,2,2026-10-01\n"
                "Milk,dairy,50,2,2026-10-01\n"
                "Bad,dairy,abc,1,2026-10-01\n"
                ",dairy,5,1,2026-10-01\n", encoding="utf-8")
            t = Tracker()
            res = import_csv(f, t, error_log=Path(d) / "err.log")
            self.assertEqual(res["added"], 1)
            self.assertEqual(res["duplicates"], 1)
            self.assertEqual([r for r, _ in res["errors"]], [4, 5])
            self.assertTrue((Path(d) / "err.log").exists())

    def test_missing_column_and_missing_file(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "in.csv"
            f.write_text("name,price\nMilk,5\n", encoding="utf-8")
            with self.assertRaises(ImportProblem):
                import_csv(f, Tracker(), error_log=Path(d) / "e.log")
            with self.assertRaises(ImportProblem):
                import_csv(Path(d) / "ghost.csv", Tracker(), error_log=Path(d) / "e.log")


if __name__ == "__main__":
    unittest.main()
