# log.py
# 日誌系統設定

import logging
import config

def setup_logger():
    """設定全域日誌格式與輸出"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    logging.info("Logger 初始化完成")
