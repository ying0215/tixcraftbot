"""
web_client.py

網頁互動客戶端 - Selenium Driver 的薄封裝層
職責：
- 載入頁面
- 提交表單
- 取得頁面內容
- 管理 Cookies
"""


from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from .logger import setup_logger

logger = setup_logger(__name__)


class WebClient:
    """
    網頁互動客戶端
    對 Selenium WebDriver 的薄封裝，提供統一的網頁操作接口
    """
    # __init__(self, driver: WebDriver) - 初始化
    # 參數 (Parameters)：
    # (driver: WebDriver): 接收從外部傳入的 Selenium WebDriver 實例。
    # 這種模式稱為「依賴注入」(Dependency Injection)，
    # 讓 WebClient 不需要關心瀏覽器是如何被建立和設定的，增加了靈活度。
    def __init__(self, driver: WebDriver):
        """
        初始化 WebClient
        
        Args:
            driver: Selenium WebDriver 實例
        """
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        logger.debug("WebClient 已初始化")
    
    # load_page(self, url: str, wait_for: tuple = None) - 載入頁面
    # 功能：打開指定的網頁
    # 參數：
    # url: 目標網址。
    # wait_for: 一個可選參數，讓您可以在頁面跳轉後，額外等待某個特定元素出現，
    # 以確認頁面已完全載入。例如 wait_for=(By.ID, "login-button")
    def load_page(self, url: str, wait_for: tuple = None) -> bool:
        """
        載入指定的網頁
        
        Args:
            url: 目標網址
            wait_for: 可選的等待條件 (By, locator)，例如 (By.ID, "element_id")
        
        Returns:
            bool: 是否成功載入
        
        Raises:
            Exception: 載入失敗時拋出異常
        """
        try:
            logger.info(f"🌐 載入頁面: {url}")
            self.driver.get(url)
            
            # 如果指定了等待條件，等待元素出現
            if wait_for:
                by, locator = wait_for
                self.wait.until(EC.presence_of_element_located((by, locator)))
                logger.debug(f"✅ 等待元素出現: {locator}")
            
            logger.info("✅ 頁面載入成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 頁面載入失敗: {e}")
            raise Exception(f"載入頁面失敗: {url}") from e
    
    def refresh_page(self) -> bool:
        """
        刷新當前頁面
        
        Returns:
            bool: 是否成功刷新
        """
        try:
            logger.info("🔄 刷新頁面")
            self.driver.refresh()
            return True
        except Exception as e:
            logger.error(f"❌ 刷新頁面失敗: {e}")
            raise Exception("刷新頁面失敗") from e
    
    def get_page_content(self) -> str:
        """
        取得當前頁面的 HTML 內容
        
        Returns:
            str: 頁面的 HTML 原始碼
        """
        try:
            content = self.driver.page_source
            logger.debug(f"📄 已取得頁面內容 (長度: {len(content)})")
            return content
        except Exception as e:
            logger.error(f"❌ 取得頁面內容失敗: {e}")
            raise Exception("取得頁面內容失敗") from e
    
    def get_current_url(self) -> str:
        """
        取得當前頁面的 URL
        
        Returns:
            str: 當前 URL
        """
        return self.driver.current_url
    
    # 功能：等待並點擊一個網頁元素
    # 參數：
    # by: 定位方式，例如 By.ID, By.CSS_SELECTOR, By.XPATH。
    # locator: 元素的路徑，例如 "#buy-button" 或 "//button[text()='下一步']"
    # 流程: wait.until(EC.element_to_be_clickable(...))。
    # element_to_be_clickable 不僅會等待元素出現在網頁上，
    # 還會確保它是可見的且可點擊的（沒有被其他東西遮擋）。
    # ****這裡之後可能需要修改成js處理****
    def click_element(self, by: By, locator: str, wait_time: int = 10) -> bool:
        """
        點擊指定的網頁元素
        
        Args:
            by: 定位方式 (By.ID, By.CSS_SELECTOR 等)
            locator: 元素定位器
            wait_time: 等待時間（秒）
        
        Returns:
            bool: 是否成功點擊
        
        Raises:
            Exception: 點擊失敗時拋出異常
        """
        try:
            wait = WebDriverWait(self.driver, wait_time)
            element = wait.until(EC.element_to_be_clickable((by, locator)))
            element.click()
            logger.debug(f"✅ 已點擊元素: {locator}")
            return True
        except Exception as e:
            logger.error(f"❌ 點擊元素失敗: {locator} - {e}")
            raise Exception(f"點擊元素失敗: {locator}") from e
    
    # 功能：在指定的輸入框中填入文字。
    # 流程:
    # 1.執行 element.clear() (清空輸入框，防止舊內容干擾)，
    # 2.執行 element.send_keys(text) (模擬鍵盤輸入)。
    def fill_input(self, by: By, locator: str, text: str) -> bool:
        """
        填寫輸入欄位
        
        Args:
            by: 定位方式
            locator: 元素定位器
            text: 要填入的文字
        
        Returns:
            bool: 是否成功填寫
        
        Raises:
            Exception: 填寫失敗時拋出異常
        """
        try:
            element = self.wait.until(EC.presence_of_element_located((by, locator)))
            element.clear()
            element.send_keys(text)
            logger.debug(f"✅ 已填入文字: {locator}")
            return True
        except Exception as e:
            logger.error(f"❌ 填寫輸入失敗: {locator} - {e}")
            raise Exception(f"填寫輸入失敗: {locator}") from e
    
    def submit_form(self, by: By = None, locator: str = None) -> bool:
        """
        提交表單
        
        Args:
            by: 提交按鈕的定位方式（可選）
            locator: 提交按鈕的定位器（可選）
        
        Returns:
            bool: 是否成功提交
        
        Raises:
            Exception: 提交失敗時拋出異常
        """
        try:
            if by and locator:
                # 點擊指定的提交按鈕
                self.click_element(by, locator)
            else:
                # 尋找並點擊通用的提交按鈕
                submit_button = self.driver.find_element(By.CSS_SELECTOR, 
                                                        'button[type="submit"], input[type="submit"]')
                submit_button.click()
            
            logger.info("✅ 表單已提交")
            return True
        except Exception as e:
            logger.error(f"❌ 提交表單失敗: {e}")
            raise Exception("提交表單失敗") from e
    
    # handle_cookies(...) - 管理 Cookies
    # 功能：將所有與 Cookie 相關的操作（讀取、設定、清除）集中管理。
    # TicketBot 在處理登入狀態時，就是透過呼叫這個函式來完成 Cookie 的載入。
    def handle_cookies(self, cookies: list = None, action: str = "load") -> list:
        """
        管理 Cookies
        
        Args:
            cookies: Cookie 列表（當 action='set' 時使用）
            action: 操作類型 ('load' 取得, 'set' 設定, 'clear' 清除)
        
        Returns:
            list: 當 action='load' 時返回 Cookie 列表
        
        Raises:
            Exception: Cookie 操作失敗時拋出異常
        """
        try:
            if action == "load":
                current_cookies = self.driver.get_cookies()
                logger.debug(f"📦 已取得 {len(current_cookies)} 個 Cookies")
                return current_cookies
            
            elif action == "set":
                if not cookies:
                    raise ValueError("設定 Cookies 時必須提供 cookies 參數")
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
                logger.info(f"✅ 已設定 {len(cookies)} 個 Cookies")
                return []
            
            elif action == "clear":
                self.driver.delete_all_cookies()
                logger.info("🗑️ 已清除所有 Cookies")
                return []
            
            else:
                raise ValueError(f"不支援的 action: {action}")
                
        except Exception as e:
            logger.error(f"❌ Cookie 操作失敗: {e}")
            raise Exception(f"Cookie 操作失敗: {action}") from e
    

    # wait_for_element(self, ...) - 等待元素出現
    # 功能：只等待，不操作。用於確認頁面狀態是否正確。
    # wait.until(EC.presence_of_element_located(...))
    # 它只要求元素存在於 DOM (文件物件模型) 中即可，不要求可見或可點擊。
    def wait_for_element(self, by: By, locator: str, timeout: int = 10) -> bool:
        """
        等待元素出現
        
        Args:
            by: 定位方式
            locator: 元素定位器
            timeout: 超時時間（秒）
        
        Returns:
            bool: 元素是否出現
        
        Raises:
            Exception: 等待超時時拋出異常
        """
        try:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(EC.presence_of_element_located((by, locator)))
            logger.debug(f"✅ 元素已出現: {locator}")
            return True
        except Exception as e:
            logger.error(f"❌ 等待元素超時: {locator}")
            raise Exception(f"等待元素超時: {locator}") from e
    
    # 功能：獲取 HTML 標籤的屬性值
    # 對於 <a href="/next-page.html">下一步</a> 這個元素，
    # 可以使用這個函式來獲取 href 屬性的值，也就是 /next-page.html。
    # 這在 _navigate_to_buy_page 中被用來取得購票頁面的連結。
    def get_element_attribute(self, by: By, locator: str, attribute: str) -> str:
        """
        取得元素的屬性值
        
        Args:
            by: 定位方式
            locator: 元素定位器
            attribute: 屬性名稱
        
        Returns:
            str: 屬性值
        """
        try:
            element = self.wait.until(EC.presence_of_element_located((by, locator)))
            value = element.get_attribute(attribute)
            logger.debug(f"📝 取得屬性 {attribute}: {value}")
            return value
        except Exception as e:
            logger.error(f"❌ 取得元素屬性失敗: {locator}.{attribute}")
            raise Exception(f"取得元素屬性失敗: {locator}.{attribute}") from e
    
    # close(self) - 關閉瀏覽器
    # 功能：安全地關閉整個瀏覽器和相關的 WebDriver 進程。
    def close(self):
        """關閉瀏覽器"""
        try:
            self.driver.quit()
            logger.info("🚪 瀏覽器已關閉")
        except Exception as e:
            logger.error(f"❌ 關閉瀏覽器失敗: {e}")