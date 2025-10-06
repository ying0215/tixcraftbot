"""
tixcraft_bot.py

拓元購票機器人
功能：
- 自動登入並保持會話
- 選擇指定場次和票種
- 下載驗證碼圖片並使用 OCR 辨識
- 自動填入驗證碼並提交購票

使用方式：
1. 確保已安裝所需套件
2. 調整設定參數
3. 執行腳本

2025/09/29 (一) 12:00 ~ 23:59 測試這個網頁
https://tixcraft.com/activity/detail/26_1rtp

python -m ticketbot.test1
"""

# 標準庫 (Standard Library)
import argparse
import datetime
import json
import logging
import os
import pickle
import re
import time
from datetime import timedelta
from pathlib import Path
from urllib.parse import urljoin

# ---

# 第三方庫 (Third-Party Libraries)
import numpy as np
import requests

# 爬蟲與自動化 (Selenium)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.common.exceptions import NoAlertPresentException, TimeoutException

# 圖像處理與 OCR
import cv2
import easyocr

# ---

# 自定義模組 (Local Modules)
import config
from cookies import load_cookies_json, save_cookies_json, wait_for_manual_login
from driver import setup_driver
from log import setup_logger
from captcha import download_captcha_image, refresh_captcha, fill_captcha
from .OCR import ocr_image, get_reader
from purchase import (
    select_match_and_buy,
    select_area,
    select_tickets,
    submit_booking,
    handle_captcha_error_alert,
)
import logging
import config
from log import setup_logger
from driver import setup_driver
from cookies import load_cookies_json, save_cookies_json, wait_for_manual_login
from arg_parser import parse_args

# -------------------
# Logging Setup
# -------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# -------------------
# Config & CLI args
# -------------------
DEFAULT_PREPARE_MINUTES = 5
COOKIE_FILE_JSON = "tixcraft_cookies.json"

parser = argparse.ArgumentParser()
parser.add_argument("--start-time", type=str, required=False,
                    help="開賣時間 (格式: YYYY-MM-DD HH:MM:SS，本地時間)。若不指定則立即開始")
parser.add_argument("--prepare-minutes", type=int, default=DEFAULT_PREPARE_MINUTES,
                    help="提前登入等待的分鐘數，預設 5 分鐘")
args = parser.parse_args()

START_TIME = None
if args.start_time:
    START_TIME = datetime.strptime(args.start_time, "%Y-%m-%d %H:%M:%S")
PREPARE_MINUTES = args.prepare_minutes

# ========== 設定參數 ==========

# 修正：使用選場次的網址
GAME_URL = "https://tixcraft.com/activity/detail/25_yama"
TARGET_DATE = "2025/10/16 (四) 20:00"
TARGET_TEXT = "yama Asia Tour 2025 虎視眈眈"
TICKET_VALUE = "2"

# OCR 設定
MAX_OCR_RETRY = 5
OCR_OUTPUT_DIR = r"C:\Users\useru\Documents\working\Python\img_captcha"
OCR_LANGUAGES = ['en']  # 英文

# 等待時間設定
SHORT_WAIT = 1.0
LONG_WAIT = 2.0

# ----------------------------------------------------
# 主程式開始前初始化
# ----------------------------------------------------
def main():
    setup_logger()
    args = parse_args()
    logging.info("購票腳本啟動")
    logging.info(f"目標活動網址：{config.GAME_URL}")

    driver = setup_driver(headless=args.headless)
    bot = TixcraftBot(driver)

    # Cookie 流程
    if not load_cookies_json(driver):
        if args.interactive:
            wait_for_manual_login(driver, wait_seconds=90)
        else:
            logging.warning("Cookie 不存在且非互動模式，略過登入等待")
        save_cookies_json(driver)
        driver.refresh()
    else:
        logging.info("✅ Cookie 載入成功，正在刷新頁面以應用登入狀態...")
        driver.refresh()

    bot.run()

    # 結束前暫停選項
    if args.pause_on_exit:
        input("按 Enter 關閉瀏覽器...")
    driver.quit()
