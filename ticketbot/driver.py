"""
driver.py

拓元購票機器人 - 瀏覽器驅動模組
設定並啟動 Chrome 瀏覽器
"""


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from .logger import setup_logger

logger = setup_logger(__name__)


def setup_driver(headless=False):
    """
    設定並啟動 Chrome 瀏覽器
    
    Args:
        headless (bool): 是否使用無頭模式
        
    Returns:
        webdriver.Chrome: 瀏覽器驅動實例
    """
    service = Service()
    options = webdriver.ChromeOptions()
    
    # 視窗設定
    if headless:
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        logger.info("使用無頭模式啟動瀏覽器")
    else:
        options.add_argument("--start-maximized")
        logger.info("使用視窗模式啟動瀏覽器")
    
    # 隱藏 automation 標記，避免被網站偵測
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # 停用一些不需要的功能以提升效能
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    
    driver = webdriver.Chrome(options=options, service=service)
    
    # 移除 webdriver 屬性
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    logger.info("✅ 瀏覽器驅動已啟動")
    return driver