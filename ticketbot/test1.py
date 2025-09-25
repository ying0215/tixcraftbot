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

# 匯入新的 OCR 模組
from .OCR import ocr_image

# ========== 設定參數 ==========
COOKIES_FILE = "tixcraft_cookies.pkl"
# 修正：使用選場次的網址
GAME_URL = "https://tixcraft.com/activity/game/25_jiajia"
TARGET_DATE = "2025/09/27 (六)"
TARGET_TEXT = "家家 月部落 Fly to the moon 你給我的月不落現場"
TICKET_VALUE = "2"

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

    def select_date(self):
        """選擇票種和數量"""
        try:
            # 選擇成人票數量
            select_elem = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "dateSearchGameList"))
            )
            select = Select(select_elem)
            select.select_by_value(TARGET_DATE)
            print(f"✅ 已選擇 {TARGET_DATE} ")
            return True
            
        except Exception as e:
            print(f"❌ 選擇票種失敗: {e}")
            return False

    def click_match(self):
        """提交購票請求"""
        try:
            next_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'立即訂購')]"))
            )
            next_btn.click()
            print("✅ 已提交購票請求")
            return True
        except Exception as e:
            print(f"⚠️ 提交購票失敗: {e}")
            return False        

    def select_tickets(self):
        """選擇票種和數量"""
        try:
            # 等待票種頁面載入
            time.sleep(3)
            
            # 選擇成人票數量
            select_elem = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "TicketForm_ticketPrice_09"))
            )
            
            select = Select(select_elem)
            select.select_by_value(TICKET_VALUE)
            print(f"✅ 已選擇 {TICKET_VALUE} 張成人票")
            
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
        """提交購票請求"""
        try:
            next_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'確認張數')]"))
            )
            next_btn.click()
            print("✅ 已提交購票請求")
            return True
        except Exception as e:
            print(f"⚠️ 提交購票失敗: {e}")
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
            
            
            
            # 購票流程
            print("\n🎫 開始購票流程...")

            #  選擇日期
            if not self.select_date():
                return
            
            # 等待用戶確認頁面狀態
            input("👉 如需要請先完成其他準備工作，完成後按 Enter 開始購票流程...")

            # 1. 選擇場次並跳轉到購票頁面
            if not self.click_match():
                return
            
            # 2. 選擇票種
            if not self.select_tickets():
                return
            
            # 3. 解決驗證碼
            success, captcha_text = self.solve_captcha()
            if not success:
                print("❌ 驗證碼辨識失敗，購票流程終止")
                return
            
            # 4. 填入驗證碼
            if not self.fill_captcha(captcha_text):
                return
            
            # 5. 提交購票
            if not self.submit_booking():
                return
            
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