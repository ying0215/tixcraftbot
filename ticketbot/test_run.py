# test_run.py
# 專案整合測試（不實際送出訂單）
# 確認所有模組能正確初始化、運作、記錄日誌

import logging
from log import setup_logger
from driver import setup_driver
from cookies import load_cookies_json
from captcha import download_captcha_image, refresh_captcha
from purchase import select_match_and_buy, select_area, select_tickets
import ticketbot.config2 as config2


def main():
    setup_logger()
    logging.info("=== 🧩 專案整合測試開始 ===")

    # 1️⃣ 啟動瀏覽器
    driver = setup_driver(headless=True)  # 測試可開 headless 模式
    driver.get(config2.GAME_URL)
    logging.info(f"已開啟頁面：{config2.GAME_URL}")

    # 2️⃣ 嘗試載入 cookies（若無則略過）
    load_cookies_json(driver)

    # 3️⃣ 嘗試執行主要功能（不送出）
    logging.info("測試選擇場次功能...")
    select_match_and_buy(driver)

    logging.info("測試選擇區域功能...")
    select_area(driver)

    logging.info("測試選擇票種功能...")
    select_tickets(driver)

    # 4️⃣ 驗證 captcha 功能
    logging.info("測試驗證碼刷新與下載...")
    refresh_captcha(driver)
    img_path = download_captcha_image(driver)
    logging.info(f"下載圖片路徑：{img_path}")

    # 5️⃣ 結束測試
    logging.info("✅ 所有模組執行結束，檢查 logs/app.log 是否完整記錄。")
    driver.quit()


if __name__ == "__main__":
    main()
