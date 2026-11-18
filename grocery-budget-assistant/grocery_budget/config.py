from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
EXPORT_DIR = ROOT / "exports"

DATA_FILE = DATA_DIR / "grocery_data.json"
SAMPLE_CSV = DATA_DIR / "sample_items.csv"
ERROR_LOG = DATA_DIR / "import_errors.log"

# Change this if you prefer something else ("$", "EUR ", ...)
CURRENCY = "Rs "

DEFAULT_BUDGET = 6000.00     # monthly budget
WARN_AT = 0.80               # warn once 80% of the budget is gone
PAGE_SIZE = 10               # rows per page in the item table
