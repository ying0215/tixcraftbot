"""
cookies.py

拓元購票機器人 - Cookie 管理模組
處理 Cookie 的載入、儲存和登入等待
"""

import threading
import json
import os
import time
from . import config
from .logger import setup_logger

logger = setup_logger(__name__)

# load_cookies(driver, path=...) - 載入通行證
# 功能：嘗試從本地 JSON 檔案讀取 Cookies，並將它們載入到當前的瀏覽器會話中。
# 參數 (Parameters)：
# driver: Selenium WebDriver 實例，代表要操作的瀏覽器。
# path: Cookie 檔案的儲存路徑，預設從 config.py 讀取。
# 流程:
# 1.檢查檔案是否存在
# 2.讀取與解析
# 3.檢查過期時間 (關鍵步驟)
#   cookie["expiry"] < current_time: 目前時間超過使用期限
# 4.加入 Cookie:
# 5.最終驗證
def load_cookies(driver, path=config.COOKIE_FILE):
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
            #continue
            logger.warning(f"⚠️ 發現過期的 Cookie 登入無效")
            return False
        
        try:
            driver.add_cookie(cookie)
            valid_cookies += 1
        except Exception as e:
            logger.warning(f"⚠️ 無法加入某個 cookie: {e}")
    
    logger.info(f"✅ 成功載入 {valid_cookies} 個有效 cookie")
    return True

# save_cookies(driver, path=...) - 儲存通行證
# 功能：將當前瀏覽器中的所有 Cookies 提取出來，並儲存到一個本地 JSON 檔案中。
# 執行時機：這個函式通常在互動模式下，使用者手動登入成功後被呼叫。
# 流程：
# driver.get_cookies(): 從 Selenium 獲取當前頁面的所有 Cookies。
# with open(...) as f: - 打開檔案
# with 陳述式: 這是一個 Python 的語法，用來確保 檔案 在使用完畢後，
# 無論是否發生錯誤，都會被自動關閉。 
# json.dump(...): 將獲取到的 Cookies 列表寫入指定的檔案路徑。
    # indent=2: 讓輸出的 JSON 檔案格式化，帶有縮排，方便人類閱讀。
    # ensure_ascii=False: 確保 Cookie 中的非英文字元（例如中文）可以被正確儲存。
def save_cookies(driver, path=config.COOKIE_FILE):
    """
    將瀏覽器的 Cookie 儲存到 JSON 檔案
    
    Args:
        driver: Selenium WebDriver 實例
        path: Cookie 儲存路徑
        
    Raises:
        Exception: Cookie 儲存失敗
    """
    logger.info(f"開始save cookies")
    try:
        cookies = driver.get_cookies()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ 已儲存 {len(cookies)} 個 cookie 到 {path}")
    except Exception as e:
        logger.error(f"❌ 儲存 cookie 失敗: {e}")
        raise Exception(f"Cookie 儲存失敗: {e}")

# waiting_for_users(wait_seconds=90) - 等待使用者手動操作
# 功能：在互動模式 (--interactive) 下，暫停程式的執行，等待使用者完成手動登入。
# 目前有 bug ，cookie 判斷完全不可行，因為網頁會跳來跳去導致cookie變化
# 如果使用 WebDriverWait 不確定是否可行
def waiting_for_users(driver, wait_seconds=90, check_interval=2):
    """
    等待使用者手動登入（智能檢測 Cookie 變化）
    
    Args:
        driver: Selenium WebDriver 實例
        wait_seconds: 最大等待秒數
        check_interval: 檢查間隔（秒）
        
    Raises:
        TimeoutError: 等待超時
    """
    logger.info(f"👉 請在 {wait_seconds} 秒內手動登入...")
    print(f"\n🔍 正在監控登入狀態...")
    print(f"⏰ 最多等待 {wait_seconds} 秒")
    print(f"💡 提示：登入成功後會自動繼續\n")
    
    # 記錄初始 Cookie 數量
    initial_cookies = len(driver.get_cookies())
    start_time = time.time()
    
    try:
        while True:
            elapsed = time.time() - start_time
            remaining = wait_seconds - int(elapsed)
            
            # 檢查是否超時
            if remaining <= 0:
                logger.warning(f"\n⏰ 等待時間已到 ({wait_seconds} 秒)")
                current_cookies = len(driver.get_cookies())
                break
            
            # 檢查 Cookie 是否增加（表示可能已登入）
            current_cookies = len(driver.get_cookies())
            if current_cookies > initial_cookies :
                logger.info(f"\n✅ 檢測到登入 (Cookie: {initial_cookies} → {current_cookies})")
                break
            
            # 顯示倒數
            print(f"\r⏳ 剩餘時間: {remaining:3d} 秒 | Cookie 數量: {current_cookies}", end='', flush=True)
            time.sleep(check_interval)
        
        print()  # 換行
        
    except KeyboardInterrupt:
        print()  # 換行
        elapsed = time.time() - start_time
        logger.info(f"✅ 使用者手動確認 (用時 {int(elapsed)} 秒)")
