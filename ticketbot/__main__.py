"""
__main__.py

拓元購票機器人 - 重構版本
使用模組化架構，職責分離清晰

功能：
- 自動登入並保持會話
- 選擇指定場次和票種
- 下載驗證碼圖片並使用 OCR 辨識
- 自動填入驗證碼並提交購票

使用方式：
    python -m ticketbot.main --start-time "2025-10-16 19:55:00"
    python -m ticketbot.main --interactive  # 互動模式（手動登入）
    python -m ticketbot.main --headless     # 無頭模式

架構說明：
    TicketBot (核心協調者)
        ├─ WebClient (網頁互動層)
        ├─ Selector (選擇邏輯層)
        └─ CaptchaSolver (驗證碼處理層)
"""


from pathlib import Path

# 自定義模組
from . import config
from .logger import setup_logger
from .driver import setup_driver
from .arg_parser import parse_args
from .ticket_bot import TicketBot
from .OCR import get_reader

logger = setup_logger(__name__)



def print_banner():
    """顯示啟動橫幅"""
    banner = """
    ╔════════════════════════════════════════════════════════╗
    ║          🎫 拓元購票機器人 - 重構版 v2.0 🎫             ║
    ║          Modular Architecture • Clean Code             ║ 
    ╚════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_config_info(args):
    """
    顯示配置資訊
    
    Args:
        args: 命令列參數
    """
    logger.info("=" * 60)
    logger.info("📋 機器人配置資訊")
    logger.info("=" * 60)
    logger.info(f"🎯 目標活動: {config.GAME_URL}")
    logger.info(f"📅 目標場次: {config.TARGET_DATE}")
    logger.info(f"💺 目標區域: {config.TARGET_AREA if hasattr(config, 'TARGET_AREA') else '自動選擇'}")
    logger.info(f"🎫 購買張數: {config.TICKET_VALUE}")
    
    if args.start_time:
        logger.info(f"⏰ 開賣時間: {args.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"⏳ 提前準備: {args.prepare_minutes} 分鐘")
    else:
        logger.info(f"⏰ 開賣時間: 立即開始")
    
    logger.info(f"🖥️  瀏覽器模式: {'無頭模式' if args.headless else '可見模式'}")
    logger.info(f"👤 登入模式: {'互動式登入' if args.interactive else '自動載入 Cookie'}")
    logger.info(f"⏸️  結束時暫停: {'是' if args.pause_on_exit else '否'}")
    logger.info("=" * 60)


def preload_ocr_model():
    """
    預載 OCR 模型
    提前載入模型可以減少首次辨識的時間
    """
    try:
        logger.info("📚 正在預載 OCR 模型...")
        get_reader(langs=config.OCR_LANGUAGES)
        logger.info("✅ OCR 模型預載完成")
    except Exception as e:
        logger.warning(f"⚠️ OCR 模型預載失敗: {e}")
        logger.warning("   將在首次使用時載入模型")


def ensure_directories():
    """
    確保必要的目錄存在
    """
    try:
        Path(config.DOWNLOADS_DIR).mkdir(parents=True, exist_ok=True)
        logger.debug("✅ 必要目錄已建立")
    except Exception as e:
        logger.error(f"❌ 建立目錄失敗: {e}")

# main() 函式 - 總執行流程
# 一：初始化 (Initialization)
# parse_args(): 接著，解析使用者從命令列傳來的指令，
# 決定這次任務的執行方式（例如是否用無頭模式、開賣時間等）。
# 二：資訊展示與準備 (Information & Preparation)
# 三：核心任務執行 (try...except...finally 區塊)
# try 區塊 (快樂路徑 Happy Path):
    # driver = setup_driver(...): 啟動瀏覽器，這是我們執行任務的「載具」。
    # bot = TicketBot(driver): 最重要的一步，建立TicketBot 的實例，
    # 並把瀏覽器的控制權交給它。
    # bot.load_login_session(...): 指揮官處理登入問題。
    # success = bot.start_booking(...): 指揮官開始執行完整的搶票流程。
    # main 函式在這裡會暫停，等待 start_booking 完成並回傳結果 (True 或 False)。
    # 任務報告: 流程結束後，呼叫 bot.report_status() 取得詳細報告並印出來。
# except 區塊 (意外處理):
    # except KeyboardInterrupt: 
    # 如果使用者在過程中按下 Ctrl+C，這個區塊會被觸發，印出訊息並準備結束程式。
    # except Exception as e: 這是一個萬能的錯誤捕手。
    # 如果程式在任何地方發生了未被處理的錯誤，它會捕獲這個錯誤，
    # 記錄詳細的日誌 (exc_info=True)，並給出故障排除建議，然後準備結束程式。
# finally 區塊 (無論如何都會執行): 
    # 這段程式碼是程式健壯性的最後一道防線。 
    # 無論 try 區塊是成功完成、被 Ctrl+C 中斷、還是發生了未知錯誤，
    # finally 區塊的程式碼永遠會被執行。
    # if args.pause_on_exit:: 根據命令列參數，
    # 決定是等待使用者按 Enter 還是自動等待幾秒。這對於防止視窗閃退非常有用。
    # driver.quit(): 最關鍵的清理工作。
    # 確保瀏覽器和相關進程被徹底關閉，釋放電腦資源，避免「殭屍進程」的產生。
def main():
    """
    主程式入口
    協調整個購票流程的執行
    """
    # 初始化
    args = parse_args()
    
    # 顯示啟動資訊
    # print_banner()
    print_config_info(args)
    
    # 確保目錄存在
    ensure_directories()
    
    # 預載 OCR 模型
    preload_ocr_model()
    
    # 啟動瀏覽器
    logger.info("\n🌐 正在啟動瀏覽器...")
    driver = setup_driver(headless=args.headless)
    
    try:
        # 建立機器人實例
        logger.info("🤖 正在初始化購票機器人...")
        bot = TicketBot(driver)
        
        # 載入登入會話
        logger.info("\n🔐 正在處理登入...")
        bot.load_login_session(interactive=args.interactive)
        
        # 確認準備就緒
        logger.info("\n✅ 機器人準備就緒！")
        
        # 執行購票流程
        success = bot.start_booking(
            start_time=args.start_time,
            prepare_minutes=args.prepare_minutes
        )
        
        # 顯示最終報告
        logger.info("\n" + "=" * 60)
        logger.info("📊 最終執行報告")
        logger.info("=" * 60)
        
        status_report = bot.report_status()
        logger.info(f"狀態: {status_report['status']}")
        logger.info(f"目標場次: {status_report['target_show']}")
        logger.info(f"購買張數: {status_report['ticket_count']}")
        
        if status_report.get('duration_seconds'):
            logger.info(f"執行時間: {status_report['duration_seconds']:.2f} 秒")
        
        if status_report['error_message']:
            logger.error(f"錯誤訊息: {status_report['error_message']}")
        
        logger.info("=" * 60)
        
        # 根據結果顯示不同訊息
        if success:
            logger.info("\n🎉 恭喜！購票流程已完成")
            logger.info("📌 請檢查瀏覽器確認訂單狀態")
            logger.info("📌 如果看到付款頁面，請儘速完成付款")
        else:
            logger.warning("\n⚠️ 購票流程未能完成")
            logger.info("💡 建議操作：")
            logger.info("   1. 檢查瀏覽器畫面，確認當前狀態")
            logger.info("   2. 查看上方日誌，了解失敗原因")
            logger.info("   3. 如果是驗證碼問題，可以嘗試重新執行")
            logger.info("   4. 如果是場次售完，請選擇其他場次")
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️ 使用者中斷程式")
        logger.info("機器人已停止")
        
    except Exception as e:
        logger.error(f"\n❌ 程式執行過程發生未預期的錯誤")
        logger.error(f"錯誤詳情: {e}", exc_info=True)
        logger.info("\n💡 故障排除建議：")
        logger.info("   1. 檢查網路連線是否正常")
        logger.info("   2. 確認活動網址是否正確")
        logger.info("   3. 檢查是否有網站維護或異常")
        logger.info("   4. 嘗試使用 --interactive 模式手動操作")
        
    finally:
        """
        # 結束前的處理
        if args.pause_on_exit:
            logger.info("\n⏸️  程式執行完畢")
            input("按 Enter 鍵關閉瀏覽器...")
        else:
            logger.info("\n⏸️  等待 5 秒後自動關閉瀏覽器...")
            import time
            time.sleep(5)
        """
        logger.info("\n⏸️  程式執行完畢")
        input("按 Enter 鍵關閉瀏覽器...")
        # 關閉瀏覽器
        try:
            driver.quit()
            logger.info("🚪 瀏覽器已關閉")
        except Exception as e:
            logger.error(f"❌ 關閉瀏覽器時發生錯誤: {e}")
        
        logger.info("\n👋 感謝使用拓元購票機器人！")
        logger.info("=" * 60)


def run_app(config_path=None):
    """
    應用程式入口（供套件調用）
    保持向後兼容性
    
    Args:
        config_path: 配置檔案路徑（保留但未使用，為了兼容性）
    """
    logger.info("🚀 以套件模式啟動購票機器人")
    main()


if __name__ == "__main__":
    main()