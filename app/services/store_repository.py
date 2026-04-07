from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

from config_manager import ensure_config_file, load_config, resolve_store_html_directory, sanitize_filename


STORE_COLUMNS = ("store_url", "data_directory", "store_name", "last_update")


@dataclass
class StoreRecord:
    name: str
    url: str
    directory: str
    original_directory: str


def get_store_list_path() -> Path:
    ensure_config_file()
    return Path(load_config()["store_list_path"])


def read_store_csv() -> pd.DataFrame:
    store_list_path = get_store_list_path()
    if not store_list_path.exists():
        raise FileNotFoundError(f"store_list.csv が見つかりません: {store_list_path}")

    for encoding in ("utf-8", "utf-8-sig", "cp932"):
        try:
            return pd.read_csv(store_list_path, encoding=encoding)
        except Exception:
            continue

    raise RuntimeError("store_list.csv の読み込みに失敗しました（encoding不一致）")


def write_store_csv(df: pd.DataFrame) -> None:
    get_store_list_path().parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(get_store_list_path(), index=False, encoding="utf-8-sig")


def get_store_name_column(df: pd.DataFrame) -> str | None:
    if "store_name" in df.columns:
        return "store_name"
    if "name" in df.columns:
        return "name"
    return None


def get_store_url_column(df: pd.DataFrame) -> str | None:
    if "store_url" in df.columns:
        return "store_url"
    if "url" in df.columns:
        return "url"
    return None


def get_store_directory_column(df: pd.DataFrame) -> str | None:
    if "data_directory" in df.columns:
        return "data_directory"
    if "directory" in df.columns:
        return "directory"
    return None


def ensure_store_columns(df: pd.DataFrame) -> pd.DataFrame:
    for column in STORE_COLUMNS:
        if column not in df.columns:
            df[column] = ""
    return df


def normalize_store_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = ensure_store_columns(df.copy())
    name_column = get_store_name_column(df) or "store_name"
    url_column = get_store_url_column(df) or "store_url"
    directory_column = get_store_directory_column(df) or "data_directory"

    df["store_name"] = df[name_column].fillna("").astype(str).str.strip()
    df["store_url"] = df[url_column].fillna("").astype(str).str.strip()
    df["data_directory"] = df[directory_column].fillna("").astype(str).str.strip()
    df["last_update"] = df["last_update"].fillna("").astype(str)
    return df


def apply_store_paths(df: pd.DataFrame, config: dict) -> list[dict]:
    normalized = normalize_store_dataframe(df)
    html_output_dir = config["html_output_dir"]
    stores = []

    for i, (_, row) in enumerate(normalized.iterrows(), start=1):
        name = row["store_name"] or f"店舗{i}"
        url = row["store_url"]
        original_directory = row["data_directory"]
        resolved_directory = resolve_store_html_directory(name, original_directory, html_output_dir)
        stores.append(
            StoreRecord(
                name=str(name),
                url=str(url),
                directory=str(resolved_directory),
                original_directory=str(original_directory),
            ).__dict__
        )

    return stores


def load_stores() -> list[dict]:
    config = load_config()
    df = read_store_csv()
    return apply_store_paths(df, config)


def is_valid_store_url(value: str) -> bool:
    parsed = urlparse(str(value or "").strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def add_store(store_name: str, store_url: str) -> dict:
    df = normalize_store_dataframe(read_store_csv())
    existing_names = set(df["store_name"].fillna("").astype(str).str.strip())
    if store_name in existing_names:
        raise ValueError(f"同名の店舗がすでに存在します: {store_name}")

    config = load_config()
    data_directory = resolve_store_html_directory(
        sanitize_filename(store_name),
        "",
        config["html_output_dir"],
    )

    new_row = {column: "" for column in df.columns}
    new_row["store_name"] = store_name
    new_row["store_url"] = store_url
    new_row["data_directory"] = data_directory
    new_row["last_update"] = ""

    write_store_csv(pd.concat([df, pd.DataFrame([new_row])], ignore_index=True))
    stores = load_stores()
    return next(store for store in stores if store["name"] == store_name)


def delete_store(store_name: str) -> int:
    df = normalize_store_dataframe(read_store_csv())
    filtered_df = df[df["store_name"] != store_name].copy()
    deleted_count = len(df) - len(filtered_df)
    if deleted_count == 0:
        raise LookupError(f"削除対象の店舗が見つかりません: {store_name}")

    write_store_csv(filtered_df)
    return deleted_count


def update_store_url(store_name: str, store_url: str) -> dict:
    df = normalize_store_dataframe(read_store_csv())
    match_mask = df["store_name"] == store_name
    if not match_mask.any():
        raise LookupError(f"更新対象の店舗が見つかりません: {store_name}")

    df.loc[match_mask, "store_url"] = store_url
    write_store_csv(df)
    stores = load_stores()
    return next(store for store in stores if store["name"] == store_name)


def reorder_stores(order: list[str]) -> int:
    df = normalize_store_dataframe(read_store_csv())
    if not order:
        raise ValueError("並び順が不正です")

    df["__orig_index__"] = range(len(df))
    name_to_index = {str(row["store_name"]): idx for idx, (_, row) in enumerate(df.iterrows())}
    ordered_indices = [name_to_index[name] for name in order if name in name_to_index]
    remaining_indices = [idx for idx in df["__orig_index__"].tolist() if idx not in ordered_indices]
    final_indices = ordered_indices + remaining_indices
    df = df.iloc[final_indices].drop(columns=["__orig_index__"])
    write_store_csv(df)
    return len(ordered_indices)
