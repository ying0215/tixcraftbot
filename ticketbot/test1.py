"""
test1.py

拓元購票機器人 - 模組化版本
功能：
- 自動登入並保持會話
- 選擇指定場次和票種
- 下載驗證碼圖片並使用 OCR 辨識
- 自動填入驗證碼並提交購票

使用方式：
python -m ticketbot.test1 --start-time "2025-10-16 19:55:00"
"""

import logging
import time
from datetime import timedelta
from pathlib import Path

# 自定義模組（使用相對導入）
from . import config
from .log import setup_logger
from .driver import setup_driver
from .cookies import load_cookies_json, save_cookies_json, wait_for_manual_login
from .arg_parser import parse_args
from .captcha import download_captcha_image, refresh_captcha, fill_captcha
from .purchase import (
    select_match_and_buy,
    select_area,
    select_tickets,
    submit_booking,
    handle_captcha_error_alert,
)
from .OCR import ocr_image, get_reader

logger = logging.getLogger(__name__)


class TixcraftBot:
    """拓元購票機器人主類別"""
    
    def __init__(self, driver):
        self.driver = driver
        Path(config.OCR_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    def start_buy(self):
        """直接跳轉到立即購票的網址"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        try:
            # 等待 <li class="buy a"> 出現
            buy_link = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.buy a"))
            )
            url = buy_link.get_attribute("href")
            # 補上完整 domain
            if url.startswith("/"):
                url = "https://tixcraft.com" + url
            # 跳轉
            self.driver.get(url)
            logger.info("✅ 已跳轉到立即購票頁面")
            return True

        except Exception as e:
            logger.error(f"❌ 立即購票失敗: {e}")
            raise Exception(f"立即購票失敗: {e}")
    
    def solve_captcha(self):
        """
        解決驗證碼（下載圖片並OCR辨識）
        
        Returns:
            str: 辨識出的驗證碼文字
            
        Raises:
            Exception: 所有嘗試都失敗
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        WebDriverWait(self.driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#TicketForm_verifyCode-image"))
        )
        
        for attempt in range(1, config.MAX_OCR_RETRY + 1):
            logger.info(f"\n=== 驗證碼辨識嘗試 {attempt}/{config.MAX_OCR_RETRY} ===")
            
            # 下載驗證碼圖片
            image_path = download_captcha_image(self.driver)
            
            # 使用 OCR 模組辨識
            logger.debug(f"🔍 使用 OCR 辨識驗證碼...")
            ocr_results = ocr_image(image_path, langs=config.OCR_LANGUAGES)
            
            if ocr_results:
                first_result = ocr_results[0]
                captcha_text = first_result['text'].strip()
                logger.info(f"✅ OCR 辨識結果: '{captcha_text}'")
                
                # 驗證碼通常是 4-6 個字符
                if len(captcha_text) >= 4:
                    logger.info(f"✅ 驗證碼辨識成功: {captcha_text}")
                    return captcha_text
                else:
                    logger.warning(f"⚠️ 辨識結果不理想 (長度: {len(captcha_text)})")
            else:
                logger.error("❌ OCR 沒有辨識出任何文字")
            
            # 刷新驗證碼並重試
            if attempt < config.MAX_OCR_RETRY:
                logger.info("🔄 刷新驗證碼並重試...")
                refresh_captcha(self.driver)
                time.sleep(1)
        
        logger.error("❌ 所有驗證碼辨識嘗試都失敗了")
        raise Exception("驗證碼辨識失敗")
    
    def wait_until_start_time(self, start_time, prepare_minutes):
        """
        等待直到開賣時間
        
        Args:
            start_time: 開賣時間 (datetime 物件)
            prepare_minutes: 提前準備分鐘數
        """
        from datetime import datetime
        
        if not start_time:
            logger.info("未指定開賣時間，立即進入搶票流程")
            self.driver.refresh()
            return
        
        now = datetime.now()
        ready_time = start_time - timedelta(minutes=prepare_minutes)

        if now < ready_time:
            wait_seconds = (ready_time - now).total_seconds()
            logger.info(f"⏰ 等待 {wait_seconds/60:.1f} 分鐘到預登入時間...")
            time.sleep(wait_seconds)

        logger.info(f"✅ 已進入預登入階段，將在 {start_time} 自動刷新搶票")

        while True:
            now = datetime.now()
            diff = (start_time - now).total_seconds()
            
            if diff <= 0:
                logger.info("🚀 開賣時間到！立即刷新...")
                self.driver.refresh()
                break
            elif diff > 30:
                logger.info(f"⏳ 距離開賣還有 {diff:.1f} 秒，低頻等待中...")
                time.sleep(15)
            else:
                logger.info(f"⏳ 距離開賣 {diff:.1f} 秒，高頻等待...")
                time.sleep(0.5)
    
    def run(self, start_time=None, prepare_minutes=5):
        """
        執行完整的購票流程
        
        Args:
            start_time: 開賣時間 (datetime 物件或 None)
            prepare_minutes: 提前準備分鐘數
        """
        logger.info("🤖 Tixcraft 購票機器人啟動")
        
        try:
            # 前往活動頁面
            logger.info(f"🌐 前往活動頁面: {config.GAME_URL}")
            self.driver.get(config.GAME_URL)
            
            # 等待直到開賣時間
            self.wait_until_start_time(start_time, prepare_minutes)
            
            # 購票流程開始
            logger.info("\n🎫 開始購票流程...")
            
            # 步驟1: 點擊立即購票
            logger.info("\n--- 步驟1: 立即購票 ---")
            self.start_buy()
            
            # 步驟2: 選擇場次
            logger.info("\n--- 步驟2: 選擇場次 ---")
            select_match_and_buy(self.driver)
            
            # 步驟3: 選擇區域
            logger.info("\n--- 步驟3: 選擇區域 ---")
            select_area(self.driver)
            
            # 步驟4: 驗證碼處理（最多重試5次）
            MAX_CAPTCHA_RETRIES = 5
            for attempt in range(1, MAX_CAPTCHA_RETRIES + 1):
                logger.info(f"\n--- 步驟4: 驗證碼處理 (第 {attempt} 次) ---")
                
                # 選擇票種
                select_tickets(self.driver)
                
                # 解決驗證碼
                captcha_text = self.solve_captcha()
                
                # 填入驗證碼
                fill_captcha(self.driver, captcha_text)
                
                # 提交購票
                submit_booking(self.driver)
                
                # 檢查是否有驗證碼錯誤警告
                has_error = handle_captcha_error_alert(self.driver)
                
                if has_error:
                    logger.warning(f"⚠️ 驗證碼錯誤，進行第 {attempt + 1} 次重試...")
                    time.sleep(1)
                else:
                    logger.info("🎉 驗證碼正確，已成功進入下一步！")
                    break
                
                if attempt == MAX_CAPTCHA_RETRIES:
                    raise Exception("已達最大驗證碼重試次數")
            
            logger.info("\n✅ 購票流程完成！")
            logger.info("請檢查瀏覽器畫面確認訂單狀態")
            
        except KeyboardInterrupt:
            logger.warning("\n⚠️ 使用者中斷程式")
        except Exception as e:
            logger.error(f"\n❌ 購票過程發生錯誤: {e}")
            raise


def main():
    """主程式入口"""
    # 設定日誌
    setup_logger()
    
    # 解析參數
    args = parse_args()
    
    logger.info("=" * 60)
    logger.info("🤖 拓元購票機器人啟動")
    logger.info("=" * 60)
    logger.info(f"目標活動: {config.GAME_URL}")
    logger.info(f"目標場次: {config.TARGET_DATE}")
    logger.info(f"購買張數: {config.TICKET_VALUE}")
    if args.start_time:
        logger.info(f"開賣時間: {args.start_time}")
        logger.info(f"提前準備: {args.prepare_minutes} 分鐘")
    logger.info("=" * 60)
    
    # 預載 OCR 模型
    logger.info("📚 預載 OCR 模型...")
    get_reader(langs=config.OCR_LANGUAGES)
    
    # 啟動瀏覽器
    driver = setup_driver(headless=args.headless)
    
    try:
        # 前往活動頁面
        driver.get(config.GAME_URL)
        
        # Cookie 處理流程
        if not load_cookies_json(driver):
            if args.interactive:
                wait_for_manual_login(driver, wait_seconds=90)
                save_cookies_json(driver)
            else:
                logger.warning("⚠️ Cookie 不存在且非互動模式，略過登入等待")
        
        # 刷新頁面以應用 Cookie
        driver.refresh()
        time.sleep(2)
        
        # 建立機器人實例並執行
        bot = TixcraftBot(driver)
        bot.run(start_time=args.start_time, prepare_minutes=args.prepare_minutes)
        
    except Exception as e:
        logger.error(f"程式執行失敗: {e}")
    finally:
        # 結束前暫停選項
        if args.pause_on_exit:
            input("\n按 Enter 關閉瀏覽器...")
        driver.quit()
        logger.info("瀏覽器已關閉")


if __name__ == "__main__":
    main()