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

import re
import os
import pickle
import time
from urllib.parse import urljoin
from pathlib import Path

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoAlertPresentException, TimeoutException


# 匯入新的 OCR 模組
from .OCR import ocr_image

# ========== 設定參數 ==========
COOKIES_FILE = "tixcraft_cookies.pkl"
# 修正：使用選場次的網址
GAME_URL = "https://tixcraft.com/activity/detail/25_key"
TARGET_DATE = "2025/10/04 (六) 19:00"
TARGET_TEXT = "2025 KEYLAND：Uncanny Valley in TAIPEI"
TICKET_VALUE = "3"

# OCR 設定
MAX_OCR_RETRY = 5
OCR_OUTPUT_DIR = r"C:\Users\useru\Documents\working\Python\img_captcha"
OCR_LANGUAGES = ['en']  # 英文和繁體中文

# 等待時間設定
SHORT_WAIT = 1.0
LONG_WAIT = 2.0

class TixcraftBot:
    def __init__(self):
        self.driver = None
        # 確保輸出目錄存在
        Path(OCR_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    def setup_driver(self):
        """設定並啟動瀏覽器"""
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        # 隱藏 automation 標記
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        self.driver = webdriver.Chrome(options=options)
        return self.driver
    
    def load_cookies(self):
        """載入已儲存的 cookies"""
        if os.path.exists(COOKIES_FILE):
            print("✅ 偵測到 cookie 檔，嘗試載入保持登入狀態...")
            with open(COOKIES_FILE, "rb") as f:
                cookies = pickle.load(f)
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    print(f"⚠️ 無法加入某個 cookie: {e}")
            self.driver.refresh()
            return True
        else:
            print("⚠️ 沒有 cookie 檔，需要手動登入")
            return False
    
    def save_cookies(self):
        """儲存 cookies"""
        cookies = self.driver.get_cookies()
        with open(COOKIES_FILE, "wb") as f:
            pickle.dump(cookies, f)
        print("✅ 已儲存 cookie，以後可直接登入")
    
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
            print(f"驗證碼圖片 src: {img_src}")
            
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
            print(f"❌ 下載驗證碼圖片失敗: {e}")
            # Fallback: 直接截圖元素
            try:
                img_elem = self.driver.find_element(By.ID, "TicketForm_verifyCode-image")
                return img_elem.screenshot_as_png
            except Exception as e2:
                print(f"❌ 截圖元素也失敗: {e2}")
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
            print(f"✅ 驗證碼圖片已儲存: {filepath}")
            return filepath
        except Exception as e:
            print(f"❌ 儲存圖片失敗: {e}")
            return None
    
    def refresh_captcha(self):
        """刷新驗證碼"""
        try:
            img_elem = self.driver.find_element(By.ID, "TicketForm_verifyCode-image")
            img_elem.click()
            print("✅ 已點擊刷新驗證碼")
        except Exception:
            try:
                img_elem = self.driver.find_element(By.ID, "TicketForm_verifyCode-image")
                self.driver.execute_script("arguments[0].click();", img_elem)
                print("✅ 已用 JS 刷新驗證碼")
            except Exception as e:
                print(f"⚠️ 無法刷新驗證碼: {e}")
        time.sleep(LONG_WAIT)
    
    def solve_captcha(self) -> tuple[bool, str]:
        """
        解決驗證碼（下載圖片並OCR辨識）
        Returns: (是否成功, 辨識結果)
        """
        for attempt in range(1, MAX_OCR_RETRY + 1):
            print(f"\n=== 驗證碼辨識嘗試 {attempt}/{MAX_OCR_RETRY} ===")
            
            # 下載驗證碼圖片
            image_data = self.download_captcha_image()
            if image_data is None:
                print("❌ 無法取得驗證碼圖片")
                continue
            
            # 儲存圖片到檔案
            filename = f"captcha_attempt_{attempt}.png"
            image_path = self.save_image_from_bytes(image_data, filename)
            if image_path is None:
                continue
            
            # 使用新的 OCR 模組辨識
            print(f"🔍 使用 OCR 辨識驗證碼...")
            ocr_results = ocr_image(image_path, langs=OCR_LANGUAGES)
            
            if ocr_results:
                # 取得信心度最高的結果
                best_result = max(ocr_results, key=lambda x: x['confidence'])
                captcha_text = best_result['text'].strip()
                confidence = best_result['confidence']
                
                print(f"✅ OCR 辨識結果: '{captcha_text}' (信心度: {confidence:.2f})")
                
                # 驗證碼通常是 4-6 個字符
                if len(captcha_text) >= 3 and confidence > 0.5:
                    print(f"✅ 驗證碼辨識成功: {captcha_text}")
                    return True, captcha_text
                else:
                    print(f"⚠️ 辨識結果不理想 (長度: {len(captcha_text)}, 信心度: {confidence:.2f})")
            else:
                print("❌ OCR 沒有辨識出任何文字")
            
            # 刷新驗證碼並重試
            if attempt < MAX_OCR_RETRY:
                print("🔄 刷新驗證碼並重試...")
                self.refresh_captcha()
        
        print("❌ 所有驗證碼辨識嘗試都失敗了")
        return False, ""
    
    def fill_captcha(self, captcha_text: str) -> bool:
        """填入驗證碼到輸入框"""
        try:
            input_elem = self.driver.find_element(By.ID, "TicketForm_verifyCode")
            input_elem.clear()
            input_elem.send_keys(captcha_text)
            print(f"✅ 已填入驗證碼: {captcha_text}")
            return True
        except Exception as e:
            print(f"❌ 填入驗證碼失敗: {e}")
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
            print(f"❌ 立即購票失敗: {e}")
            return False


    def select_match_and_buy(self):
        """選擇目標場次並直接跳轉到購票頁面"""
        try:
            # 等待頁面載入
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#gameList table"))
            )

            print(f"🔍 搜尋目標場次: {TARGET_DATE}")
            print(f"🔍 搜尋目標活動: {TARGET_TEXT}")

            # 找到所有購票按鈕
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[data-href*='ticket/area']")

            for button in buttons:
                ticket_url = button.get_attribute("data-href")
                if ticket_url:
                    print(f"✅ 找到購票網址: {ticket_url}")

                    # 直接跳轉到購票頁面
                    self.driver.get(ticket_url)
                    print("✅ 已跳轉到購票頁面")
                    return True

            print("❌ 未找到任何購票按鈕")
            return False

        except Exception as e:
            print(f"❌ 選擇場次失敗: {e}")
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
                    print("✅ 已切換至電腦配位模式")
            except Exception as e:
                print(f"⚠️ 無法切換配位模式: {e}")

            # 取得所有可購票區域
            available_areas = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".zone.area-list li.select_form_a a, .zone.area-list li.select_form_b a"
            )

            if not available_areas:
                print("❌ 沒有找到任何可購票的區域")
                return False

            print(f"🔍 找到 {len(available_areas)} 個可購票區域")

            min_ticket = int(TICKET_VALUE)

            for area in available_areas:
                try:
                    area_id = area.get_attribute("id")
                    area_name = area.text.strip()
                    print(f"🎯 嘗試區域: {area_name} ({area_id})")

                    # ---------- 新增判斷 ----------
                    if "已售完" in area_name:
                        print(f"⛔ {area_name} 已售完，跳過")
                        continue

                    elif "剩餘" in area_name:
                        match = re.search(r"剩餘\s*(\d+)", area_name)
                        if match:
                            remain = int(match.group(1))
                            if remain < min_ticket:
                                print(f"⚠️ {area_name} 剩餘 {remain}，不足 {min_ticket} 張，跳過")
                                continue
                            else:
                                print(f"✅ {area_name} 剩餘 {remain}，符合需求，嘗試進入")

                    elif "熱賣中" in area_name:
                        print(f"🔥 {area_name} 顯示熱賣中，數量未知，嘗試進入")

                    else:
                        print(f"❓ {area_name} 格式不明，跳過")
                        continue
                    # ----------------------------

                    # 使用JavaScript獲取對應購票網址
                    ticket_url = self.driver.execute_script(
                        "return typeof areaUrlList !== 'undefined' && areaUrlList[arguments[0]] ? areaUrlList[arguments[0]] : null;", 
                        area_id
                    )

                    if not ticket_url:
                        print(f"⚠️ 找不到 {area_name} 的購票網址，直接點擊")
                        self.driver.execute_script("arguments[0].click();", area)
                    else:
                        print(f"✅ 取得購票網址: {ticket_url}")
                        self.driver.get(ticket_url)

                    # 等待頁面載入
                    time.sleep(2)

                    try:
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "img[src*='captcha'], #TicketForm_verifyCode-image"))
                        )
                        print(f"🎉 成功進入 {area_name} 購票頁面！")
                        return True
                    except:
                        if self.driver.find_elements(By.CSS_SELECTOR, ".zone.area-list"):
                            print(f"❌ {area_name} 已售完，自動跳回選區頁面")
                            continue

                        error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".alert-danger, .error-message, .fcRed")
                        if error_elements:
                            error_text = error_elements[0].text.strip()
                            print(f"❌ 購票失敗: {error_text}")
                            self.driver.back()
                            time.sleep(1)
                            continue

                        print(f"❌ {area_name} 購票頁面載入異常，嘗試下一個區域")
                        self.driver.back()
                        time.sleep(1)
                        continue

                except Exception as area_error:
                    print(f"❌ 處理區域 {area_name if 'area_name' in locals() else '未知'} 時發生錯誤: {area_error}")
                    try:
                        self.driver.back()
                        time.sleep(1)
                    except:
                        pass
                    continue

            print("❌ 所有可購票區域都已嘗試完畢，均無法成功購票")
            return False

        except Exception as e:
            print(f"❌ 選擇區域過程發生嚴重錯誤: {e}")
            return False


    def select_tickets(self):
        """通用票種和數量選擇函數 - 支援動態票種ID"""
        try:
                    
            # 等待票種列表出現
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "ticketPriceList"))
            )
            print("✅ 票種列表已載入")
            
            # 查找所有票種選擇器（使用CSS選擇器匹配ID模式）
            ticket_selects = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "select[id^='TicketForm_ticketPrice_']"
            )
            
            if not ticket_selects:
                raise Exception("❌ 找不到任何票種選擇器")
            
            print(f"📋 找到 {len(ticket_selects)} 個票種選項")
            
            # 選擇第一個票種
            first_ticket = ticket_selects[0]
            ticket_id = first_ticket.get_attribute("id")
            print(f"🎫 選擇第一個票種 (ID: {ticket_id})")
            
            # 使用 Select 類別操作下拉選單
            select = Select(first_ticket)
            
            # 獲取所有可選數量選項
            available_options = [option.get_attribute("value") for option in select.options]
            print(f"📊 可選數量: {', '.join(available_options)}")
            
            # 智能選擇數量
            if TICKET_VALUE in available_options:
                # 情況1: 想要的數量可用
                select.select_by_value(TICKET_VALUE)
                print(f"✅ 已選擇 {TICKET_VALUE} 張票")
            else:
                # 情況2: 想要的數量不可用，選擇最大值
                # 過濾掉 "0"，找出最大值
                numeric_options = [int(opt) for opt in available_options if opt.isdigit()]
                max_available = max(numeric_options) if numeric_options else 0
                
                if max_available > 0:
                    select.select_by_value(str(max_available))
                    print(f"⚠️  想要 {TICKET_VALUE} 張但不可用，已自動選擇最大值: {max_available} 張")
                else:
                    print("⚠️  警告: 該票種目前無可選數量（僅0可選）")
                    select.select_by_value("0")
            
            # 驗證選擇結果
            selected_value = select.first_selected_option.get_attribute("value")
            print(f"🎉 最終選擇數量: {selected_value} 張")
            
            # 勾選同意條款
            try:
                agree = self.driver.find_element(By.ID, "TicketForm_agree")
                if not agree.is_selected():
                    self.driver.execute_script("arguments[0].click();", agree)
                print("✅ 條款已勾選")
            except Exception as e:
                print(f"❌ 勾選條款失敗: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ 選擇票種失敗: {e}")
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
            
            print("✅ 已提交購票請求 (JS 點擊)")
            return True
        except Exception as e:
            print(f"⚠️ 提交購票失敗: {e}")
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
            print(f"⚠️ 偵測到警告視窗，內容: {alert_text}")
            
            # 點擊「確定」按鈕
            alert.accept()
            print("✅ 已點擊警告視窗的「確定」按鈕，釋放頁面鎖定。")
            return True
            
        except TimeoutException:
            # 如果在設定時間內沒有彈出警告視窗，表示可能成功進入下一步或沒有觸發錯誤
            # 這是正常情況，可以繼續檢查下一頁
            return False
        except NoAlertPresentException:
            # 雖然已經有 TimeoutException 處理了，但仍保留以防萬一
            return False
        except Exception as e:
            print(f"❌ 處理警告視窗時發生意外錯誤: {e}")
            return False

    def run(self):
        """執行完整的購票流程"""
        print("🤖 Tixcraft 購票機器人啟動")
        
        try:
            # 設定瀏覽器
            self.setup_driver()
            # 修正：直接前往選場次頁面
            self.driver.get(GAME_URL)
            
            # 處理登入
            if not self.load_cookies():
                input("👉 請手動登入，完成後按 Enter 繼續...")
                self.save_cookies()
            
            # 等待用戶確認頁面狀態
            #input("👉 如需要請先完成其他準備工作，完成後按 Enter 開始購票流程...")
            
            # 購票流程
            print("\n🎫 開始購票流程...")
            
            # 跳轉到購票頁面
            if not self.start_buy():
                return

            # 選擇場次並跳轉到購票頁面
            if not self.select_match_and_buy():
                return
            
            if not self.select_area():
                return

            MAX_RETRIES = 3 # 設定最大重試次數

            for attempt in range(MAX_RETRIES):
                print(f"\n--- 嘗試提交驗證碼 (第 {attempt + 1} 次) ---")
                # 選擇票種
                if not self.select_tickets():
                    return
                
                # 解決驗證碼
                success, captcha_text = self.solve_captcha()
                if not success:
                    print("❌ 驗證碼辨識失敗，購票流程終止")
                    return
                
                # 填入驗證碼
                if not self.fill_captcha(captcha_text):
                    return
                
                # 提交購票
                if not self.submit_booking():
                    return
                
                is_alert_handled = self.handle_captcha_error_alert()
                if is_alert_handled:
                    # 如果出現警告視窗並點擊了「確定」，表示驗證碼**錯誤**，頁面將刷新。
                    print("🔄 驗證碼錯誤。等待頁面刷新後，進入下一輪重試...")
                    
                    # 您需要在這裡加入等待頁面刷新或等待新的驗證碼元素出現的邏輯
                    # self.wait_for_new_captcha_image()
                else:
                    # 如果沒有警告視窗彈出，則預設為成功進入下一頁
                    print("🎉 未偵測到錯誤警告視窗，預設已成功進入下一步。")
                    break
                if attempt == MAX_RETRIES - 1:
                    print("🛑 已達最大重試次數，終止程序。")

            print("🎉 購票流程完成！")
            
        except Exception as e:
            print(f"❌ 購票過程發生錯誤: {e}")
        
        finally:
            input("按 Enter 關閉瀏覽器...")
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    bot = TixcraftBot()
    bot.run()