# captcha.py
# 處理驗證碼相關的操作（不含 OCR）

import os
import time
import logging
import requests
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
import config


def _timestamp_name(prefix="captcha"):
    """產生時間戳記檔名"""
    now = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return f"{prefix}_{now}.png"


def download_captcha_image(driver: WebDriver) -> str:
    """
    嘗試下載驗證碼圖片（支援 blob/data src）
    回傳儲存的本地路徑
    """
    try:
        captcha_element = driver.find_element(By.ID, "TicketForm_verifyCode-image")
        src = captcha_element.get_attribute("src")

        # 確保資料夾存在
        os.makedirs(config.IMAGE_PATH, exist_ok=True)
        filename = _timestamp_name()
        file_path = os.path.join(config.IMAGE_PATH, filename)

        if src.startswith("blob:"):
            # 若為 blob URL，直接擷取元素截圖
            captcha_element.screenshot(file_path)
        elif src.startswith("data:image"):
            # 若為 base64 圖片
            import base64
            base64_data = src.split(",")[1]
            with open(file_path, "wb") as f:
                f.write(base64.b64decode(base64_data))
        else:
            # 一般 HTTP(S) 圖片
            resp = requests.get(src, timeout=10)
            with open(file_path, "wb") as f:
                f.write(resp.content)

        logging.info(f"驗證碼圖片已下載：{file_path}")
        return file_path
    except Exception as e:
        logging.error(f"下載驗證碼圖片失敗：{e}")
        return ""


def refresh_captcha(driver: WebDriver):
    """點擊刷新驗證碼"""
    try:
        refresh_button = driver.find_element(By.ID, "TicketForm_verifyCode-button")
        refresh_button.click()
        time.sleep(1)
        logging.info("驗證碼已刷新")
    except Exception as e:
        logging.warning(f"刷新驗證碼失敗：{e}")


def fill_captcha(driver: WebDriver, captcha_text: str):
    """將辨識結果填入驗證碼欄位"""
    try:
        input_box = driver.find_element(By.ID, "TicketForm_verifyCode")
        input_box.clear()
        input_box.send_keys(captcha_text)
        logging.info(f"已填入驗證碼：{captcha_text}")
    except Exception as e:
        logging.error(f"填入驗證碼失敗：{e}")
