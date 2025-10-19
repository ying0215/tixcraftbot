"""
log.py
日誌配置模組
"""
import logging
from logging.handlers import RotatingFileHandler
from .config import LOGS_DIR, ensure_directories

def setup_logger(name="bot", level=logging.INFO):
    """
    設置日誌記錄器
    
    Args:
        name: 日誌記錄器名稱
        level: 日誌級別
    
    Returns:
        logger: 配置好的日誌記錄器
    """

    ensure_directories()
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Handler 目的地
    # 避免重複添加 handler
    # 同一個 logger 的設定只會進行一次。
    if logger.handlers:
        return logger
    
    # 檔案 handler - 一般日誌
    # RotatingFileHandler 會「輪替」的檔案處理器
    # log_file: 指定日誌檔案的路徑
    # maxBytes 單一檔案的最大容量，
    # 大小超過 10MB 時，RotatingFileHandler 會自動將它重新命名為 app.log.1。
    # backupCount 最多會保留到 app.log.5，再舊的就會被自動刪除。
    # encoding='utf-8': 確保日誌可以正確寫入中文等非英文字元。
    log_file = LOGS_DIR / "app.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    # file_handler.setLevel(logging.INFO): 
    # 這個 handler 會接收所有 INFO 級別及以上的訊息。
    file_handler.setLevel(logging.INFO)
    
    # 檔案 handler - 錯誤日誌
    error_file = LOGS_DIR / "error.log"
    error_handler = RotatingFileHandler(
        error_file,
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    # error_handler.setLevel(logging.ERROR): 
    # 這個 handler 只會接收 ERROR 級別及以上的訊息。
    error_handler.setLevel(logging.ERROR)
    
    # 控制台 handler
    # StreamHandler : 日誌訊息輸出到標準輸出（終端機）。
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 格式化 (Formatter)
    # Formatter 用來定義每一條日誌訊息的外觀格式
    # '%(asctime)s': 訊息記錄的時間。
    #'%(name)s': logger 的名字 (就是前面傳入的 name="bot")。
    #'%(levelname)s': 訊息的級別 (INFO, ERROR 等)。
    #'%(message)s': 您實際要記錄的訊息內容。
    #datefmt: 自訂時間戳的格式。
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加 handlers
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)
    
    return logger

"""
# 使用範例:假設在 main.py 中
from .log import setup_logger

# 在程式開始時，先呼叫一次來完成設定
logger = setup_logger()

def start_bot():
    logger.info("機器人程式已啟動。")
    logger.info(f"目標開賣時間設定為: ...")
    
    try:
        # 這裡放可能出錯的程式碼
        ticket_status = get_ticket_status()
        if not ticket_status:
            logger.warning("無法獲取票券狀態，可能頁面有變動。")
        
        # 假設這裡發生了嚴重錯誤
        result = 10 / 0

    except Exception as e:
        # 使用 logger.error 來記錄錯誤
        # exc_info=True 會自動附上詳細的錯誤追蹤訊息
        logger.error(f"搶票過程中發生未預期的錯誤: {e}", exc_info=True)

    logger.info("機器人程式執行完畢。")

start_bot()

"""

