def submit_booking(self):
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
    