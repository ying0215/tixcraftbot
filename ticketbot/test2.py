"""
test1.py
測試檔案
"""

from .logger import setup_logger

logger = setup_logger()

logger.info("Recorder information test")
logger.error("logger error test")
