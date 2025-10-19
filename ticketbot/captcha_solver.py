"""
captcha_solver.py

驗證碼解決器 - 整合驗證碼相關功能
職責：
- 下載驗證碼圖片
- 使用 OCR 辨識驗證碼
- 填入驗證碼
- 處理驗證碼錯誤並重試
"""

import time
from pathlib import Path
from typing import Optional, Tuple

# 導入現有模組的功能
from . import captcha
from . import OCR
from . import config
from .logger import setup_logger

logger = setup_logger(__name__)


class CaptchaSolver:
    """
    驗證碼解決器類別
    整合驗證碼下載、OCR 辨識、填寫等功能
    """
    
    # __init__(self, web_client, max_retry=None) - 初始化
    # 參數 (Parameters)：
    # web_client: WebClient 的實例，用來下載圖片和填寫輸入框。
    # max_retry: 最大重試次數。如果外部沒有指定，就從 config.py 讀取預設值。
    # Process :
    # 1.儲存 web_client 和 max_retry
    # 2._init_ocr_reader()：這是一個非常重要的性能優化。
    # 它在機器人一開始初始化時就預先載入 OCR 模型。
    def __init__(self, web_client, max_retry: int = None):
        """
        初始化 CaptchaSolver
        
        Args:
            web_client: WebClient 實例，用於網頁互動
            max_retry: 最大重試次數（預設從 config 讀取）
        """
        self.web_client = web_client
        self.driver = web_client.driver  # 直接引用 driver，方便呼叫現有模組
        self.max_retry = max_retry or config.MAX_OCR_RETRY
        
        # 初始化 OCR 讀取器（預載模型）
        self.ocr_reader = None
        self._init_ocr_reader()
        
        logger.debug(f"CaptchaSolver 已初始化 - 最大重試次數: {self.max_retry}")
    
    def _init_ocr_reader(self):
        """
        初始化 OCR 讀取器
        預載模型以提高首次辨識速度
        """
        try:
            logger.info("📚 正在初始化 OCR 模型...")
            self.ocr_reader = OCR.get_reader(langs=config.OCR_LANGUAGES)
            logger.info("✅ OCR 模型初始化完成")
        except Exception as e:
            logger.warning(f"⚠️ OCR 模型初始化失敗: {e}")
            self.ocr_reader = None
    
    def get_image(self) -> Path:
        """
        從網頁下載驗證碼圖片
        
        Returns:
            Path: 下載的圖片路徑
        
        Raises:
            Exception: 下載失敗時拋出異常
        """
        try:
            logger.debug("📥 正在下載驗證碼圖片...")
            
            # 呼叫現有的 captcha 模組功能
            # download_captcha_image 會：
            # 1. 找到驗證碼圖片元素
            # 2. 取得圖片 URL 或直接截圖
            # 3. 儲存到 OCR_OUTPUT_DIR
            image_path = captcha.download_captcha_image(self.driver, max_keep=5)
            
            logger.info(f"✅ 驗證碼圖片已下載: {image_path}")
            return image_path
            
        except Exception as e:
            logger.error(f"❌ 下載驗證碼圖片失敗: {e}")
            raise Exception("下載驗證碼圖片失敗") from e
    
    # solve(self, image_path=None) - 辨識圖像
    # 功能：對指定的圖片檔案執行 OCR 辨識
    # 執行流程：
    # 如果沒有提供 image_path，就先呼叫 self.get_image() 自動從網頁下載。
    # 呼叫 OCR.ocr_image() 進行辨識。
    # 從辨識結果中提取文字和信心度。
    # 進行一個簡單的健全性檢查 (if len(captcha_text) < 4:)。
    # 如果辨識出的文字長度太短，很可能辨識有誤，直接拋出例外，觸發重試機制。
    # 這可以避免將明顯錯誤的結果填入。
    def solve(self, image_path: Path = None) -> str:
        """
        使用 OCR 辨識驗證碼
        
        Args:
            image_path: 圖片路徑（可選，若未提供則自動下載）
        
        Returns:
            str: 辨識出的驗證碼文字
        
        Raises:
            Exception: 辨識失敗時拋出異常
        """
        try:
            # 如果沒有提供圖片路徑，先下載
            if image_path is None:
                image_path = self.get_image()
            
            logger.debug(f"🔍 正在辨識驗證碼: {image_path}")
            
            # 使用 OCR 模組辨識
            ocr_results = OCR.ocr_image(image_path, langs=config.OCR_LANGUAGES)
            
            if not ocr_results:
                logger.error("❌ OCR 沒有辨識出任何文字")
                raise Exception("OCR 辨識失敗：無結果")
            
            # 取得第一個辨識結果
            first_result = ocr_results[0]
            captcha_text = first_result['text'].strip()
            confidence = first_result.get('confidence', 0)
            
            logger.info(f"✅ OCR 辨識結果: '{captcha_text}' (信心度: {confidence:.2f})")
            
            # 驗證結果長度（驗證碼通常是 4-6 個字符）
            if len(captcha_text) < 4:
                logger.warning(f"⚠️ 辨識結果過短 (長度: {len(captcha_text)})")
                raise Exception(f"驗證碼長度不符預期: {len(captcha_text)}")
            
            return captcha_text
            
        except Exception as e:
            logger.error(f"❌ 驗證碼辨識失敗: {e}")
            raise Exception("驗證碼辨識失敗") from e
    
    def fill_captcha(self, captcha_text: str) -> bool:
        """
        填入驗證碼到輸入框
        
        Args:
            captcha_text: 驗證碼文字
        
        Returns:
            bool: 是否成功填入
        
        Raises:
            Exception: 填入失敗時拋出異常
        """
        try:
            logger.info(f"✍️ 正在填入驗證碼: {captcha_text}")
            
            # 呼叫現有的 captcha 模組功能
            # fill_captcha 會：
            # 1. 找到驗證碼輸入框
            # 2. 填入驗證碼文字
            captcha.fill_captcha(self.driver, captcha_text)
            
            logger.info("✅ 驗證碼已填入")
            return True
            
        except Exception as e:
            logger.error(f"❌ 填入驗證碼失敗: {e}")
            raise Exception("填入驗證碼失敗") from e
    
    def refresh_captcha(self) -> bool:
        """
        刷新驗證碼（重新取得新的驗證碼圖片）
        
        Returns:
            bool: 是否成功刷新
        
        Raises:
            Exception: 刷新失敗時拋出異常
        """
        try:
            logger.info("🔄 正在刷新驗證碼...")
            
            # 呼叫現有的 captcha 模組功能
            # refresh_captcha 會：
            # 1. 找到刷新按鈕
            # 2. 點擊刷新
            # 3. 等待新驗證碼載入
            captcha.refresh_captcha(self.driver)
            logger.info("✅ 驗證碼已刷新")
            return True
            
        except Exception as e:
            logger.error(f"❌ 刷新驗證碼失敗: {e}")
            raise Exception("刷新驗證碼失敗") from e
    
    # solve_with_retry(self) - 帶重試的辨識
    # 功能：這是 solve() 的強化版，也是模組中最核心的重試邏輯所在。
    # 執行流程：
    #用一個 for 迴圈來控制重試次數。
    # 在 try...except 區塊中，嘗試下載並辨識
    # (self.get_image() -> self.solve())。
    # 如果成功，立即 return captcha_text。
    # 如果失敗 (捕捉到 Exception)，記錄警告訊息，並檢查是否還有重試機會。
    # 如果有，就呼叫 self.refresh_captcha() 點擊網頁上的刷新按鈕，
    # 然後進入下一次迴圈。
    # 如果所有重試次數都用完，就拋出最終的例外，宣告失敗。
    def solve_with_retry(self) -> str:
        """
        使用重試機制解決驗證碼
        如果辨識失敗，會自動刷新驗證碼並重試
        
        Returns:
            str: 辨識出的驗證碼文字
        
        Raises:
            Exception: 所有重試都失敗時拋出異常
        """
        last_error = None
        
        for attempt in range(1, self.max_retry + 1):
            try:
                logger.info(f"\n=== 驗證碼辨識嘗試 {attempt}/{self.max_retry} ===")
                
                # 下載並辨識驗證碼
                image_path = self.get_image()
                captcha_text = self.solve(image_path)
                
                # 成功辨識，返回結果
                logger.info(f"✅ 驗證碼辨識成功: {captcha_text}")
                return captcha_text
                
            except Exception as e:
                last_error = e
                logger.warning(f"⚠️ 第 {attempt} 次辨識失敗: {e}")
                
                # 如果還有重試機會，刷新驗證碼
                if attempt < self.max_retry:
                    logger.info(f"🔄 刷新驗證碼並重試...")
                    try:
                        self.refresh_captcha()
                    except Exception as refresh_error:
                        logger.error(f"❌ 刷新驗證碼失敗: {refresh_error}")
                        # 繼續重試，可能頁面會自動更新
        
        # 所有重試都失敗
        logger.error(f"❌ 所有 {self.max_retry} 次驗證碼辨識嘗試都失敗了")
        raise Exception(f"驗證碼辨識失敗（{self.max_retry} 次重試）") from last_error
    
    # verify_and_handle_error(self) - 驗證結果 / 聽取回饋
    # 功能：在機器人提交驗證碼之後，用來檢查網頁上是否跳出了「驗證碼錯誤」之類的提示。
    # 這是驗證碼流程的回饋迴路。
    # 返回值：Tuple[bool, str] - (是否有錯誤, 錯誤訊息)。
    # TicketBot 會根據這個回傳值來決定是繼續下一步，
    # 還是需要再次執行驗證碼處理流程。
    def verify_and_handle_error(self) -> Tuple[bool, str]:
        """
        驗證驗證碼是否正確，並處理錯誤警告
        檢查頁面上是否有驗證碼錯誤的提示
        
        Returns:
            Tuple[bool, str]: (是否有錯誤, 錯誤訊息)
                - (False, "") 表示驗證碼正確
                - (True, "錯誤訊息") 表示驗證碼錯誤
        """
        try:
            logger.debug("🔍 檢查驗證碼是否正確...")
            
            # 呼叫現有的 purchase 模組功能
            # handle_captcha_error_alert 會：
            # 1. 檢查是否有錯誤警告框
            # 2. 如果有，讀取錯誤訊息並關閉警告
            # 3. 返回是否有錯誤
            from . import purchase
            has_error = purchase.handle_captcha_error_alert(self.driver)
            
            if has_error:
                logger.warning("⚠️ 驗證碼錯誤")
                return (True, "驗證碼錯誤")
            else:
                logger.info("✅ 驗證碼正確")
                return (False, "")
                
        except Exception as e:
            logger.error(f"❌ 檢查驗證碼錯誤時發生異常: {e}")
            # 無法確定是否有錯誤，保守起見返回有錯誤
            return (True, f"檢查失敗: {e}")
    # solve_and_fill(self) - 一鍵完成（便捷方法）
    # 功能：這是 TicketBot 最常呼叫的公開介面。
    # 它將整個驗證碼處理流程打包成一個函式。
    # 執行流程：
    # 呼叫 self.solve_with_retry() 取得辨識結果。
    # 呼叫 self.fill_captcha() 將結果填入輸入框。
    def solve_and_fill(self) -> str:
        """
        一次性完成驗證碼的下載、辨識、填入
        這是最常用的便捷方法
        
        Returns:
            str: 辨識並填入的驗證碼文字
        
        Raises:
            Exception: 任何步驟失敗時拋出異常
        """
        try:
            logger.info("🎯 開始驗證碼完整處理流程...")
            
            # 1. 下載並辨識
            captcha_text = self.solve_with_retry()
            
            # 2. 填入驗證碼
            self.fill_captcha(captcha_text)
            
            logger.info("✅ 驗證碼處理完成")
            return captcha_text
            
        except Exception as e:
            logger.error(f"❌ 驗證碼處理流程失敗: {e}")
            raise Exception("驗證碼處理失敗") from e
    
    def get_ocr_stats(self) -> dict:
        """
        取得 OCR 統計資訊（輔助方法）
        
        Returns:
            dict: OCR 統計資訊，包含成功率、平均時間等
        
        Note:
            這是一個輔助方法，供未來增加監控功能使用
        """
        # TODO: 實作 OCR 統計追蹤
        stats = {
            'total_attempts': 0,
            'successful': 0,
            'failed': 0,
            'success_rate': 0.0,
            'avg_time': 0.0
        }
        return stats
    
    def set_max_retry(self, max_retry: int):
        """
        動態設定最大重試次數
        
        Args:
            max_retry: 新的最大重試次數
        """
        self.max_retry = max_retry
        logger.info(f"🔄 更新最大重試次數: {max_retry}")