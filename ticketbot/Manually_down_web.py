"""
1.設定初始網址
2.執行後 手動到需要的網頁
3.回到終端機案 Enter
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import os

# --- 設定變數 ---
# ⚠️ 請將這個 URL 替換為您需要開始操作的網址 (例如：反機器人頁面或登入頁)
INITIAL_URL = "https://tixcraft.com/activity/detail/25_ksmasters" 

# --- 啟動瀏覽器 ---
try:
    # 設置 Chrome 選項 (讓瀏覽器更容易操作，不要用無頭模式)
    options = Options()
    # 建議不使用 --headless，讓您可以看見視窗並手動操作
    
    # 啟動 WebDriver
    # 確保您的 WebDriver 檔案 (例如 chromedriver.exe) 位於系統路徑或被正確引用
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1200, 800)
    
    # 導航到初始頁面
    print(f"導航至初始網址: {INITIAL_URL}")
    driver.get(INITIAL_URL)
    
    # =========================================================================
    # 🔴 手動操作等待點 (MANUAL ACTION BREAKPOINT) 🔴
    # =========================================================================
    
    print("\n" + "="*50)
    print("        請在瀏覽器視窗中完成所有手動操作 (例如:")
    print("        1. 通過反機器人驗證 (PoW/reCAPTCHA)")
    print("        2. 登入帳號 (如果需要)")
    print("        3. 點擊進入到最終的『座位選擇』頁面")
    print("        \n        完成後，請回到此控制台視窗，按下 ENTER 鍵繼續...")
    print("="*50 + "\n")
    
    # 等待使用者輸入 Enter 鍵
    input("按下 ENTER 鍵繼續抓取網頁原始碼...\n")
    
    # =========================================================================
    # 🟢 繼續執行 (GRABBING CODE) 🟢
    # =========================================================================
    
    print(f"繼續執行。當前網址: {driver.current_url}")
    
    # 獲取當前頁面（您手動操作後停留的頁面）的完整原始碼
    page_source = driver.page_source
    
    # 將原始碼儲存到檔案
    # 使用當前時間作為檔案名的一部分，避免覆蓋
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    file_name = f"page_source_manual_{timestamp}.html"
    
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(page_source)
    
    print(f"\n✅ 原始碼已成功儲存到檔案: {file_name}")
    print("您可以從檔案中找到您需要的選位邏輯 (例如 `areaUrlList` 等)。")
    
except Exception as e:
    print(f"\n❌ 程式碼執行出錯: {e}")
    
finally:
    # 關閉瀏覽器
    if 'driver' in locals():
        driver.quit()