class TixcraftBot:
    def __init__(self, driver):
        self.driver = driver
        Path(OCR_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    def handle_captcha(self):
        img_path = download_captcha_image(self.driver)
        result = self.ocr_recognize(img_path)  # OCR 模組之後抽出
        fill_captcha(self.driver, result)

    def download_captcha_image(self) -> bytes:
        """
        下載驗證碼圖片
        Returns: 圖片的 bytes 資料
        """
        try:
            # 找到驗證碼圖片元素
            img_elem = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "TicketForm_verifyCode-image"))
            )
            
            # 取得圖片 src
            img_src = img_elem.get_attribute("src")
            logger.debug(f"驗證碼圖片 src: {img_src}")
            
            # 建立完整 URL
            captcha_url = urljoin(self.driver.current_url, img_src)
            
            # 取得瀏覽器的 cookies 用於請求
            cookies = {cookie['name']: cookie['value'] for cookie in self.driver.get_cookies()}
            
            # 下載圖片
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(captcha_url, cookies=cookies, headers=headers, timeout=10)
            response.raise_for_status()
            
            return response.content
            
        except Exception as e:
            logger.error(f"❌ 下載驗證碼圖片失敗: {e}")
            # Fallback: 直接截圖元素
            try:
                img_elem = self.driver.find_element(By.ID, "TicketForm_verifyCode-image")
                return img_elem.screenshot_as_png
            except Exception as e2:
                logger.error(f"❌ 截圖元素也失敗: {e2}")
                return None
    
    def save_image_from_bytes(self, image_data: bytes, filename: str) -> str:
        """
        將圖片 bytes 資料儲存為檔案
        Returns: 儲存的檔案路徑
        """
        try:
            filepath = os.path.join(OCR_OUTPUT_DIR, filename)
            with open(filepath, 'wb') as f:
                f.write(image_data)
            logger.info(f"✅ 驗證碼圖片已儲存: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"❌ 儲存圖片失敗: {e}")
            return None
    
    def refresh_captcha(self):
        """刷新驗證碼"""
        try:
            img_elem = self.driver.find_element(By.ID, "TicketForm_verifyCode-image")
            img_elem.click()
            logger.info("✅ 已點擊刷新驗證碼")
        except Exception:
            try:
                img_elem = self.driver.find_element(By.ID, "TicketForm_verifyCode-image")
                self.driver.execute_script("arguments[0].click();", img_elem)
                logger.info("✅ 已用 JS 刷新驗證碼")
            except Exception as e:
                logger.warning(f"⚠️ 無法刷新驗證碼: {e}")
        
    
    def solve_captcha(self) -> tuple[bool, str]:
        """
        解決驗證碼（下載圖片並OCR辨識）
        Returns: (是否成功, 辨識結果)
        """
        WebDriverWait(self.driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#TicketForm_verifyCode-image"))
        )
        for attempt in range(1, MAX_OCR_RETRY + 1):
            logger.info(f"\n=== 驗證碼辨識嘗試 {attempt}/{MAX_OCR_RETRY} ===")
            
            # 下載驗證碼圖片
            image_data = self.download_captcha_image()
            if image_data is None:
                logger.error("❌ 無法取得驗證碼圖片")
                continue
            
            # 儲存圖片到檔案
            filename = f"captcha_attempt_{attempt}.png"
            image_path = self.save_image_from_bytes(image_data, filename)
            if image_path is None:
                continue
            
            # 使用新的 OCR 模組辨識
            logger.debug(f"🔍 使用 OCR 辨識驗證碼...")
            ocr_results = ocr_image(image_path, langs=OCR_LANGUAGES)
            if ocr_results:                
                first_result = ocr_results[0]
                captcha_text = first_result['text'].strip()        
                logger.info(f"✅ OCR 辨識結果: '{captcha_text}'")
                
                # 驗證碼通常是 4-6 個字符
                if len(captcha_text) >= 4 :
                    logger.info(f"✅ 驗證碼辨識成功: {captcha_text}")
                    return True, captcha_text
                else:
                    logger.warning(f"⚠️ 辨識結果不理想 (長度: {len(captcha_text)}")
            else:
                logger.error("❌ OCR 沒有辨識出任何文字")
            
            # 刷新驗證碼並重試
            if attempt < MAX_OCR_RETRY:
                logger.info("🔄 刷新驗證碼並重試...")
                self.refresh_captcha()
        
        logger.error("❌ 所有驗證碼辨識嘗試都失敗了")
        return False, ""
    
    def fill_captcha(self, captcha_text: str) -> bool:
        """填入驗證碼到輸入框"""
        try:
            input_elem = self.driver.find_element(By.ID, "TicketForm_verifyCode")
            input_elem.clear()
            input_elem.send_keys(captcha_text)
            logger.info(f"✅ 已填入驗證碼: {captcha_text}")
            return True
        except Exception as e:
            logger.error(f"❌ 填入驗證碼失敗: {e}")
            return False

    def start_buy(self):
        """直接跳轉到立即購票的網址"""
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
            return True

        except Exception as e:
            logger.error(f"❌ 立即購票失敗: {e}")
            return False


    def select_match_and_buy(self):
        """選擇目標場次並直接跳轉到購票頁面"""
        try:
            # 等待頁面載入
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#gameList table"))
            )

            logger.info(f"🔍 搜尋目標場次: {TARGET_DATE}")
            logger.info(f"🔍 搜尋目標活動: {TARGET_TEXT}")

            # 找到所有購票按鈕
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[data-href*='ticket/area']")

            for button in buttons:
                ticket_url = button.get_attribute("data-href")
                if ticket_url:
                    logger.info(f"✅ 找到購票網址: {ticket_url}")

                    # 直接跳轉到購票頁面
                    self.driver.get(ticket_url)
                    logger.info("✅ 已跳轉到購票頁面")
                    return True

            logger.error("❌ 未找到任何購票按鈕")
            return False

        except Exception as e:
            logger.error(f"❌ 選擇場次失敗: {e}")
            return False

    
    def select_area(self):
        """依序嘗試不同區域，直到找到可購票的為止"""
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".zone.area-list"))
            )

            # 確保選擇「電腦配位」模式（如果有）
            try:
                auto_radio = self.driver.find_element(By.ID, "select_form_auto")
                if not auto_radio.is_selected():
                    auto_radio.click()
                    logger.info("✅ 已切換至電腦配位模式")
            except Exception as e:
                logger.warning(f"⚠️ 無法切換配位模式: {e}")

            # 取得所有可購票區域
            available_areas = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".zone.area-list li.select_form_a a, .zone.area-list li.select_form_b a"
            )

            if not available_areas:
                logger.error("❌ 沒有找到任何可購票的區域")
                return False

            logger.info(f"🔍 找到 {len(available_areas)} 個可購票區域")

            min_ticket = int(TICKET_VALUE)

            for area in available_areas:
                try:
                    area_id = area.get_attribute("id")
                    area_name = area.text.strip()
                    logger.info(f"🎯 嘗試區域: {area_name} ({area_id})")

                    # ---------- 新增判斷 ----------
                    if "已售完" in area_name:
                        logger.warning(f"⛔ {area_name} 已售完，跳過")
                        continue

                    elif "剩餘" in area_name:
                        match = re.search(r"剩餘\s*(\d+)", area_name)
                        if match:
                            remain = int(match.group(1))
                            if remain < min_ticket:
                                logger.warning(f"⚠️ {area_name} 剩餘 {remain}，不足 {min_ticket} 張，跳過")
                                continue
                            else:
                                logger.info(f"✅ {area_name} 剩餘 {remain}，符合需求，嘗試進入")

                    elif "熱賣中" in area_name:
                        logger.info(f"🔥 {area_name} 顯示熱賣中，數量未知，嘗試進入")

                    else:
                        logger.warning(f"❓ {area_name} 格式不明，跳過")
                        continue
                    # ----------------------------

                    # 使用JavaScript獲取對應購票網址
                    ticket_url = self.driver.execute_script(
                        "return typeof areaUrlList !== 'undefined' && areaUrlList[arguments[0]] ? areaUrlList[arguments[0]] : null;", 
                        area_id
                    )

                    if not ticket_url:
                        logger.warning(f"⚠️ 找不到 {area_name} 的購票網址，直接點擊")
                        self.driver.execute_script("arguments[0].click();", area)
                    else:
                        logger.info(f"✅ 取得購票網址: {ticket_url}")
                        self.driver.get(ticket_url)                   

                    try:
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "img[src*='captcha'], #TicketForm_verifyCode-image"))
                        )
                        logger.info(f"🎉 成功進入 {area_name} 購票頁面！")
                        return True
                    except:
                        if self.driver.find_elements(By.CSS_SELECTOR, ".zone.area-list"):
                            logger.warning(f"❌ {area_name} 已售完，自動跳回選區頁面")
                            continue

                        error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".alert-danger, .error-message, .fcRed")
                        if error_elements:
                            error_text = error_elements[0].text.strip()
                            logger.error(f"❌ 購票失敗: {error_text}")
                            self.driver.back()                            
                            continue

                        logger.warning(f"❌ {area_name} 購票頁面載入異常，嘗試下一個區域")
                        self.driver.back()                
                        continue

                except Exception as area_error:
                    logger.error(f"❌ 處理區域 {area_name if 'area_name' in locals() else '未知'} 時發生錯誤: {area_error}")
                    try:
                        self.driver.back()                        
                    except:
                        pass
                    continue

            logger.error("❌ 所有可購票區域都已嘗試完畢，均無法成功購票")
            return False

        except Exception as e:
            logger.error(f"❌ 選擇區域過程發生嚴重錯誤: {e}")
            return False


    def select_tickets(self):
        """通用票種和數量選擇函數 - 支援動態票種ID"""
        try:
                    
            # 等待票種列表出現
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "ticketPriceList"))
            )
            logger.info("✅ 票種列表已載入")
            
            # 查找所有票種選擇器（使用CSS選擇器匹配ID模式）
            ticket_selects = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "select[id^='TicketForm_ticketPrice_']"
            )
            
            if not ticket_selects:
                raise Exception("❌ 找不到任何票種選擇器")
            
            logger.info(f"📋 找到 {len(ticket_selects)} 個票種選項")
            
            # 選擇第一個票種
            first_ticket = ticket_selects[0]
            ticket_id = first_ticket.get_attribute("id")
            logger.info(f"🎫 選擇第一個票種 (ID: {ticket_id})")
            
            # 使用 Select 類別操作下拉選單
            select = Select(first_ticket)
            
            # 獲取所有可選數量選項
            available_options = [option.get_attribute("value") for option in select.options]
            logger.info(f"📊 可選數量: {', '.join(available_options)}")
            
            # 智能選擇數量
            if TICKET_VALUE in available_options:
                # 情況1: 想要的數量可用
                select.select_by_value(TICKET_VALUE)
                logger.info(f"✅ 已選擇 {TICKET_VALUE} 張票")
            else:
                # 情況2: 想要的數量不可用，選擇最大值
                # 過濾掉 "0"，找出最大值
                numeric_options = [int(opt) for opt in available_options if opt.isdigit()]
                max_available = max(numeric_options) if numeric_options else 0
                
                if max_available > 0:
                    select.select_by_value(str(max_available))
                    logger.warning(f"⚠️  想要 {TICKET_VALUE} 張但不可用，已自動選擇最大值: {max_available} 張")
                else:
                    logger.warning(f"⚠️  警告: 該票種目前無可選數量(僅0可選)")
                    select.select_by_value("0")
            
            # 驗證選擇結果
            selected_value = select.first_selected_option.get_attribute("value")
            logger.info(f"🎉 最終選擇數量: {selected_value} 張")
            
            # 勾選同意條款
            try:
                agree = self.driver.find_element(By.ID, "TicketForm_agree")
                if not agree.is_selected():
                    self.driver.execute_script("arguments[0].click();", agree)
                logger.info("✅ 條款已勾選")
            except Exception as e:
                logger.error(f"❌ 勾選條款失敗: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 選擇票種失敗: {e}")
            return False
    
    def submit_booking(self):
        """提交購票請求 (使用 JavaScript 強制點擊)"""
        btn_xpath = "//button[contains(text(),'確認張數') and @type='submit']"
        try:
            # 1. 等待元素載入到 DOM
            next_btn = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, btn_xpath))
            )
            
            # 2. 使用 JavaScript 點擊 (繞過畫面遮擋檢查)
            self.driver.execute_script("arguments[0].click();", next_btn)
            
            logger.info("✅ 已提交購票請求 (JS 點擊)")
            return True
        except Exception as e:
            logger.warning(f"⚠️ 提交購票失敗: {e}")
            return False
    
    def handle_captcha_error_alert(self):
        """
        處理驗證碼錯誤時彈出的瀏覽器原生警告視窗 (Alert)。
        點擊「確定」按鈕來關閉視窗，使主網頁能夠繼續操作或刷新。
        """
        # 設置等待時間，因為警告視窗可能需要短暫時間才彈出
        ALERT_WAIT_TIME = 3 
        
        try:
            # 等待警告視窗出現
            WebDriverWait(self.driver, ALERT_WAIT_TIME).until(
                EC.alert_is_present(), 
                "等待警告視窗超時。"
            )
            
            # 切換到警告視窗
            alert = self.driver.switch_to.alert
            
            # 獲取警告視窗的文字內容 (可選，用於確認是驗證碼錯誤)
            alert_text = alert.text
            logger.warning(f"⚠️ 偵測到警告視窗，內容: {alert_text}")
            
            # 點擊「確定」按鈕
            alert.accept()
            logger.info("✅ 已點擊警告視窗的「確定」按鈕，釋放頁面鎖定。")
            return True
            
        except TimeoutException:
            # 如果在設定時間內沒有彈出警告視窗，表示可能成功進入下一步或沒有觸發錯誤
            # 這是正常情況，可以繼續檢查下一項
            return False
        except NoAlertPresentException:
            # 雖然已經有 TimeoutException 處理了，但仍保留以防萬一
            return False
        except Exception as e:
            logger.error(f"❌ 處理警告視窗時發生意外錯誤: {e}")
            return False

    def run(self):
        # 範例購票流程
        self.driver.get(config.GAME_URL)
        if not select_match_and_buy(self.driver):
            return

        if not select_area(self.driver):
            return

        if not select_tickets(self.driver):
            return

        # 驗證碼處理
        img_path = download_captcha_image(self.driver)
        captcha_text = self.ocr_recognize(img_path)  # OCR 仍暫留
        fill_captcha(self.driver, captcha_text)

        submit_booking(self.driver)
        if handle_captcha_error_alert(self.driver):
            logging.info("重新嘗試驗證碼流程")

if __name__ == "__main__":
    main()