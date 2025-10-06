# arg_parser.py
# 統一命令列參數解析

import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Tixcraft 自動購票腳本")
    parser.add_argument("--headless", action="store_true", help="啟用無頭模式")
    parser.add_argument("--interactive", action="store_true", help="需要手動登入與關閉前暫停")
    parser.add_argument("--pause-on-exit", action="store_true", help="結束時暫停按 Enter")
    parser.add_argument("--ticket-index", type=int, default=1, help="預設票種索引 (1開始)")
    parser.add_argument("--ticket-label", type=str, default="", help="依票名選擇票種（預設空）")
    return parser.parse_args()
