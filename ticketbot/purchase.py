# purchase.py
# 負責購票流程邏輯（選場次、選區域、選票種、提交表單、錯誤處理）

import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
import config
from captcha import download_captcha_image, fill_captcha, refresh_captcha


def select_match_and_buy(driver: WebDriver):
    """選擇目標場次並進入購票"""
    try:
        match_rows = driver.find_elements(By.CSS_SELECTOR, "tr.gridc.fcTxt")
        for row in match_rows:
            date_text = row.find_elements(By.TAG_NAME, "td")[0].text.strip()
            event_text = row.find_elements(By.TAG_NAME, "td")[1].text.strip()
            location = row.find_elements(By.TAG_NAME, "td")[2].text.strip()

            if (config.TARGET_DATE in date_text) and (config.TARGET_TEXT in location):
                logging.info(f"找到場次：{date_text} - {location}")
                buy_button = row.find_element(By.TAG_NAME, "button")
                buy_button.click()
                time.sleep(1)
                return True

        logging.warning("未找到目標場次")
        return False
    except Exception as e:
        logging.error(f"選擇場次失敗：{e}")
        return False


def select_area(driver: WebDriver):
    """選擇座位區域"""
    try:
        areas = driver.find_elements(By.CSS_SELECTOR, "div.area-list a")
        for area in areas:
            try:
                area.click()
                logging.info(f"選擇區域成功：{area.text.strip()}")
                return True
            except Exception as e:
                logging.debug(f"區域 {area.text.strip()} 點擊失敗：{e}")
        logging.warning("無法選擇任何區域")
        return False
    except Exception as e:
        logging.error(f"選擇區域失敗：{e}")
        return False


def select_tickets(driver: WebDriver):
    """選擇票種與數量"""
    try:
        # 選第一個票種（保留原邏輯）
        selects = driver.find_elements(By.CSS_SELECTOR, "select[id^='TicketForm_ticketPrice']")
        if not selects:
            logging.warning("未找到票種下拉選單")
            return False

        ticket_select = selects[0]
        from selenium.webdriver.support.ui import Select
        select = Select(ticket_select)

        if config.TICKET_VALUE in [o.get_attribute("value") for o in select.options]:
            select.select_by_value(config.TICKET_VALUE)
        else:
            select.select_by_index(1)

        logging.info(f"票種數量設定完成：{config.TICKET_VALUE}")
        return True
    except Exception as e:
        logging.error(f"選擇票種失敗：{e}")
        return False


def submit_booking(driver: WebDriver):
    """送出訂票"""
    try:
        submit_btn = driver.find_element(By.ID, "ticketPriceSubmit")
        submit_btn.click()
        logging.info("已點擊送出訂票")
        time.sleep(2)
        return True
    except Exception as e:
        logging.error(f"送出訂票失敗：{e}")
        return False


def handle_captcha_error_alert(driver: WebDriver):
    """處理驗證碼錯誤提示"""
    try:
        alert_text = driver.find_element(By.CSS_SELECTOR, "div.alert.alert-danger").text
        if "驗證碼" in alert_text:
            logging.warning("驗證碼錯誤，準備重試")
            refresh_captcha(driver)
            return True
        return False
    except Exception:
        return False
