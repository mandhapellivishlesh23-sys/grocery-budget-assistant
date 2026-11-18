import unittest

from grocery_budget import validation as v


class PriceTests(unittest.TestCase):
    def test_normal_and_currency_junk(self):
        self.assertEqual(v.clean_price("12.5"), 12.5)
        self.assertEqual(v.clean_price("Rs. 1,250"), 1250.0)

    def test_bad_prices(self):
        for bad in ["", "abc", "-5", "0", "nan", "inf", "999999999"]:
            with self.assertRaises(ValueError, msg=bad):
                v.clean_price(bad)

    def test_boundaries(self):
        self.assertEqual(v.clean_price("0.01"), 0.01)
        self.assertEqual(v.clean_price("100000"), 100000.0)


class QuantityTests(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(v.clean_quantity("3"), 3)
        self.assertEqual(v.clean_quantity("4.0"), 4)

    def test_bad(self):
        for bad in ["", "0", "1.5", "1000", "x", "-2"]:
            with self.assertRaises(ValueError, msg=bad):
                v.clean_quantity(bad)


class OtherTests(unittest.TestCase):
    def test_dates(self):
        self.assertEqual(v.clean_date("2026-02-03"), "2026-02-03")
        for bad in ["", "03/02/2026", "2026-13-01", "2999-01-01", "1990-01-01"]:
            with self.assertRaises(ValueError, msg=bad):
                v.clean_date(bad)

    def test_names(self):
        self.assertEqual(v.clean_name("  green   tea "), "Green tea")
        for bad in ["", "   ", "1234", "x" * 41]:
            with self.assertRaises(ValueError, msg=bad):
                v.clean_name(bad)

    def test_category_by_number(self):
        self.assertEqual(v.clean_category("2"), "dairy")
        with self.assertRaises(ValueError):
            v.clean_category("sauces")

    def test_month(self):
        self.assertEqual(v.clean_month("2026-11"), "2026-11")
        with self.assertRaises(ValueError):
            v.clean_month("2026-13")
