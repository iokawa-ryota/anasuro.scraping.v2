from bs4 import BeautifulSoup
import pandas as pd
import os
import re
from tqdm.notebook import tqdm

# 対象ディレクトリを指定
html_dir = r"D:\Users\Documents\python\saved_html\SLOT ACT"
output_path = os.path.join(html_dir, "output.xlsx")

# データ格納
all_data = []

# 対象ファイル一覧取得
html_files = sorted([f for f in os.listdir(html_dir) if f.endswith(".html")])

# ファイルを1つずつ処理
for file in tqdm(html_files, desc="HTML処理中", unit="file"):
    # 日付をファイル名から取得
    match = re.search(r"\d{4}-\d{2}-\d{2}", file)
    if not match:
        continue
    day = match.group(0)

    file_path = os.path.join(html_dir, file)
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    table = soup.find("table", {"id": "all_data_table"})
    if not table:
        continue

    rows = table.find_all("tr")[1:]  # ヘッダーをスキップ
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
        except:
            game_int = 0
        try:
            bb_int = int(bb)
        except:
            bb_int = 0
        try:
            rb_int = int(rb)
        except:
            rb_int = 0
        try:
            diff_int = int(diff)
        except:
            diff_int = 0

        total = round(game_int / (bb_int + rb_int), 1) if (bb_int + rb_int) else 0
        big_per = round(game_int / bb_int, 1) if bb_int else 0
        reg_per = round(game_int / rb_int, 1) if rb_int else 0

        all_data.append({
            "day": day,
            "dai_name": dai_name,
            "dai_num": int(dai_num) if dai_num.isdigit() else 0,
            "game": game_int,
            "difference": diff_int,
            "bb": bb_int,
            "rb": rb_int,
            "Total": total,
            "big_per": big_per,
            "reg_per": reg_per
        })

# Excel保存
if all_data:
    df = pd.DataFrame(all_data)
    df.to_excel(output_path, index=False)
    print(f"✅ 保存完了: {output_path}")
else:
    print("⚠️ データが見つかりませんでした。")
