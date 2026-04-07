# Runtime Contracts

アプリ内で受け渡している主要なランタイムファイル契約をまとめます。

## `app/runtime/temp_store_list.csv`

- 用途: スクレイピング対象として選択された店舗だけを一時保存
- 生成元: `POST /api/scrape`
- 消費側: `app/anasuro_selective.py`
- 必須列:
  - `store_name`
  - `store_url`
  - `data_directory`
  - `last_update`

## `app/runtime/completed_stores.json`

- 用途: 整形処理の結果サマリ
- 生成元: `app/offline_scraping.py`
- 消費側: `GET /api/jobs/<job_id>` の format 結果
- 形式:

```json
{
  "completed": ["更新のあった店舗名"],
  "processed": ["処理した全店舗名"]
}
```

## `app/runtime/scraping_log.json`

- 用途: スクレイピングと整形ジョブの簡易履歴
- 生成元: `services/job_service.py`
- 形式: 1 行 1 JSON の JSONL
- 主なキー:
  - `timestamp`
  - `action`
  - `script`
  - `returncode`
  - `output`
