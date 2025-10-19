#!/usr/bin/env python3
"""
輕量級啟動腳本
直接執行此檔案來啟動應用程式
"""

import sys
from pathlib import Path

# 確保可以導入 my_package
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ticketbot import run_app

if __name__ == "__main__":
    # 可以從命令列參數接收配置
    config_path = sys.argv[1] if len(sys.argv) > 1 else None
    run_app(config_path)