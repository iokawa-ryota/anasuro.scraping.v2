# スロット店舗スクレイピング Web UI

Windows 前提で使う、店舗選択型のスクレイピング UI です。  
店舗一覧の追加・削除・並び替え、保存先設定、実行ログ確認までブラウザ上で行えます。

## 構成

```text
d:\Users\Documents\python\pycord\anaslot\
├── Start.bat
├── setup.bat
├── setup_check.py
├── requirements.txt
├── data\
│   └── store_list.sample.csv
├── app\
│   ├── app.py
│   ├── index.html
│   ├── static\
│   │   ├── styles.css
│   │   └── app.js
│   ├── anasuro_selective.py
│   ├── offline_scraping.py
│   ├── config_manager.py
│   ├── services\
│   └── runtime\
└── dev\
    ├── DEV_REFERENCES.md
    └── RUNTIME_CONTRACTS.md
```

## セットアップ

```powershell
pip install -r requirements.txt
python setup_check.py
```

または `setup.bat` を実行してください。  
`setup_check.py` は不足パッケージの補完、設定ファイル生成、`data\store_list.csv` の初期化まで行います。

## 起動方法

```powershell
python app\app.py
```

または `Start.bat` を実行します。  
起動後は `http://localhost:5000` を開きます。

## UI でできること

- 店舗一覧の選択
- 店舗の追加
- 店舗の削除
- 店舗順の保存
- 保存先設定の更新
- スクレイピング実行
- Excel 自動整形の実行
- 実行ログの確認

## API の主な変更点

- `POST /api/scrape`
  非同期ジョブを作成し、`job_id` を返します。
- `POST /api/format-offline`
  非同期ジョブを作成し、`job_id` を返します。
- `GET /api/jobs/<job_id>`
  実行状態、メッセージ、出力ログ、整形結果を返します。
- `POST /api/stores`
  店舗追加。
- `DELETE /api/stores/<store_name>`
  店舗削除。

## デフォルト保存先

初期設定ではリポジトリ配下の `data\` を使います。

- `store_list_path`: `data\store_list.csv`
- `html_output_dir`: `data\saved_html`
- `csv_output_dir`: `data\machine_csv`

既存の運用先に変えたい場合は、Web UI の保存先設定から更新できます。

## 依存関係メモ

- `tqdm` と `lxml` を整形処理で使います
- `undetected-chromedriver` は Python 3.14 対応のため、プロジェクト内の `app/distutils/` shim に依存しています
- 将来的には `undetected-chromedriver` 側の更新でこの shim を外せる形へ寄せる想定です

## ランタイムファイル契約

ランタイムで受け渡すファイル形式は [RUNTIME_CONTRACTS.md](/d:/Users/Documents/python/pycord/anaslot/dev/RUNTIME_CONTRACTS.md) にまとめています。

## 開発用参照

開発時の参照資料は [DEV_REFERENCES.md](/d:/Users/Documents/python/pycord/anaslot/dev/DEV_REFERENCES.md) を起点にしてください。
