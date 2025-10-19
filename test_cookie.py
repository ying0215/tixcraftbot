# test_cookie.py
from ticketbot.downloader import save_cookie, load_cookie
from ticketbot.config import ensure_directories, COOKIES_DIR

def test_cookie_functions():
    ensure_directories()  # 確保資料夾存在
    
    # 假資料（模擬 Selenium cookies 結構）
    dummy_cookie = [
        {"name": "sessionid", "value": "abc123", "domain": ".tixcraft.com"},
        {"name": "user", "value": "jack", "domain": "tixcraft.com"}
    ]
    
    print("=== 儲存 cookie ===")
    save_cookie(dummy_cookie, "test_cookie.json")

    print("\n=== 載入 cookie ===")
    loaded = load_cookie("test_cookie.json")
    
    print("\n=== 結果 ===")
    print(loaded)
    print(f"Cookie 檔案位置: {COOKIES_DIR / 'test_cookie.json'}")

if __name__ == "__main__":
    test_cookie_functions()
