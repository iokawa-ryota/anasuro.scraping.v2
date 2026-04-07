# 起動方法ガイド

## ふだん使う起動方法

### `Start.bat`

- Python Launcher (`py -3`) または `python` を自動検出します
- Flask サーバーを別ウィンドウで起動し、ブラウザを開きます
- 手軽ですが、詳細ログを見るには向きません

停止したいときは、`Flask Server` として起動した Python プロセスを閉じてください。

### `python app\app.py`

```powershell
python app\app.py
```

- ターミナルでログを見ながら起動できます
- スクレイピングや整形ジョブのエラー確認に向いています
- 停止は `Ctrl + C` です

## 初回セットアップ

```powershell
python setup_check.py
```

または `setup.bat` を使ってください。  
初期設定では `data\store_list.csv`、`data\saved_html`、`data\machine_csv` が用意されます。

## 実行ログ

フロント右側の `実行ログ` タブでは、直近ジョブの状態を確認できます。  
より詳しい履歴は `app\runtime\scraping_log.json` に JSONL 形式で保存されます。

## よくある問題

### スクレイピング開始後にすぐ終わらない

現在は非同期ジョブで処理します。  
画面上のステータスと `実行ログ` タブ、または `GET /api/jobs/<job_id>` の結果を確認してください。

### 整形処理が失敗する

`tqdm` と `lxml` が不足していないか、`python setup_check.py` で確認してください。

### ChromeDriver 周りで失敗する

`undetected-chromedriver` と Chrome の組み合わせに依存します。  
`app/distutils/` の互換 shim は暫定策なので、将来は依存更新で置き換える方針です。
