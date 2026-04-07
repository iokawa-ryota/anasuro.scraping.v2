import argparse
import json
import os
import re
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

from config_manager import load_config, resolve_store_html_directory, sanitize_filename
from services.runtime_paths import COMPLETED_STORES_PATH, RUNTIME_DIR
from services.store_repository import normalize_store_dataframe, read_store_csv

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover - setup_check should catch this
    tqdm = None


RUNTIME_DIR.mkdir(exist_ok=True)


def parse_args():
    parser = argparse.ArgumentParser(description="保存済みHTMLから CSV を再生成します")
    parser.add_argument("--stores", nargs="*", default=None, help="対象店舗名を指定")
    return parser.parse_args()


def load_store_dataframe(selected_stores=None):
    config = load_config()
    df = normalize_store_dataframe(read_store_csv())
    if selected_stores:
        selected = {str(name).strip() for name in selected_stores if str(name).strip()}
        df = df[df["store_name"].isin(selected)].copy()
    return config, df.drop_duplicates(subset=["data_directory", "store_name"])


def build_rows_from_html(file_path, day):
    all_data = []
    with open(file_path, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "lxml")

    table = soup.find("table", {"id": "all_data_table"})
    if not table:
        return all_data

    rows = table.find_all("tr")[1:]
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 6:
            continue

        dai_name = cols[0].get_text(strip=True)
        dai_num = cols[1].get_text(strip=True).replace(",", "")
        game = cols[2].get_text(strip=True).replace(",", "")
        diff = cols[3].get_text(strip=True).replace(",", "").replace("+", "")
        bb = cols[4].get_text(strip=True)
        rb = cols[5].get_text(strip=True)

        try:
            game_int = int(game)
        except Exception:
            game_int = 0
        try:
            bb_int = int(bb)
        except Exception:
            bb_int = 0
        try:
            rb_int = int(rb)
        except Exception:
            rb_int = 0
        try:
            diff_int = int(diff)
        except Exception:
            diff_int = 0

        total = round(game_int / (bb_int + rb_int), 1) if (bb_int + rb_int) else 0
        big_per = round(game_int / bb_int, 1) if bb_int else 0
        reg_per = round(game_int / rb_int, 1) if rb_int else 0

        all_data.append(
            {
                "day": day,
                "dai_name": dai_name,
                "dai_num": int(dai_num) if dai_num.isdigit() else 0,
                "game": game_int,
                "difference": diff_int,
                "bb": bb_int,
                "rb": rb_int,
                "Total": total,
                "big_per": big_per,
                "reg_per": reg_per,
            }
        )

    return all_data


def process_store(row, config, processed_outputs):
    html_dir = resolve_store_html_directory(
        row["store_name"],
        row.get("data_directory", ""),
        config["html_output_dir"],
    )
    store_name = row["store_name"]
    safe_store_name = sanitize_filename(store_name)
    output_path = Path(config["csv_output_dir"]) / f"{safe_store_name}-slotdata.csv"

    if str(output_path) in processed_outputs:
        return store_name, False
    processed_outputs.add(str(output_path))

    all_data = []
    existing_days = set()
    latest_day = None
    if output_path.exists():
        try:
            existing_df = pd.read_csv(output_path)
            if "day" in existing_df.columns:
                existing_df["day"] = pd.to_datetime(existing_df["day"], errors="coerce")
                existing_days = set(existing_df["day"].dt.strftime("%Y-%m-%d").dropna())
                latest_day = existing_df["day"].max()
            print(f"[既存データあり] {output_path}")
        except Exception as error:
            print(f"[警告] 既存CSVの読み込みに失敗しました: {output_path} ({error})")
            existing_df = pd.DataFrame()
    else:
        existing_df = pd.DataFrame()

    html_dir_path = Path(html_dir)
    if not html_dir_path.exists():
        print(f"[情報] HTML 保存先が見つかりません: {html_dir_path}")
        return store_name, False

    html_files = [
        file.name
        for file in html_dir_path.iterdir()
        if file.is_file() and file.suffix == ".html" and re.search(r"\d{4}-\d{2}-\d{2}", file.name)
    ]
    file_day_map = {name: re.search(r"\d{4}-\d{2}-\d{2}", name).group(0) for name in html_files}
    new_files = [
        file
        for file, day in file_day_map.items()
        if day not in existing_days and (not latest_day or pd.to_datetime(day) > latest_day)
    ]
    new_files.sort()

    iterator = tqdm(new_files, desc=store_name[:20], unit="file") if tqdm else new_files
    for file_name in iterator:
        file_path = html_dir_path / file_name
        day = file_day_map[file_name]
        all_data.extend(build_rows_from_html(file_path, day))

    if not all_data:
        print(f"[情報] 新しいデータはありません: {html_dir_path}")
        return store_name, False

    df_result = pd.DataFrame(all_data)
    if not existing_df.empty:
        df_result = pd.concat([existing_df, df_result], ignore_index=True)
        if "day" in df_result.columns:
            df_result["day"] = pd.to_datetime(df_result["day"], errors="coerce")
        df_result = df_result.drop_duplicates(subset=["day", "dai_name", "dai_num"], keep="last").reset_index(drop=True)
    elif "day" in df_result.columns:
        df_result["day"] = pd.to_datetime(df_result["day"], errors="coerce")

    if "day" in df_result.columns:
        df_result["day"] = df_result["day"].dt.strftime("%Y-%m-%d")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_result.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[保存完了] {output_path}")
    return store_name, True


def run(selected_stores=None):
    config, df = load_store_dataframe(selected_stores)
    processed_outputs = set()
    completed_stores = []
    processed_stores = []

    for index, (_, row) in enumerate(df.iterrows()):
        if index > 0:
            print("")

        store_name, updated = process_store(row, config, processed_outputs)
        processed_stores.append(store_name)
        if updated:
            completed_stores.append(store_name)

    with open(COMPLETED_STORES_PATH, "w", encoding="utf-8") as file:
        json.dump(
            {
                "completed": completed_stores,
                "processed": processed_stores,
            },
            file,
            ensure_ascii=False,
            indent=2,
        )
    print(f"[完了] 処理完了店舗を保存しました: {COMPLETED_STORES_PATH}")
    return completed_stores, processed_stores


def main():
    args = parse_args()
    run(args.stores)


if __name__ == "__main__":
    main()
