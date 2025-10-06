# config.py
# 專案設定參數集中管理

# 日誌
LOG_FILE = "app.log"

# Cookie 與圖片
COOKIE_FILE_JSON = "cookies.json"
IMAGE_PATH = "img_captcha"

# 目標資訊
GAME_URL = "https://tixcraft.com/activity/game/25_fireball"
TARGET_DATE = "2025/10/10"
TARGET_TEXT = "Legacy Taipei"
TICKET_VALUE = "2"

# OCR 與重試
OCR_THRESHOLD = 0.8
RETRY_LIMIT = 5
RETRY_INTERVAL = 2  # 秒

# 其他可調參數
WAIT_TIMEOUT = 10
CLICK_DELAY = 0.5
