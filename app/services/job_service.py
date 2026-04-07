from __future__ import annotations

import json
import subprocess
import sys
import threading
import uuid
from datetime import datetime

from services.runtime_paths import (
    BASE_DIR,
    COMPLETED_STORES_PATH,
    LOG_FILE,
    OFFLINE_FORMAT_SCRIPT_PATH,
    SCRAPING_SCRIPT_PATH,
    TEMP_STORE_LIST_PATH,
)


_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()


def _utc_now():
    return datetime.now().isoformat()


def append_log(entry: dict) -> None:
    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def get_recent_logs(limit: int = 20) -> list[dict]:
    if not LOG_FILE.exists():
        return []

    logs = []
    with LOG_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            try:
                logs.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return logs[-limit:]


def _set_job(job_id: str, **fields) -> dict:
    with _jobs_lock:
        job = _jobs[job_id]
        job.update(fields)
        return dict(job)


def get_job(job_id: str) -> dict | None:
    with _jobs_lock:
        job = _jobs.get(job_id)
        return dict(job) if job else None


def create_job(job_type: str, stores: list[str] | None = None) -> dict:
    job_id = uuid.uuid4().hex
    job = {
        "job_id": job_id,
        "type": job_type,
        "status": "queued",
        "message": "ジョブを受け付けました",
        "output": "",
        "stores": stores or [],
        "test_mode": False,
        "completed_stores": [],
        "processed_stores": [],
        "created_at": _utc_now(),
        "started_at": None,
        "finished_at": None,
        "returncode": None,
    }
    with _jobs_lock:
        _jobs[job_id] = job
    return dict(job)


def _run_subprocess(script_path, timeout_seconds: int, extra_args: list[str] | None = None, extra_log: dict | None = None):
    command = [sys.executable, str(script_path)] + (extra_args or [])
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        encoding="utf-8",
        errors="replace",
        cwd=BASE_DIR,
    )
    output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    log_entry = {
        "timestamp": _utc_now(),
        "script": str(script_path.name),
        "command": command,
        "returncode": result.returncode,
        "output": output[-2000:],
    }
    if extra_log:
        log_entry.update(extra_log)
    append_log(log_entry)
    return result.returncode, output


def start_scrape_job(selected_store_names: list[str], test_mode: bool = False) -> dict:
    job = create_job("scrape", selected_store_names)
    _set_job(job["job_id"], test_mode=test_mode)

    def worker():
        running_message = f"{len(selected_store_names)} 個の店舗のスクレイピングを実行しています"
        if test_mode:
            running_message = f"{len(selected_store_names)} 個の店舗のテストスクレイピング（直近3日分）を実行しています"
        _set_job(
            job["job_id"],
            status="running",
            started_at=_utc_now(),
            message=running_message,
        )
        try:
            returncode, output = _run_subprocess(
                SCRAPING_SCRIPT_PATH,
                timeout_seconds=3600,
                extra_args=["--recent-days", "3"] if test_mode else [],
                extra_log={
                    "action": "scrape",
                    "selected_stores": selected_store_names,
                    "count": len(selected_store_names),
                    "test_mode": test_mode,
                    "temp_file": str(TEMP_STORE_LIST_PATH),
                },
            )
            status = "succeeded" if returncode == 0 else "failed"
            message = (
                f"{len(selected_store_names)} 個の店舗のスクレイピングを実行しました"
                if returncode == 0
                else "スクレイピングの起動に失敗しました"
            )
            if returncode == 0 and test_mode:
                message = f"{len(selected_store_names)} 個の店舗のテストスクレイピング（直近3日分）を実行しました"
            _set_job(
                job["job_id"],
                status=status,
                finished_at=_utc_now(),
                message=message,
                output=output[-4000:],
                returncode=returncode,
            )
        except subprocess.TimeoutExpired:
            _set_job(
                job["job_id"],
                status="failed",
                finished_at=_utc_now(),
                message="スクレイピングがタイムアウトしました",
                output="ジョブの実行がタイムアウトしました。",
                returncode=124,
            )
        except Exception as error:
            _set_job(
                job["job_id"],
                status="failed",
                finished_at=_utc_now(),
                message="スクレイピング実行エラー",
                output=str(error),
                returncode=1,
            )

    threading.Thread(target=worker, daemon=True).start()
    return get_job(job["job_id"])


def _read_completed_stores():
    completed_stores = []
    processed_stores = []
    if COMPLETED_STORES_PATH.exists():
        try:
            with COMPLETED_STORES_PATH.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if isinstance(data, dict):
                completed_stores = data.get("completed", [])
                processed_stores = data.get("processed", [])
            elif isinstance(data, list):
                completed_stores = data
        except Exception:
            pass
    return completed_stores, processed_stores


def start_format_job() -> dict:
    job = create_job("format")

    def worker():
        _set_job(
            job["job_id"],
            status="running",
            started_at=_utc_now(),
            message="Excel 自動整形を実行しています",
        )
        try:
            returncode, output = _run_subprocess(
                OFFLINE_FORMAT_SCRIPT_PATH,
                timeout_seconds=1800,
                extra_log={"action": "format_offline"},
            )
            completed_stores, processed_stores = _read_completed_stores()
            status = "succeeded" if returncode == 0 else "failed"
            message = "Excel 自動整形を実行しました" if returncode == 0 else "Excel整形処理に失敗しました"
            _set_job(
                job["job_id"],
                status=status,
                finished_at=_utc_now(),
                message=message,
                output=output[-4000:],
                completed_stores=completed_stores,
                processed_stores=processed_stores,
                returncode=returncode,
            )
        except subprocess.TimeoutExpired:
            _set_job(
                job["job_id"],
                status="failed",
                finished_at=_utc_now(),
                message="Excel 自動整形がタイムアウトしました",
                output="ジョブの実行がタイムアウトしました。",
                returncode=124,
            )
        except Exception as error:
            _set_job(
                job["job_id"],
                status="failed",
                finished_at=_utc_now(),
                message="整形処理実行エラー",
                output=str(error),
                returncode=1,
            )

    threading.Thread(target=worker, daemon=True).start()
    return get_job(job["job_id"])
