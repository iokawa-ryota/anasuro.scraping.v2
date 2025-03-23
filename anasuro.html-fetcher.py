import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import os
from datetime import datetime

# HTMLを保存
def save_html(driver, date_str, save_dir):
    os.makedirs(save_dir, exist_ok=True)
    filename = os.path.join(save_dir, f"{date_str}.html")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print(f"HTMLを保存しました: {filename}")

# 店舗一覧読み込み
store_list_path = "D:/Users/Documents/python/saved_html/store_list.xlsx"
df = pd.read_excel(store_list_path)

# Chrome起動（JavaScript無効化）
options = uc.ChromeOptions()
prefs = {
    "profile.managed_default_content_settings.javascript": 2
}
options.add_experimental_option("prefs", prefs)
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--start-maximized")
driver = uc.Chrome(options=options)

try:
    for index, row in df.iterrows():
        list_url = row["store_url"]
        save_dir = row["data_directory"]
        print(f"\n📍 店舗処理開始: {list_url}")

        # 保存済みファイル取得
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        existing_files = set(f.replace(".html", "") for f in os.listdir(save_dir) if f.endswith(".html"))

        # ページへアクセス
        driver.get(list_url)
        print("一覧ページにアクセスしました")

        date_rows = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.date-table .table-row"))
        )

        # 取得対象日付一覧を作成
        date_list = []
        for row in reversed(date_rows):
            try:
                a_tag = row.find_element(By.TAG_NAME, "a")
                date_text = a_tag.text.strip().split("(")[0].replace("/", "-")
                datetime.strptime(date_text, "%Y-%m-%d")  # 正しい日付形式か確認
                if date_text not in existing_files:
                    date_list.append(date_text)
            except:
                continue

        print(f"取得対象日数: {len(date_list)} 件")

        for date_str in date_list:
            print(f"日付 {date_str} にアクセスします")

            # 一覧から最新のリンク再取得
            date_rows = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.date-table .table-row"))
            )
            link_element = None
            for row in reversed(date_rows):
                try:
                    a_tag = row.find_element(By.TAG_NAME, "a")
                    if a_tag.text.strip().startswith(date_str.replace("-", "/")):
                        link_element = a_tag
                        break
                except:
                    continue

            if not link_element:
                print(f"{date_str} のリンクが見つかりませんでした。")
                continue

            driver.execute_script("arguments[0].scrollIntoView(true);", link_element)
            ActionChains(driver).move_to_element(link_element).pause(0.5).click().perform()

            WebDriverWait(driver, 10).until(lambda d: "-data" in d.current_url)
            print("遷移成功：", driver.current_url)

            save_html(driver, date_str, save_dir)

            driver.get(list_url)

finally:
    driver.quit()
    print("ブラウザを閉じました。")
