"""
config.py

拓元購票機器人 - 設定檔
集中管理所有設定參數
"""

import os
from pathlib import Path

# ========== 網站設定 ==========
GAME_URL = "https://tixcraft.com/activity/detail/25_yama"
TARGET_DATE = "2025/10/16 (四) 20:00"
TARGET_TEXT = "yama Asia Tour 2025 虎視眈眈"

# ========== 票種設定 ==========
TICKET_VALUE = "2"  # 購買張數

# ========== OCR 設定 ==========
MAX_OCR_RETRY = 5  # OCR 最大重試次數
OCR_OUTPUT_DIR = r"C:\Users\useru\Documents\working\Python\img_captcha"
OCR_LANGUAGES = ['en']  # 英文

# ========== 時間設定 ==========
SHORT_WAIT = 1.0
LONG_WAIT = 2.0
DEFAULT_PREPARE_MINUTES = 5  # 提前登入等待分鐘數

# ========== Cookie 設定 ==========
COOKIE_FILE_JSON = "tixcraft_cookies.json"

# ========== 日誌設定 ==========
LOG_FILE = "ticket_bot.log"

# ========== 初始化目錄 ==========
def init_directories():
    """確保所需目錄存在"""
    Path(OCR_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# 自動初始化
init_directories()