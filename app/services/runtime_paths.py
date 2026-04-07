from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
RUNTIME_DIR = BASE_DIR / "runtime"
TEMP_STORE_LIST_PATH = RUNTIME_DIR / "temp_store_list.csv"
SCRAPING_SCRIPT_PATH = BASE_DIR / "anasuro_selective.py"
OFFLINE_FORMAT_SCRIPT_PATH = BASE_DIR / "offline_scraping.py"
LOG_FILE = RUNTIME_DIR / "scraping_log.json"
COMPLETED_STORES_PATH = RUNTIME_DIR / "completed_stores.json"

RUNTIME_DIR.mkdir(exist_ok=True)
