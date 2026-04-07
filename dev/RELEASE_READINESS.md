# 作業フォルダ監査メモ

作成日: 2026-04-04  
対象: `d:\Users\Documents\python\pycord\anaslot`

## 現状サマリ

判定: **以前よりかなり整理されたが、一般配布前にはまだ少し整備したい**

今回までで改善された点:

- 保存先設定を `app_config.json` に集約した
- Web UI から HTML 保存先と CSV 出力先を変更できる
- `setup_check.py` の Windows コンソール互換性を改善した
- `start.bat` 前提のズレを縮小した
- スクレイパ起動失敗時に API でエラーが見えるようになった

## 現在の主要ファイル

### コア実装

- `app.py`
- `index.html`
- `anasuro_selective.py`
- `offline_scraping.py`
- `config_manager.py`
- `app_config.json`

### 起動・セットアップ

- `setup.bat`
- `start_silent.bat`
- `setup_check.py`
- `requirements.txt`

### 実行時生成物

- `temp_store_list.csv`
- `scraping_log.json`
- `completed_stores.json`

## まだ気になる点

### 1. 実行生成物が Git 管理に残りやすい

- `temp_store_list.csv`
- `scraping_log.json`
- `completed_stores.json`

これらは `.gitignore` に入れておく方が安全です。

### 2. `store_list.csv` の扱い

設定で参照先は切り替えられるようになったが、公開用には `store_list.sample.csv` のようなサンプルがあると親切です。

### 3. 開発向け設定

- `app.py` は `debug=False` で起動するように変更済み

公開運用では `debug=False` に寄せたいです。

### 4. 旧補助スクリプトの扱い

- `anasuro.html-fetcher.py`

現行フローの主役ではないので、残すなら役割を README に書くか、不要なら整理したいです。

### 5. 利用ポリシーの明文化

- 対象サイトの利用条件
- アクセス頻度
- 公開配布時の注意事項

このあたりは README か別文書にあると安心です。

## 配布前チェックリスト

- [ ] 実行生成物を `.gitignore` に追加
- [ ] `store_list.sample.csv` を追加
- [ ] `debug=False` 前提の起動方法を整理
- [ ] 不要ファイルの棚卸し
- [ ] README の公開向け説明をもう一段整理
- [ ] 利用条件や運用注意を明記

## 結論

現状は「自分用・小規模共有」にはかなり扱いやすくなっています。  
一般配布するなら、生成物の除外と公開向けサンプル整備をやれば、かなり出しやすい状態です。

## 開発時の参考資料

`dev/references/everything-claude-code/` に参照用の開発資料を置いてあります。  
実装やレビュー時は [DEV_REFERENCES.md](/d:/Users/Documents/python/pycord/anaslot/dev/DEV_REFERENCES.md) を起点に、必要に応じてこれらのファイルを参照してコーディングして構いません。
