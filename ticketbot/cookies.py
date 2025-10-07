"""
cookies.py

拓元購票機器人 - Cookie 管理模組
處理 Cookie 的載入、儲存和登入等待
"""

import logging
import json
import os
import time
from . import config

logger = logging.getLogger(__name__)


def load_cookies_json(driver, path=config.COOKIE_FILE_JSON):
    """
    從 JSON 檔案載入 Cookie 到瀏覽器
    
    Args:
        driver: Selenium WebDriver 實例
        path: Cookie 檔案路徑
        
    Returns:
        bool: 是否成功載入有效的 Cookie
        
    Raises:
        Exception: Cookie 檔案讀取或解析失敗
    """
    if not os.path.exists(path):
        logger.warning("⚠️ 沒有 cookie 檔，需要手動登入")
        return False
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            cookies = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"❌ Cookie 檔案格式錯誤: {e}")
        raise Exception(f"Cookie 檔案解析失敗: {e}")
    
    current_time = time.time()
    valid_cookies = 0
    
    for cookie in cookies:
        # 檢查過期時間
        if "expiry" in cookie and cookie["expiry"] < current_time:
            continue
        
        try:
            driver.add_cookie(cookie)
            valid_cookies += 1
        except Exception as e:
            logger.warning(f"⚠️ 無法加入某個 cookie: {e}")
    
    if valid_cookies == 0:
        logger.warning("⚠️ 所有 cookie 已過期，需要重新登入")
        return False
    
    logger.info(f"✅ 成功載入 {valid_cookies} 個有效 cookie")
    return True


def save_cookies_json(driver, path=config.COOKIE_FILE_JSON):
    """
    將瀏覽器的 Cookie 儲存到 JSON 檔案
    
    Args:
        driver: Selenium WebDriver 實例
        path: Cookie 儲存路徑
        
    Raises:
        Exception: Cookie 儲存失敗
    """
    try:
        cookies = driver.get_cookies()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ 已儲存 {len(cookies)} 個 cookie 到 {path}")
    except Exception as e:
        logger.error(f"❌ 儲存 cookie 失敗: {e}")
        raise Exception(f"Cookie 儲存失敗: {e}")


def wait_for_manual_login(driver, wait_seconds=90):
    """
    等待使用者手動登入
    
    Args:
        driver: Selenium WebDriver 實例
        wait_seconds: 等待秒數
        
    Raises:
        TimeoutError: 等待超時
    """
    logger.info(f"👉 請在 {wait_seconds} 秒內手動登入...")
    logger.info("登入完成後請按 Enter 繼續...")
    
    try:
        # 使用 input() 等待使用者按 Enter
        input()
        logger.info("✅ 使用者確認已登入")
    except KeyboardInterrupt:
        raise Exception("使用者中斷登入流程")