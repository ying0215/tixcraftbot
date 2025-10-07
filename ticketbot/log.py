"""
log.py

拓元購票機器人 - 日誌模組
統一設定日誌格式與輸出
"""

import logging
from . import config


def setup_logger():
    """
    設定日誌系統
    - 同時輸出到檔案和終端
    - 使用 UTF-8 編碼
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(funcName)s] %(message)s",
        handlers=[
            logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("日誌系統已初始化")
    return logger