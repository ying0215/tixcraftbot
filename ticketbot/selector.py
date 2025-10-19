"""
selector.py

選擇器模組 - 負責解析網頁並執行選擇邏輯
職責：
- 選擇場次 (select_show)
- 選擇區域/座位 (select_area)
- 選擇票數 (select_ticket_count)
- 解析網頁內容並做出決策
"""

from typing import Optional, Dict, Any
from selenium.webdriver.common.by import By

# 導入現有模組的功能
from . import purchase
from .logger import setup_logger

logger = setup_logger(__name__)


class Selector:
    """
    選擇器類別
    負責解析網頁內容並執行選擇邏輯（場次、座位、票數）
    """
    # _init__(self, web_client, config) - 初始化
    # 功能：建立 Selector 物件，並接收它完成任務所需的兩樣東西：工具和指令。
    # Parameters:
    # web_client: WebClient 的實例。這是 Selector 用來與網頁互動的唯一工具。
    # 它不會直接操作 Selenium driver。
    # config: 設定字典。這是 Selector 的行動指令，告訴它目標是什麼。
    # process:
    # 1.儲存 web_client 和 config
    # 2.從 config 中提取目標參數 
    # (target_date, target_area, ticket_count) 到實例屬性中，
    # 方便內部方法直接取用。
    def __init__(self, web_client, config: Dict[str, Any]):
        """
        初始化 Selector
        
        Args:
            web_client: WebClient 實例，用於網頁互動
            config: 配置字典，包含目標場次、座位偏好、票數等
        """
        self.web_client = web_client
        self.driver = web_client.driver  # 直接引用 driver，方便呼叫現有模組
        self.config = config
        
        # 從配置中提取關鍵參數
        self.target_date = config.get('TARGET_DATE')
        self.target_area = config.get('TARGET_AREA')
        self.ticket_count = config.get('TICKET_VALUE')
        
        logger.debug(f"Selector 已初始化 - 目標場次: {self.target_date}, 票數: {self.ticket_count}")
    
    # select_show(self) - 選擇場次
    # 功能：在列出所有場次的頁面，
    # 找到 config 中指定的 TARGET_DATE 對應的那一場，
    # 並點擊它的「立即訂購」按鈕。
    # 執行方式：它將這個任務委派給了 
    # purchase.select_match_and_buy(self.driver)。
    # 真正的解析和點擊邏輯被封裝在 purchase 模組中。
    def select_show(self) -> bool:
        """
        選擇場次
        解析場次列表，找到目標場次並點擊「立即訂購」
        
        Returns:
            bool: 是否成功選擇場次
        
        Raises:
            Exception: 選擇場次失敗時拋出異常
        """
        try:
            logger.info("🎭 開始選擇場次...")
            logger.info(f"   目標場次: {self.target_date}")
            
            # 呼叫現有的 purchase 模組功能
            # select_match_and_buy 會：
            # 1. 解析場次列表
            # 2. 找到符合 TARGET_DATE 的場次
            # 3. 點擊「立即訂購」按鈕
            purchase.select_match_and_buy(self.driver)
            
            logger.info("✅ 場次選擇成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 選擇場次失敗: {e}")
            raise Exception("選擇場次失敗") from e
    

    # select_area(self) - 選擇座位區域
    # 功能：在選擇座位區域的頁面，
    # 根據 config 中的 TARGET_AREA 來點擊對應的區域。
    # 如果 TARGET_AREA 是空的，它可能會自動選擇第一個有空位的區域
    # 這個邏輯同樣在 purchase 模組裡）。
    def select_area(self) -> bool:
        """
        選擇區域/座位
        解析座位區域列表，根據偏好選擇目標區域
        
        Returns:
            bool: 是否成功選擇區域
        
        Raises:
            Exception: 選擇區域失敗時拋出異常
        """
        try:
            logger.info("💺 開始選擇座位區域...")
            logger.info(f"   目標區域: {self.target_area if self.target_area else '自動選擇'}")
            
            # 呼叫現有的 purchase 模組功能
            # select_area 會：
            # 1. 解析可用的座位區域
            # 2. 根據 TARGET_AREA 配置選擇區域
            # 3. 點擊對應的區域按鈕
            purchase.select_area(self.driver)
            
            logger.info("✅ 座位區域選擇成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 選擇座位區域失敗: {e}")
            raise Exception("選擇座位區域失敗") from e
    
    # select_ticket_count(self) - 選擇票數
    # 功能：在最後確認頁面，找到選擇張數的下拉選單，
    # 並選擇 config 中設定的 TICKET_VALUE
    def select_ticket_count(self) -> bool:
        """
        選擇票數
        在票種選擇頁面設定購買數量
        
        Returns:
            bool: 是否成功選擇票數
        
        Raises:
            Exception: 選擇票數失敗時拋出異常
        """
        try:
            logger.info("🎫 開始選擇票數...")
            logger.info(f"   購買張數: {self.ticket_count}")
            
            # 呼叫現有的 purchase 模組功能
            # select_tickets 會：
            # 1. 找到票種選擇下拉選單
            # 2. 設定購買數量為 TICKET_VALUE
            # 3. 點選同意條款
            purchase.select_tickets(self.driver)
            
            logger.info("✅ 票數選擇成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 選擇票數失敗: {e}")
            raise Exception("選擇票數失敗") from e
    
    def get_show_list(self) -> list:
        """
        取得場次列表（輔助方法）
        解析當前頁面的所有可用場次
        
        Returns:
            list: 場次資訊列表，每個元素為 dict，包含 date, time, status 等
        
        Note:
            這是一個輔助方法，供未來擴展使用
            目前 select_show 直接呼叫 purchase 模組
        """
        try:
            logger.debug("📋 解析場次列表...")
            
            # 這裡可以實作更細緻的場次解析邏輯
            # 例如：返回所有場次的詳細資訊供外部使用
            # 目前先返回空列表，因為實際選擇邏輯在 purchase.py 中
            
            shows = []
            # TODO: 實作詳細的場次解析
            # shows = self._parse_shows_from_page()
            
            logger.debug(f"📋 找到 {len(shows)} 個場次")
            return shows
            
        except Exception as e:
            logger.error(f"❌ 解析場次列表失敗: {e}")
            return []
    
    def get_available_areas(self) -> list:
        """
        取得可用的座位區域列表（輔助方法）
        解析當前頁面的所有可選區域
        
        Returns:
            list: 區域資訊列表，每個元素為 dict，包含 name, available 等
        
        Note:
            這是一個輔助方法，供未來擴展使用
        """
        try:
            logger.debug("📋 解析座位區域列表...")
            
            areas = []
            # TODO: 實作詳細的區域解析
            # areas = self._parse_areas_from_page()
            
            logger.debug(f"📋 找到 {len(areas)} 個可用區域")
            return areas
            
        except Exception as e:
            logger.error(f"❌ 解析座位區域列表失敗: {e}")
            return []
    
    def validate_selection(self) -> Dict[str, bool]:
        """
        驗證當前選擇是否有效（輔助方法）
        檢查場次、區域、票數等選擇是否符合預期
        
        Returns:
            dict: 驗證結果，例如 {'show': True, 'area': True, 'count': True}
        
        Note:
            這是一個輔助方法，供未來增加驗證邏輯使用
        """
        result = {
            'show': False,
            'area': False,
            'count': False
        }
        
        try:
            logger.debug("🔍 驗證選擇結果...")
            
            # TODO: 實作選擇驗證邏輯
            # 例如：檢查當前 URL、頁面元素等，確認選擇成功
            
            # 暫時返回預設值
            result = {
                'show': True,
                'area': True,
                'count': True
            }
            
            logger.debug(f"🔍 驗證結果: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ 驗證選擇失敗: {e}")
            return result
    
    def _parse_shows_from_page(self) -> list:
        """
        從頁面解析場次資訊（私有方法）
        
        Returns:
            list: 解析出的場次列表
        
        Note:
            供內部使用的解析方法
        """
        # TODO: 實作場次解析邏輯
        # 1. 取得頁面內容
        # 2. 使用 BeautifulSoup 或 Selenium 解析
        # 3. 提取場次日期、時間、狀態等資訊
        return []
    
    def _parse_areas_from_page(self) -> list:
        """
        從頁面解析區域資訊（私有方法）
        
        Returns:
            list: 解析出的區域列表
        
        Note:
            供內部使用的解析方法
        """
        # TODO: 實作區域解析邏輯
        return []
    
    # update_target(self, **kwargs) - 更新目標
    # 功能：這是一個非常重要的方法，
    # 它允許外部（主要是 TicketBot）在執行過程中動態地修改 Selector 的目標。
    def update_target(self, **kwargs):
        """
        更新目標選擇配置
        
        Args:
            **kwargs: 可更新的配置項，例如 target_date, target_area, ticket_count
        
        Example:
            selector.update_target(target_date="2025-10-20", ticket_count=2)
        """
        if 'target_date' in kwargs:
            self.target_date = kwargs['target_date']
            self.config['TARGET_DATE'] = kwargs['target_date']
            logger.info(f"🔄 更新目標場次: {self.target_date}")
        
        if 'target_area' in kwargs:
            self.target_area = kwargs['target_area']
            self.config['TARGET_AREA'] = kwargs['target_area']
            logger.info(f"🔄 更新目標區域: {self.target_area}")
        
        if 'ticket_count' in kwargs:
            self.ticket_count = kwargs['ticket_count']
            self.config['TICKET_VALUE'] = kwargs['ticket_count']
            logger.info(f"🔄 更新票數: {self.ticket_count}")