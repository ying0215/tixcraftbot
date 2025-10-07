# config.py
# 動態配置
import argparse
from pathlib import Path

# 定義一個 Config 類別來集中管理設定
class AppConfig:
    def __init__(self):
        # 預設值
        self.BASE_URL = "https://example.com/"
        self.TIMEOUT = 10
        self.OUTPUT_DIR = Path("./data")
        self.LOG_LEVEL = "INFO"

    def parse_args(self):
        """解析命令行參數並更新配置"""
        parser = argparse.ArgumentParser(description="My Web Scraper.")
        parser.add_argument("--url", type=str, default=self.BASE_URL,
                            help="The starting URL for scraping.")
        parser.add_argument("--level", type=str, default=self.LOG_LEVEL,
                            help="Set logging level (DEBUG, INFO, ERROR).")
        args = parser.parse_args()
        
        self.BASE_URL = args.url
        self.LOG_LEVEL = args.level.upper()
        
        if not self.OUTPUT_DIR.exists():
            self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        return self

# 在其他地方使用時，我們只匯入這個單例實例
CONFIG = AppConfig().parse_args()