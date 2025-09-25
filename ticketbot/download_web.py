import os
from selenium import webdriver

def save_html_pages(urls, folder="html_pages"):
    # 如果資料夾不存在就建立
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"📂 已建立資料夾: {folder}")

    # 啟動瀏覽器
    driver = webdriver.Chrome()

    for i, url in enumerate(urls, start=1):
        try:
            driver.get(url)

            # 抓 HTML
            html_content = driver.page_source

            # 檔名（避免特殊符號，可以用編號）
            filename = os.path.join(folder, f"page_{i}.html")

            # 存檔
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html_content)

            print(f"✅ {url} 已存成 {filename}")

        except Exception as e:
            print(f"⚠️ 抓取失敗 {url}: {e}")

    driver.quit()


# 使用範例
urls = [
    "https://tixcraft.com/activity/detail/25_fireball",
    "https://tixcraft.com/activity/game/25_fireball",
    "https://tixcraft.com/ticket/area/25_fireball/19899"
]

save_html_pages(urls)
