"""
ticket_bot.py

購票機器人核心類別 - 協調所有模組完成購票流程
職責：
- 協調購票流程（登入 → 選場次 → 選座位 → 選票數 → 驗證碼 → 提交）
- 管理機器人狀態
- 處理異常和重試邏輯
- 報告購票狀態
"""


import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any
from selenium.webdriver.common.by import By

# 導入自定義模組
from .web_client import WebClient
from .selector import Selector
from .captcha_solver import CaptchaSolver
from . import config
from . import cookies
from . import purchase
from .logger import setup_logger

logger = setup_logger(__name__)


# State Machine 狀態機
# Enum 枚舉 : 定義了機器人所有可能的狀態
class BotStatus(Enum):
    """機器人狀態枚舉"""
    IDLE = "閒置"
    INITIALIZING = "初始化中"
    WAITING = "等待開賣"
    LOGGING_IN = "登入中"
    SELECTING_SHOW = "選擇場次中"
    SELECTING_AREA = "選擇區域中"
    SELECTING_TICKETS = "選擇票數中"
    SOLVING_CAPTCHA = "處理驗證碼中"
    SUBMITTING = "提交中"
    SUCCESS = "購票成功"
    FAILED = "購票失敗"
    ERROR = "發生錯誤"

# 核心方法解析
class TicketBot:
    """
    購票機器人核心類別
    協調所有模組完成購票流程，管理狀態和錯誤處理
    """
    # __init__(self, driver, bot_config=None) - 初始化
    # 功能：物件被建立時執行的函式，負責完成所有前置準備。
    # 參數:
    #   driver: Selenium WebDriver 的物件。這是從外部傳入的瀏覽器控制器，
    #       讓 TicketBot 可以接管一個已經設定好的瀏覽器。
    #   bot_config: Dict[str, Any] = None: 一個可選的設定字典。
    #       如果提供了這個字典，機器人就會使用它；
    #       如果沒有提供 (None)，
    #       則會透過 _load_default_config() 從 config.py 載入預設設定。
    # 流程:
    #   1.初始化內部狀態變數 (self.status, self.error_message 等)。
    #   2.載入設定 (self.config)。
    #   3.實例化所有專家模組 (WebClient, Selector, CaptchaSolver)。
    #   4.從設定中讀取搶票目標 (target_show, game_url 等) 並存為實例屬性。
    #   5.印出初始化的日誌訊息。
    def __init__(self, driver, bot_config: Dict[str, Any] = None):
        """
        初始化購票機器人
        
        Args:
            driver: Selenium WebDriver 實例
            bot_config: 機器人配置字典（可選，預設使用 config 模組） 
        """
        # 初始化內部狀態變數 (self.status, self.error_message 等)。
        self.status = BotStatus.INITIALIZING
        self.error_message = ""
        self.start_time = None
        self.end_time = None
        
        # 載入設定 (self.config)
        self.config = bot_config or self._load_default_config()
        
        # 初始化各個模組
        self.web_client = WebClient(driver)
        self.selector = Selector(self.web_client, self.config)
        self.captcha_solver = CaptchaSolver(self.web_client)
        
        # 購票目標
        self.target_show = self.config.get('TARGET_DATE')
        self.target_area = self.config.get('TARGET_AREA')
        self.ticket_count = self.config.get('TICKET_VALUE')
        self.game_url = self.config.get('GAME_URL')
        # 重試配置
        self.max_captcha_retry = self.config.get('MAX_CAPTCHA_RETRY', 5)
        
        # 印出初始化的日誌訊息
        logger.info("🤖 TicketBot 初始化完成")
        logger.info(f"   目標活動: {self.game_url}")
        logger.info(f"   目標場次: {self.target_show}")
        logger.info(f"   購買張數: {self.ticket_count}")
        
        self.status = BotStatus.IDLE
    
    # 回傳一個字典 (Dictionary)，其中字典的鍵 (key) 是字串 (string)，而值 (value) 可以是任何型別 (Any)。
    # getattr(config, 'TARGET_AREA', None)
    # 用途: 你想要鎖定的目標區域，例如演唱會的「A區」或「搖滾區」。
    # getattr:「嘗試從 config 物件中取得 TARGET_AREA 這個屬性，
    # 如果找不到，就使用 None 作為預設值」。
    # 這表示 TARGET_AREA 是一個可選填的設定。如果沒有指定，程式可能就會選擇任何有空位的區域。
    def _load_default_config(self) -> Dict[str, Any]:
        """
        載入預設配置
        
        Returns:
            dict: 配置字典
        """
        return {
            'GAME_URL': config.GAME_URL,
            'TARGET_DATE': config.TARGET_DATE,
            'TARGET_AREA': getattr(config, 'TARGET_AREA', None),
            'TICKET_VALUE': config.TICKET_VALUE,
            'MAX_CAPTCHA_RETRY': 5,
        }
    
    # set_target(...) - 動態設定目標
    # 功能：允許在機器人建立之後，
    # 動態地修改搶票的目標（例如場次、區域、張數）。這增加了機器人的彈性。
    def set_target(self, show_id: str = None, area: str = None, count: int = None):
        """
        設定購票目標
        
        Args:
            show_id: 目標場次 ID 或日期
            area: 目標座位區域
            count: 購買張數
        """
        if show_id:
            self.target_show = show_id
            self.config['TARGET_DATE'] = show_id
            logger.info(f"🎯 設定目標場次: {show_id}")
        
        if area:
            self.target_area = area
            self.config['TARGET_AREA'] = area
            logger.info(f"🎯 設定目標區域: {area}")
        
        if count:
            self.ticket_count = count
            self.config['TICKET_VALUE'] = count
            logger.info(f"🎯 設定購買張數: {count}")
        
        # 更新 Selector 的配置
        self.selector.update_target(
            target_date=self.target_show,
            target_area=self.target_area,
            ticket_count=self.ticket_count
        )
    
    # load_login_session(...) - 處理登入
    # 功能：負責處理拓元網站的登入狀態，這是搶票的第一步。
    # 參數：
    #   interactive: bool = False: 「互動模式」設定
    # 流程:
    # 1.先前往活動頁面。
    # 2.嘗試從 cookies 模組載入之前儲存的 Cookie (登入憑證)。
    # 3.如果載入成功，就刷新頁面，完成自動登入。
    # 4.如果 Cookie 載入失敗，則檢查是否為互動模式：
    #   是 (interactive=True)：程式會暫停，等待使用者手動在瀏覽器中登入，登入成功後會自動儲存新的 Cookie 供下次使用。
    #   否 (interactive=False)：程式會印出警告，並以「未登入」的訪客狀態繼續。
    def load_login_session(self, cookie_file: str = None, interactive: bool = False) -> bool:
        """
        載入登入會話（Cookie）
        
        Args:
            cookie_file: Cookie 檔案路徑（可選）
            interactive: 是否進入互動模式等待使用者手動登入
        
        Returns:
            bool: 是否成功載入登入資訊
        """
        try:
            self.status = BotStatus.LOGGING_IN
            logger.info("🔐 正在載入登入資訊...")
            
            # 先前往活動頁面
            self.web_client.load_page(self.game_url)
            
            # 嘗試載入 Cookie
            cookie_loaded = cookies.load_cookies(self.web_client.driver)
            
            if cookie_loaded:
                logger.info("✅ Cookie 載入成功")
                self.web_client.refresh_page()
                return True
            
            # Cookie 不存在，處理互動模式
            if interactive:
                logger.info("⏳ 進入互動模式，請手動登入...")
                input("登入完成請按 Enter...")
                # cookies.waiting_for_users(self.web_client.driver)
                cookies.save_cookies(self.web_client.driver)
                logger.info("✅ 登入資訊已儲存")
                return True
            else:
                logger.warning("⚠️ Cookie 不存在且非互動模式，將以訪客身份繼續")
                return False
                
        except Exception as e:
            logger.error(f"❌ 載入登入資訊失敗: {e}")
            self.error_message = f"登入失敗: {e}"
            return False
    
    # wait_until_start_time(...) - 智慧等待
    # 功能：控制機器人從容不迫地等待到開賣時間。
    # 流程：
    # 1.它會先計算一個 ready_time (開賣時間 - 提前準備分鐘數)。
    # 2.如果離 ready_time 還很久，它會用 time.sleep() 進行一次長等待。
    # 3.進入 ready_time 後，它會開始一個高頻率的檢查迴圈 (while True)：
    #   離開賣還有一段時間 (>30秒)，就低頻等待 (15秒檢查一次)。
    #   快開賣時 (<30秒)，就高頻等待 (1秒檢查一次)，以確保準時刷新。
    # 4.時間一到，立刻刷新頁面，進入戰鬥狀態。
    def wait_until_start_time(self, start_time: datetime, prepare_minutes: int = 5):
        """
        等待直到開賣時間
        
        Args:
            start_time: 開賣時間
            prepare_minutes: 提前準備分鐘數
        """
        if not start_time:
            logger.info("未指定開賣時間，立即進入搶票流程")
            self.web_client.refresh_page()
            return
        
        self.status = BotStatus.WAITING
        now = datetime.now()
        ready_time = start_time - timedelta(minutes=prepare_minutes)
        
        # 等待到預登入時間
        if now < ready_time:
            wait_seconds = (ready_time - now).total_seconds()
            logger.info(f"⏰ 等待 {wait_seconds/60:.1f} 分鐘到預登入時間...")
            logger.info(f"   預登入時間: {ready_time.strftime('%Y-%m-%d %H:%M:%S')}")
            time.sleep(wait_seconds)
        
        logger.info(f"✅ 已進入預登入階段，將在 {start_time.strftime('%H:%M:%S')} 自動刷新搶票")
        
        # 高頻等待開賣時間
        while True:
            now = datetime.now()
            diff = (start_time - now).total_seconds()
            
            if diff <= 0:
                logger.info("🚀 開賣時間到！立即刷新...")
                self.web_client.refresh_page()
                break
            elif diff > 30:
                logger.info(f"⏳ 距離開賣還有 {diff:.1f} 秒，低頻等待中...")
                time.sleep(15)
            else:
                logger.info(f"⏳ 距離開賣 {diff:.1f} 秒，高頻等待...")
                time.sleep(1)
    
    # _navigate_to_buy_page() - 內部方法：前往購票頁
    # 功能：從活動主頁點擊「立即購票」按鈕，跳轉到選擇場次的頁面。
    # 命名慣例：方法名稱前的底線 _ 是一個 Python 的慣例，
    # 代表這是一個「內部」或「私有」方法，不建議從類別的外部直接呼叫它。
    def _navigate_to_buy_page(self) -> bool:
        """
        導航到立即購票頁面（內部方法）
        
        Returns:
            bool: 是否成功導航
        """
        try:
            logger.info("🎫 正在導航到購票頁面...")
            
            # 等待並點擊「立即購票」按鈕
            buy_link = self.web_client.wait_for_element(By.CSS_SELECTOR, "li.buy a", timeout=10)
            url = self.web_client.get_element_attribute(By.CSS_SELECTOR, "li.buy a", "href")
            
            # 補上完整 domain
            if url.startswith("/"):
                url = "https://tixcraft.com" + url
            
            # 跳轉到購票頁面
            self.web_client.load_page(url)
            logger.info("✅ 已進入購票頁面")
            return True
            
        except Exception as e:
            logger.error(f"❌ 導航到購票頁面失敗: {e}")
            raise Exception("無法進入購票頁面") from e
    
    # _handle_captcha_with_retry() - 內部方法：處理驗證碼 (帶重試)
    # 功能：這是整個機器人最關鍵的攻堅部分，負責處理最容易失敗的驗證碼環節。
    # 流程：
    # 1.使用一個 for 迴圈來實現重試機制，最多重試 max_captcha_retry 次
    # 2.在迴圈中，它會依序執行：重新選擇票數 -> 呼叫 CaptchaSolver 辨識並填入驗證碼 -> 提交表單。
    # 3.提交後，檢查頁面是否出現驗證碼錯誤的訊息。
    # 4.如果有錯誤，就印出警告，等待一下，然後 continue 進入下一次重試。
    # 5.如果沒有錯誤，表示成功，就回傳 True 並跳出迴圈。
    # 6.如果所有重試次數都用完還是失敗，就會拋出一個例外。
    def _handle_captcha_with_retry(self) -> bool:
        """
        處理驗證碼（帶重試機制，內部方法）
        
        Returns:
            bool: 是否成功通過驗證碼
        """
        for attempt in range(1, self.max_captcha_retry + 1):
            try:
                logger.info(f"\n--- 驗證碼處理 (第 {attempt}/{self.max_captcha_retry} 次) ---")
                
                # 選擇票數（每次重試都需要重新選擇）
                self.selector.select_ticket_count()
                
                # 解決驗證碼並填入
                captcha_text = self.captcha_solver.solve_and_fill()
                
                # 提交表單
                logger.info("📤 正在提交購票表單...")
                purchase.submit_booking(self.web_client.driver)

                # 檢查是否有驗證碼錯誤
                has_error, error_msg = self.captcha_solver.verify_and_handle_error()
                
                if has_error:
                    logger.warning(f"⚠️ {error_msg}，準備重試...")
                    if attempt < self.max_captcha_retry:
                        continue
                    else:
                        raise Exception("已達最大驗證碼重試次數")
                else:
                    logger.info("🎉 驗證碼正確，已成功進入下一步！")
                    return True
                    
            except Exception as e:
                logger.error(f"❌ 第 {attempt} 次驗證碼處理失敗: {e}")
                if attempt == self.max_captcha_retry:
                    raise Exception(f"驗證碼處理失敗（{self.max_captcha_retry} 次重試）") from e
        
        return False
    
    # 功能：這是啟動整個購票流程的公開方法。
    #       main.py 就是透過呼叫這個方法來啟動機器人。
    # 流程：
    # 它像一個劇本，按照順序呼叫其他內部方法來完成一個完整的購票流程。
    # 步驟 0: 等待開賣時間 
    # -> 步驟 1: 前往購票頁面 
    # -> 步驟 2: 選擇場次 
    # -> 步驟 3: 選擇座位區域 
    # -> 步驟 4: 處理驗證碼並提交。
    # 使用 try...except... 結構來捕捉所有可能的錯誤，
    # 包括使用者手動按 Ctrl+C (KeyboardInterrupt) 中斷，並在出錯時更新機器人狀態。
    # 最後根據結果更新狀態為 SUCCESS 或 FAILED/ERROR。
    def start_booking(self, start_time: datetime = None, prepare_minutes: int = 5) -> bool:
        """
        開始購票流程（主要入口方法）
        
        Args:
            start_time: 開賣時間（可選）
            prepare_minutes: 提前準備分鐘數
        
        Returns:
            bool: 是否購票成功
        """
        self.start_time = datetime.now()
        
        try:
            logger.info("=" * 60)
            logger.info("🤖 開始購票流程")
            logger.info("=" * 60)
            
            # 步驟 0: 等待開賣時間
            if start_time:
                self.wait_until_start_time(start_time, prepare_minutes)
            
            # 步驟 1: 導航到購票頁面
            logger.info("\n--- 步驟 1: 前往購票頁面 ---")
            self._navigate_to_buy_page()
            
            # 步驟 2: 選擇場次
            logger.info("\n--- 步驟 2: 選擇場次 ---")
            self.status = BotStatus.SELECTING_SHOW
            self.selector.select_show()
            
            # 步驟 3: 選擇區域
            logger.info("\n--- 步驟 3: 選擇座位區域 ---")
            self.status = BotStatus.SELECTING_AREA
            self.selector.select_area()
            
            # 步驟 4: 處理驗證碼並提交
            logger.info("\n--- 步驟 4: 處理驗證碼並提交 ---")
            self.status = BotStatus.SOLVING_CAPTCHA
            success = self._handle_captcha_with_retry()
            
            if success:
                self.status = BotStatus.SUCCESS
                self.end_time = datetime.now()
                duration = (self.end_time - self.start_time).total_seconds()
                
                logger.info("\n" + "=" * 60)
                logger.info("🎉 購票流程完成！")
                logger.info(f"⏱️  總耗時: {duration:.2f} 秒")
                logger.info("=" * 60)
                logger.info("請檢查瀏覽器畫面確認訂單狀態")
                return True
            else:
                raise Exception("購票流程未能完成")
                
        except KeyboardInterrupt:
            logger.warning("\n⚠️ 使用者中斷程式")
            self.status = BotStatus.FAILED
            self.error_message = "使用者中斷"
            return False
            
        except Exception as e:
            logger.error(f"\n❌ 購票流程發生錯誤: {e}")
            self.status = BotStatus.ERROR
            self.error_message = str(e)
            self.end_time = datetime.now()
            return False
    
    # report_status(): 回傳一個包含所有詳細資訊的字典，方便記錄或顯示。
    def report_status(self) -> Dict[str, Any]:
        """
        回報當前機器人狀態
        
        Returns:
            dict: 狀態報告，包含當前狀態、錯誤訊息、執行時間等
        """
        report = {
            'status': self.status.value,
            'target_show': self.target_show,
            'target_area': self.target_area,
            'ticket_count': self.ticket_count,
            'error_message': self.error_message,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
        }
        
        # 計算執行時間
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
            report['duration_seconds'] = duration
        
        return report
    
    # get_status(): 回傳當前的 BotStatus 枚舉。
    def get_status(self) -> BotStatus:
        """
        取得當前狀態
        
        Returns:
            BotStatus: 當前狀態枚舉
        """
        return self.status
    
    def is_success(self) -> bool:
        """
        檢查是否購票成功
        
        Returns:
            bool: 是否成功
        """
        return self.status == BotStatus.SUCCESS
    
    def is_running(self) -> bool:
        """
        檢查機器人是否正在執行
        
        Returns:
            bool: 是否正在執行
        """
        return self.status not in [
            BotStatus.IDLE,
            BotStatus.SUCCESS,
            BotStatus.FAILED,
            BotStatus.ERROR
        ]
    
    # reset(): 重置機器人的所有狀態，讓它可以重新執行一次新的搶票任務。
    def reset(self):
        """
        重置機器人狀態
        用於重新開始購票流程
        """
        self.status = BotStatus.IDLE
        self.error_message = ""
        self.start_time = None
        self.end_time = None
        logger.info("🔄 機器人狀態已重置")