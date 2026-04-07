from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, request, send_from_directory

from config_manager import ensure_config_file, load_config, save_config
from services.job_service import get_job, get_recent_logs, start_format_job, start_scrape_job
from services.runtime_paths import TEMP_STORE_LIST_PATH
from services.store_repository import (
    add_store as add_store_record,
    delete_store as delete_store_record,
    is_valid_store_url,
    load_stores,
    normalize_store_dataframe,
    reorder_stores as reorder_store_records,
    update_store_url as update_store_url_record,
)


BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config["JSON_AS_ASCII"] = False

ensure_config_file()


@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/api/stores", methods=["GET"])
def get_stores():
    return jsonify(load_stores())


@app.route("/api/stores", methods=["POST"])
def add_store():
    try:
        data = request.get_json() or {}
        store_name = str(data.get("store_name") or "").strip()
        store_url = str(data.get("store_url") or "").strip()

        if not store_name:
            return jsonify({"error": "店舗名を入力してください"}), 400
        if not store_url:
            return jsonify({"error": "店舗URLを入力してください"}), 400
        if not is_valid_store_url(store_url):
            return jsonify({"error": "店舗URLの形式が不正です"}), 400

        added_store = add_store_record(store_name, store_url)
        return jsonify({"message": f"店舗を追加しました: {store_name}", "store": added_store})
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception as error:
        return jsonify({"error": f"店舗追加エラー: {error}"}), 500


@app.route("/api/stores/<path:store_name>", methods=["DELETE"])
def delete_store(store_name):
    try:
        target_name = str(store_name or "").strip()
        if not target_name:
            return jsonify({"error": "削除対象の店舗名が不正です"}), 400

        deleted_count = delete_store_record(target_name)
        return jsonify({"message": f"店舗を削除しました: {target_name}", "deleted_count": deleted_count})
    except LookupError as error:
        return jsonify({"error": str(error)}), 404
    except Exception as error:
        return jsonify({"error": f"店舗削除エラー: {error}"}), 500


@app.route("/api/stores/<path:store_name>", methods=["PATCH"])
def update_store_url(store_name):
    try:
        target_name = str(store_name or "").strip()
        data = request.get_json() or {}
        store_url = str(data.get("store_url") or "").strip()

        if not target_name:
            return jsonify({"error": "更新対象の店舗名が不正です"}), 400
        if not store_url:
            return jsonify({"error": "店舗URLを入力してください"}), 400
        if not is_valid_store_url(store_url):
            return jsonify({"error": "店舗URLの形式が不正です"}), 400

        updated_store = update_store_url_record(target_name, store_url)
        return jsonify({"message": f"店舗URLを更新しました: {target_name}", "store": updated_store})
    except LookupError as error:
        return jsonify({"error": str(error)}), 404
    except Exception as error:
        return jsonify({"error": f"店舗URL更新エラー: {error}"}), 500


@app.route("/api/stores/<path:store_name>/url", methods=["POST"])
def update_store_url_via_post(store_name):
    return update_store_url(store_name)


@app.route("/api/stores/reorder", methods=["POST"])
def reorder_stores():
    try:
        data = request.get_json() or {}
        order = data.get("order", [])
        reordered_count = reorder_store_records(order)
        return jsonify({"message": f"並び順を保存しました（{reordered_count} 件を並べ替え）"})
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception as error:
        return jsonify({"error": f"並び順保存エラー: {error}"}), 500


@app.route("/api/settings", methods=["GET"])
def get_settings():
    config = load_config()
    config["temp_store_list_path"] = str(TEMP_STORE_LIST_PATH.resolve())
    return jsonify(config)


@app.route("/api/settings", methods=["POST"])
def update_settings():
    try:
        data = request.get_json() or {}
        current_config = load_config()
        next_config = {
            "store_list_path": data.get("store_list_path") or current_config["store_list_path"],
            "html_output_dir": data.get("html_output_dir") or current_config["html_output_dir"],
            "csv_output_dir": data.get("csv_output_dir") or current_config["csv_output_dir"],
        }
        config = save_config(next_config)
        Path(config["html_output_dir"]).mkdir(parents=True, exist_ok=True)
        Path(config["csv_output_dir"]).mkdir(parents=True, exist_ok=True)
        return jsonify({"message": "設定を保存しました", "settings": config})
    except Exception as error:
        return jsonify({"error": f"設定保存エラー: {error}"}), 500


@app.route("/api/scrape", methods=["POST"])
def start_scraping():
    try:
        data = request.get_json() or {}
        selected_store_names = data.get("stores", [])
        test_mode = bool(data.get("test_mode"))

        if not selected_store_names:
            return jsonify({"error": "店舗が選択されていません"}), 400

        all_stores = pd.DataFrame(load_stores())
        selected_stores_df = all_stores[all_stores["name"].isin(selected_store_names)].copy()
        if selected_stores_df.empty:
            return jsonify({"error": "選択された店舗が見つかりません"}), 400

        selected_stores_df = selected_stores_df.rename(columns={"name": "store_name", "url": "store_url", "directory": "data_directory"})
        selected_stores_df = normalize_store_dataframe(selected_stores_df)
        TEMP_STORE_LIST_PATH.parent.mkdir(exist_ok=True)
        selected_stores_df.to_csv(TEMP_STORE_LIST_PATH, index=False, encoding="utf-8-sig")

        job = start_scrape_job(selected_store_names, test_mode=test_mode)
        return jsonify(
            {
                "message": job["message"],
                "job_id": job["job_id"],
                "status": job["status"],
                "test_mode": job["test_mode"],
                "status_url": f"/api/jobs/{job['job_id']}",
            }
        ), 202
    except Exception as error:
        return jsonify({"error": f"処理エラー: {error}"}), 500


@app.route("/api/format-offline", methods=["POST"])
def format_offline():
    try:
        job = start_format_job()
        return jsonify(
            {
                "message": job["message"],
                "job_id": job["job_id"],
                "status": job["status"],
                "status_url": f"/api/jobs/{job['job_id']}",
            }
        ), 202
    except Exception as error:
        return jsonify({"error": f"処理エラー: {error}", "completed_stores": []}), 500


@app.route("/api/jobs/<job_id>", methods=["GET"])
def get_job_status(job_id):
    job = get_job(job_id)
    if not job:
        return jsonify({"error": "ジョブが見つかりません"}), 404
    return jsonify(job)


@app.route("/api/logs", methods=["GET"])
def get_logs():
    try:
        return jsonify(get_recent_logs())
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@app.errorhandler(404)
def not_found(_error):
    return jsonify({"error": "Not Found"}), 404


@app.errorhandler(500)
def server_error(_error):
    return jsonify({"error": "Internal Server Error"}), 500


if __name__ == "__main__":
    print("=" * 50)
    print("スロット店舗スクレイピング Web UI")
    print("=" * 50)
    print("サーバーが起動しました")
    print("ブラウザで http://localhost:5000 にアクセスしてください")
    print("=" * 50)
    app.run(debug=False, host="localhost", port=5000)
