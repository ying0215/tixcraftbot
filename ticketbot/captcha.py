"""
captcha.py

拓元購票機器人 - 驗證碼處理模組
處理驗證碼的下載、刷新和填入
"""

import os
import time
import requests
from urllib.parse import urljoin
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from . import config
from .logger import setup_logger

logger = setup_logger(__name__)

def cleanup_old_captcha_images(directory, max_files=5, pattern="captcha_*.png"):
    """
    清理舊的驗證碼圖片，只保留最新的 N 個
    
    Args:
        directory: 圖片目錄
        max_files: 最多保留的檔案數量
        pattern: 檔案名稱模式（支援萬用字元）
        
    Returns:
        int: 刪除的檔案數量
    """
    try:
        # 取得所有符合條件的檔案
        image_dir = Path(directory)
        image_files = sorted(
            image_dir.glob(pattern),
            key=lambda p: p.stat().st_mtime,  # 按修改時間排序
            reverse=True  # 最新的在前面
        )
        
        # 如果檔案數量超過限制，刪除舊的
        if len(image_files) > max_files:
            files_to_delete = image_files[max_files:]
            deleted_count = 0
            
            for file_path in files_to_delete:
                try:
                    file_path.unlink()  # 刪除檔案
                    deleted_count += 1
                    logger.debug(f"🗑️ 已刪除舊驗證碼圖片: {file_path.name}")
                except Exception as e:
                    logger.warning(f"⚠️ 刪除檔案失敗: {file_path.name} - {e}")
            
            if deleted_count > 0:
                logger.info(f"🧹 已清理 {deleted_count} 個舊驗證碼圖片（保留最新 {max_files} 個）")
            
            return deleted_count
        
        return 0
        
    except Exception as e:
        logger.warning(f"⚠️ 清理舊圖片時發生錯誤: {e}")
        return 0

def download_captcha_image(driver, max_keep=5):
    """
    下載驗證碼圖片並儲存
    
    Args:
        driver: Selenium WebDriver 實例
        max_keep: 最多保留的驗證碼圖片數量

    Returns:
        str: 儲存的圖片檔案路徑
        
    Raises: 
        Exception: 下載或儲存失敗
    """
    try:
        # 確保下載目錄存在
        Path(config.DOWNLOADS_DIR).mkdir(parents=True, exist_ok=True)
        
        # 先清理舊圖片
        cleanup_old_captcha_images(config.DOWNLOADS_DIR, max_files=max_keep)
        
        # 找到驗證碼圖片元素
        img_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "TicketForm_verifyCode-image"))
        )
        
        # 取得圖片 src
        img_src = img_elem.get_attribute("src")
        logger.debug(f"驗證碼圖片 src: {img_src}")
        
        # 建立完整 URL
        captcha_url = urljoin(driver.current_url, img_src)
        
        # 取得瀏覽器的 cookies 用於請求
        cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}
        
        # 下載圖片
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(captcha_url, cookies=cookies, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 儲存圖片
        timestamp = int(time.time() * 1000)
        filename = f"captcha_{timestamp}.png"
        filepath = os.path.join(config.DOWNLOADS_DIR, filename)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"✅ 驗證碼圖片已儲存: {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"❌ 下載驗證碼圖片失敗: {e}")
        
        # Fallback: 直接截圖元素
        try:
            img_elem = driver.find_element(By.ID, "TicketForm_verifyCode-image")
            timestamp = int(time.time() * 1000)
            filename = f"captcha_screenshot_{timestamp}.png"
            filepath = os.path.join(config.DOWNLOADS_DIR, filename)
            img_elem.screenshot(filepath)
            logger.info(f"✅ 使用截圖方式儲存驗證碼: {filepath}")
            return filepath
        except Exception as e2:
            logger.error(f"❌ 截圖元素也失敗: {e2}")
            raise Exception(f"無法取得驗證碼圖片: {e2}")


def refresh_captcha(driver):
    """
    刷新驗證碼圖片
    
    Args:
        driver: Selenium WebDriver 實例
        
    Raises:
        Exception: 刷新失敗
    """
    try:
        img_elem = driver.find_element(By.ID, "TicketForm_verifyCode-image")
        img_elem.click()
        logger.info("✅ 已點擊刷新驗證碼")
    except Exception:
        try:
            img_elem = driver.find_element(By.ID, "TicketForm_verifyCode-image")
            driver.execute_script("arguments[0].click();", img_elem)
            logger.info("✅ 已用 JS 刷新驗證碼")
        except Exception as e:
            logger.error(f"❌ 無法刷新驗證碼: {e}")
            raise Exception(f"刷新驗證碼失敗: {e}")


def fill_captcha(driver, captcha_text):
    """
    填入驗證碼到輸入框
    
    Args:
        driver: Selenium WebDriver 實例
        captcha_text: 驗證碼文字
        
    Raises:
        Exception: 填入失敗
    """
    try:
        input_elem = driver.find_element(By.ID, "TicketForm_verifyCode")
        input_elem.clear()
        input_elem.send_keys(captcha_text)
        logger.info(f"✅ 已填入驗證碼: {captcha_text}")
    except Exception as e:
        logger.error(f"❌ 填入驗證碼失敗: {e}")
        raise Exception(f"填入驗證碼失敗: {e}")