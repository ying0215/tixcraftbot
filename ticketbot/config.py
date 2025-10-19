"""
config.py

拓元購票機器人 - 設定檔
集中管理所有設定參數
"""

import os
from pathlib import Path

# 專案根目錄
# PROJECT_ROOT = Path(__file__).parent.parent
# __file__：代表 config.py 這個檔案本身的路徑。
# .parent：代表該檔案所在的資料夾，也就是 (專案根目錄)/ticketbot/。
# .parent.parent：代表父級資料夾的父級資料夾，也就是專案的根目錄。
# 確保無論您從哪個位置執行程式，都能正確找到專案根目錄。
PROJECT_ROOT = Path(__file__).parent.parent

# 資料目錄
DATA_DIR = PROJECT_ROOT / "data"
# DOWNLOADS_DIR => img_captche
DOWNLOADS_DIR = DATA_DIR / "downloads"
COOKIES_DIR = DATA_DIR / "cookies"
CACHE_DIR = DATA_DIR / "cache"

# cookie file
COOKIE_FILE = COOKIES_DIR / "tixcraft_cookies.json"

# 日誌目錄
LOGS_DIR = PROJECT_ROOT / "logs"

# 配置目錄
CONFIG_DIR = PROJECT_ROOT / "config"

# ========== 網站設定 ==========
GAME_URL = "https://tixcraft.com/activity/detail/25_tbtour"
TARGET_DATE = "2025/10/18 (六) 20:00"
TARGET_TEXT = "Tizzy Bac《說出我的名字》巡迴演唱會—Sit Down Please 特別場"

# ========== 票種設定 ==========
TARGET_AREA = ""
TICKET_VALUE = "2"  # 購買張數

# ========== OCR 設定 ==========
MAX_OCR_RETRY = 5  # OCR 最大重試次數
OCR_LANGUAGES = ['en']  # 英文
# 驗證碼圖片管理
MAX_CAPTCHA_IMAGES = 5  # 最多保留的驗證碼圖片數量
CAPTCHA_CLEANUP_PATTERN = "captcha_*.png"  # 清理的檔案模式

# ========== 時間設定 ==========
SHORT_WAIT = 1.0
LONG_WAIT = 2.0
PREPARE_MINUTES = 5  # 提前登入等待分鐘數

# ========== 初始化目錄 ==========
# ensure_directories() 功能：確保目錄都實際存在於您的電腦硬碟上。
# directory.mkdir(parents=True, exist_ok=True)：
# parents=True：如果父目錄不存在，會一併建立。
# 例如要建立 data/cookies，但 data 資料夾還不存在，它會先把 data 建立起來。
# exist_ok=True：如果資料夾已經存在，則不會報錯，會靜默處理。
def ensure_directories():
    """建立必要的目錄"""
    directories = [
        DATA_DIR,
        DOWNLOADS_DIR,
        COOKIES_DIR,
        CACHE_DIR,
        LOGS_DIR,
        CONFIG_DIR,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

# load_config(config_path=None)
# 載入外部設定檔 (例如 config.yaml)
# 檢查使用者是否從外部傳入了設定檔的路徑 (config_path)。
# 如果沒有，它會預設去 CONFIG_DIR 資料夾找一個叫 config.yaml 的檔案。
# 如果找到了設定檔 (config_file.exists() 為 True)，它就會準備從該檔案載入設定。
# 如果找不到，它就會退回使用這個 config.py 檔案中寫死的預設值。
def load_config(config_path=None):
    """載入配置"""
    ensure_directories()  # 確保目錄存在
    
    if config_path:
        config_file = Path(config_path)
    else:
        config_file = CONFIG_DIR / "config.yaml"
    
    if config_file.exists():
        print(f"從 {config_file} 載入配置")
        # 這裡可以用 yaml.safe_load() 讀取
        return {"mode": "file", "config_path": str(config_file)}
    else:
        print("使用預設配置")
        return {
            "mode": "default",
            "downloads_dir": str(DOWNLOADS_DIR),
            "cookies_dir": str(COOKIES_DIR),
            "logs_dir": str(LOGS_DIR),
        }


