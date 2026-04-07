#!/usr/bin/env python3
"""
セットアップ・テストスクリプト

以下の処理を行います：
1. 必要なパッケージの確認と不足分のインストール
2. 設定ファイルの確認
3. デフォルトの store_list.csv の準備
4. 起動手順の案内
"""

import csv
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config_manager import DEFAULT_CONFIG, ensure_config_file, load_config


def check_python_version():
    print("[CHECK] Python version...")
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"[OK] Python {version}")

    if sys.version_info < (3, 10):
        print("[WARN] Python 3.10 or newer is recommended")
        return False
    return True


def check_packages():
    print("\n[CHECK] Python packages...")

    required_packages = {
        "flask": "Flask",
        "pandas": "pandas",
        "selenium": "selenium",
        "bs4": "beautifulsoup4",
        "undetected_chromedriver": "undetected-chromedriver",
        "tqdm": "tqdm",
        "lxml": "lxml",
    }

    missing_packages = []
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"[OK] {package_name} is installed")
        except ImportError:
            print(f"[MISSING] {package_name}")
            missing_packages.append(package_name)

    if not missing_packages:
        return True

    print("\n[INSTALL] Installing missing packages...")
    print(f"   {', '.join(missing_packages)}")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade"] + missing_packages)
        print("[OK] Installation complete")
        return True
    except subprocess.CalledProcessError as error:
        print(f"[ERROR] Installation failed: {error}")
        return False


def check_config_files():
    print("\n[CHECK] Project files...")

    required_files = {
        "app/app.py": "Flask バックエンド",
        "app/index.html": "フロントエンド UI",
        "app/static/app.js": "フロントエンド JavaScript",
        "app/static/styles.css": "フロントエンド CSS",
        "app/anasuro_selective.py": "スクレイピング処理",
        "app/offline_scraping.py": "CSV 整形処理",
        "Start.bat": "起動バッチ",
    }

    all_exist = True
    for filename, description in required_files.items():
        path = BASE_DIR / filename
        if path.exists():
            print(f"[OK] {filename} ({description}) - {path.stat().st_size:,} bytes")
        else:
            print(f"[MISSING] {filename} ({description})")
            all_exist = False
    return all_exist


def ensure_sample_store_list(store_list_path: Path):
    store_list_path.parent.mkdir(parents=True, exist_ok=True)
    if store_list_path.exists():
        return

    rows = [
        {
            "store_name": "店舗A - サンプル",
            "store_url": "https://example.com/store-a",
            "data_directory": str(store_list_path.parent / "店舗A-サンプル"),
            "last_update": "",
        },
        {
            "store_name": "店舗B - サンプル",
            "store_url": "https://example.com/store-b",
            "data_directory": str(store_list_path.parent / "店舗B-サンプル"),
            "last_update": "",
        },
    ]
    with store_list_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["store_name", "store_url", "data_directory", "last_update"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"[OK] Sample file created: {store_list_path}")


def check_store_list():
    print("\n[CHECK] store_list.csv...")
    ensure_config_file()
    config = load_config()
    store_list_path = Path(config["store_list_path"])
    ensure_sample_store_list(store_list_path)

    try:
        import pandas as pd

        df = pd.read_csv(store_list_path, encoding="utf-8-sig")
        required_cols = {"store_name", "store_url", "data_directory"}
        actual_cols = set(df.columns)

        print(f"[OK] {store_list_path} exists")
        print(f"  Rows: {len(df)}")
        print(f"  Columns: {', '.join(df.columns)}")
        if not required_cols.issubset(actual_cols):
            print("[WARN] Required columns are missing")
            print(f"   Required: {required_cols}")
            print(f"   Actual: {actual_cols}")
            return False
        return True
    except Exception as error:
        print(f"[ERROR] Failed to read file: {error}")
        return False


def check_default_paths():
    print("\n[CHECK] Default config paths...")
    config = load_config()
    for key, value in config.items():
        path = Path(value)
        if key.endswith("_dir"):
            path.mkdir(parents=True, exist_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
        print(f"[OK] {key}: {value}")
    if config == DEFAULT_CONFIG:
        print("[INFO] Using repo-local default paths")
    return True


def print_summary():
    print("\n" + "=" * 60)
    print("Setup complete")
    print("=" * 60)
    print("\nUse one of the following commands:\n")
    print("  Start.bat")
    print("  python app\\app.py")
    print("\nThen open this URL in your browser:\n")
    print("  http://localhost:5000\n")
    print("Default data folders are created under:")
    print(f"  {BASE_DIR / 'data'}")
    print("=" * 60)


def main():
    print("\n" + "=" * 60)
    print("Slot Store Scraper Web UI - Setup")
    print("=" * 60 + "\n")

    checks = [
        ("Python バージョン確認", check_python_version),
        ("パッケージ確認", check_packages),
        ("設定ファイル確認", check_config_files),
        ("デフォルトパス確認", check_default_paths),
        ("店舗リスト確認", check_store_list),
    ]

    results = []
    for check_name, check_func in checks:
        try:
            results.append((check_name, check_func()))
        except Exception as error:
            print(f"[ERROR] Unexpected error in {check_name}: {error}")
            results.append((check_name, False))

    print("\n" + "=" * 60)
    print("Results:")
    print("=" * 60)
    for check_name, result in results:
        print(f"{'[OK]' if result else '[NG]'}: {check_name}")

    if all(result for _, result in results):
        print_summary()
        return

    print("\n[WARN] Some checks failed")
    print("Review the messages above and fix the reported issues")
    sys.exit(1)


if __name__ == "__main__":
    main()
