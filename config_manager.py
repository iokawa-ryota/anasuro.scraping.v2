import json
import os
import re


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "app_config.json")

DEFAULT_CONFIG = {
    "store_list_path": r"D:\Users\Documents\python\saved_html\store_list.csv",
    "html_output_dir": r"D:\Users\Documents\python\saved_html",
    "csv_output_dir": r"G:\マイドライブ\machine-Excel",
}


def load_config():
    config = DEFAULT_CONFIG.copy()

    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
            if isinstance(saved, dict):
                for key in DEFAULT_CONFIG:
                    value = saved.get(key)
                    if isinstance(value, str) and value.strip():
                        config[key] = value.strip()
        except Exception:
            pass

    return config


def save_config(config):
    merged = DEFAULT_CONFIG.copy()
    for key in DEFAULT_CONFIG:
        value = config.get(key)
        if isinstance(value, str) and value.strip():
            merged[key] = value.strip()

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    return merged


def ensure_config_file():
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)


def sanitize_filename(name):
    value = str(name or "").strip()
    value = re.sub(r'[\\/*?:"<>|]', "", value)
    return value or "store"


def get_store_subdir(store_name, existing_directory=""):
    existing_directory = str(existing_directory or "").strip()
    if existing_directory:
        return os.path.basename(existing_directory.rstrip("\\/")) or sanitize_filename(store_name)
    return sanitize_filename(store_name)


def resolve_store_html_directory(store_name, existing_directory, html_output_dir):
    html_root = str(html_output_dir or "").strip()
    if not html_root:
        return str(existing_directory or "").strip()
    return os.path.join(html_root, get_store_subdir(store_name, existing_directory))
