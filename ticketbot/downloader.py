"""
downloader.py
下載和 Cookie 管理
"""
import json
from pathlib import Path
from .config import DOWNLOADS_DIR, COOKIES_DIR
from .logger import setup_logger

logger = setup_logger(__name__)

def save_cookie(cookie_data, filename="cookies.json"):
    """
    儲存 Cookie
    
    Args:
        cookie_data: Cookie 資料（字典或列表）
        filename: 檔案名稱
    """
    cookie_file = COOKIES_DIR / filename
    try:
        with open(cookie_file, 'w', encoding='utf-8') as f:
            json.dump(cookie_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Cookie 已儲存到: {cookie_file}")
    except Exception as e:
        logger.error(f"儲存 Cookie 失敗: {e}")
        raise

def load_cookie(filename="cookies.json"):
    """
    載入 Cookie
    
    Args:
        filename: 檔案名稱
    
    Returns:
        Cookie 資料
    """
    cookie_file = COOKIES_DIR / filename
    if not cookie_file.exists():
        logger.warning(f"Cookie 檔案不存在: {cookie_file}")
        return None
    
    try:
        with open(cookie_file, 'r', encoding='utf-8') as f:
            cookie_data = json.load(f)
        logger.info(f"Cookie 已載入: {cookie_file}")
        return cookie_data
    except Exception as e:
        logger.error(f"載入 Cookie 失敗: {e}")
        raise

def download_image(url, filename=None):
    """
    下載圖片（示意用途）
    
    Args:
        url: 圖片網址
        filename: 儲存的檔案名稱（可選）
    
    Returns:
        儲存的檔案路徑
    """
    import requests
    from urllib.parse import urlparse
    
    if filename is None:
        # 從 URL 提取檔名
        filename = Path(urlparse(url).path).name or "image.jpg"
    
    save_path = DOWNLOADS_DIR / filename
    
    try:
        logger.info(f"開始下載: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"圖片已儲存到: {save_path}")
        return save_path
    except Exception as e:
        logger.error(f"下載失敗: {e}")
        raise