import json
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
HTML_OUTPUT_DIR = DATA_DIR / "saved_html"
CSV_OUTPUT_DIR = DATA_DIR / "machine_csv"
STORE_LIST_PATH = DATA_DIR / "store_list.csv"
CONFIG_PATH = BASE_DIR / "app_config.json"

DEFAULT_CONFIG = {
    "store_list_path": str(STORE_LIST_PATH),
    "html_output_dir": str(HTML_OUTPUT_DIR),
    "csv_output_dir": str(CSV_OUTPUT_DIR),
}


def _normalize_non_empty_string(value):
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def ensure_default_directories():
    DATA_DIR.mkdir(exist_ok=True)
    HTML_OUTPUT_DIR.mkdir(exist_ok=True)
    CSV_OUTPUT_DIR.mkdir(exist_ok=True)


def load_config():
    ensure_default_directories()
    config = DEFAULT_CONFIG.copy()

    if CONFIG_PATH.exists():
        try:
            with CONFIG_PATH.open("r", encoding="utf-8") as file:
                saved = json.load(file)
            if isinstance(saved, dict):
                for key in DEFAULT_CONFIG:
                    value = _normalize_non_empty_string(saved.get(key))
                    if value:
                        config[key] = value
        except Exception:
            pass

    return config


def save_config(config):
    ensure_default_directories()
    merged = DEFAULT_CONFIG.copy()
    for key in DEFAULT_CONFIG:
        value = _normalize_non_empty_string(config.get(key))
        if value:
            merged[key] = value

    with CONFIG_PATH.open("w", encoding="utf-8") as file:
        json.dump(merged, file, ensure_ascii=False, indent=2)

    return merged


def ensure_config_file():
    ensure_default_directories()
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)


def sanitize_filename(name):
    value = str(name or "").strip()
    value = re.sub(r'[\\/*?:"<>|]', "", value)
    return value or "store"


def get_store_subdir(store_name, existing_directory=""):
    existing_directory = str(existing_directory or "").strip()
    if existing_directory:
        return Path(existing_directory.rstrip("\\/")).name or sanitize_filename(store_name)
    return sanitize_filename(store_name)


def resolve_store_html_directory(store_name, existing_directory, html_output_dir):
    html_root = str(html_output_dir or "").strip()
    if not html_root:
        return str(existing_directory or "").strip()
    return str(Path(html_root) / get_store_subdir(store_name, existing_directory))
