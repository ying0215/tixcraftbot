"""
arg_parser.py

拓元購票機器人 - 命令列參數解析
處理啟動時的各種參數選項
"""

import argparse
from datetime import datetime
from . import config


def parse_args():
    """
    解析命令列參數
    
    Returns:
        argparse.Namespace: 包含所有參數的物件
    """
    parser = argparse.ArgumentParser(
        description="拓元購票機器人 - 自動化購票工具"
    )
    
    parser.add_argument(
        "--start-time",
        type=str,
        required=False,
        help="開賣時間 (格式: YYYY-MM-DD HH:MM:SS，本地時間)。若不指定則立即開始"
    )
    
    parser.add_argument(
        "--prepare-minutes",
        type=int,
        default=config.DEFAULT_PREPARE_MINUTES,
        help=f"提前登入等待的分鐘數，預設 {config.DEFAULT_PREPARE_MINUTES} 分鐘"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="使用無頭模式運行瀏覽器（不顯示視窗）"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        default=True,
        help="互動模式：Cookie 失效時等待手動登入"
    )
    
    parser.add_argument(
        "--pause-on-exit",
        action="store_true",
        default=False,
        help="程式結束前暫停，等待按 Enter 關閉"
    )
    
    args = parser.parse_args()
    
    # 轉換 start_time 為 datetime 物件
    if args.start_time:
        try:
            args.start_time = datetime.strptime(args.start_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise ValueError("開賣時間格式錯誤，請使用: YYYY-MM-DD HH:MM:SS")
    
    return args