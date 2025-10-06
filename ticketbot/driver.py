# cookies.py
# 負責載入與儲存 cookies

import json
import logging
import os
import time
from selenium.webdriver.remote.webdriver import WebDriver
import config


def load_cookies_json(driver: WebDriver, cookie_file=config.COOKIE_FILE_JSON):
    """從 JSON 載入 cookies 到瀏覽器"""
    if not os.path.exists(cookie_file):
        logging.warning(f"Cookie 檔案不存在：{cookie_file}")
        return False

    try:
        with open(cookie_file, "r", encoding="utf-8") as f:
            cookies = json.load(f)

        driver.get("https://tixcraft.com/")  # 先進入主網域再加入 cookies
        for cookie in cookies:
            # 移除無效欄位
            cookie.pop("sameSite", None)
            if "expiry" in cookie and isinstance(cookie["expiry"], float):
                cookie["expiry"] = int(cookie["expiry"])
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                logging.debug(f"略過無效 cookie：{cookie.get('name')}，原因：{e}")

        logging.info("Cookies 已載入至瀏覽器")
        return True
    except Exception as e:
        logging.error(f"載入 cookies 失敗：{e}")
        return False


def save_cookies_json(driver: WebDriver, cookie_file=config.COOKIE_FILE_JSON):
    """將 cookies 由瀏覽器儲存成 JSON"""
    try:
        cookies = driver.get_cookies()
        with open(cookie_file, "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=4, ensure_ascii=False)
        logging.info(f"Cookies 已儲存：{cookie_file}")
    except Exception as e:
        logging.error(f"儲存 cookies 失敗：{e}")


def wait_for_manual_login(driver: WebDriver, wait_seconds=60):
    """手動登入等待，用於第一次登入"""
    logging.info(f"請在 {wait_seconds} 秒內手動登入帳號...")
    for i in range(wait_seconds):
        time.sleep(1)
    logging.info("等待結束，繼續執行。")
