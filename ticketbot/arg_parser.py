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
    
    # parser(解析器): 
    # argparse.ArgumentParser(...)建立空的設定選單。
    parser = argparse.ArgumentParser(
        description="拓元購票機器人 - 自動化購票工具"
    )
    # 定義可接受的參數
    # .add_argument(...)選單上新增一個設定選項
    # type=str：接收的輸入格式當作字串
    # required=False：代表參數是選填的，不是必須的
    # help="..."：說明文字
    # 當使用者在命令列輸入 python -m ticketbot --help 時，
    # 告訴使用者這個參數的用途和格式。
    parser.add_argument(        
        "--start-time",
        type=str,
        required=False,
        help="開賣時間 (格式: YYYY-MM-DD HH:MM:SS，本地時間)。若不指定則立即開始"
    )
    
    parser.add_argument(
        "--prepare-minutes",
        type=int,
        default=config.PREPARE_MINUTES,
        help=f"提前登入等待的分鐘數，預設 {config.PREPARE_MINUTES} 分鐘"
    )

    # --headless：決定是否在背景模式執行瀏覽器。
    # 在無頭模式 (headless mode) 下，程式執行時不會跳出瀏覽器視窗，
    # 所有操作都在記憶體中完成。這在伺服器上執行或單純想減少干擾時非常有用。
    # action="store_true"：
    #   加上 --headless，參數的值為 True，即可啟用。
    #   如果沒有加入 --headless，值就是 False。
    parser.add_argument(
        "--headless",
        action="store_true",
        help="使用無頭模式運行瀏覽器（不顯示視窗）"
    )
    
    # 用來控制「互動模式」。當程式發現儲存的 Cookie (登入憑證) 失效時，
    # 如果處於互動模式，程式會暫停並等待使用者手動登入
    parser.add_argument(
        "--interactive",
        dest="interactive",
        action="store_true",
        default=True,
        help="互動模式：Cookie 失效時等待手動登入"
    )

    parser.add_argument(
        "--no-interactive",
        dest="interactive",
        action="store_false",
        help="停用互動模式：Cookie 失效使用遊客模式"
    )

    # 程式在所有任務完成或發生錯誤結束前，會停在終端機畫面，
    # 並顯示類似 "Press Enter to exit..." 的訊息。
    # 這對於在 Windows 雙擊 .bat 檔案執行程式的使用者來說非常有用，
    # 可以防止視窗「閃退」，讓他們有機會看到程式最後的輸出訊息。
    parser.add_argument(
        "--pause-on-exit",
        action="store_true",
        default=False,
        help="程式結束前暫停，等待按 Enter 關閉"
    )

    # 解析實際輸入
    # .parse_args() 檢查使用者在命令列中真正輸入了什麼，並將這些輸入值整理好。
    args = parser.parse_args()
    
    # 轉換 start_time 為 datetime 物件
    if args.start_time:
        try:
            args.start_time = datetime.strptime(args.start_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise ValueError("開賣時間格式錯誤，請使用: YYYY-MM-DD HH:MM:SS")
    
    return args