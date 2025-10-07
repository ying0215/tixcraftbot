"""
purchase.py

拓元購票機器人 - 購票流程模組
處理選場次、選區域、選票種、提交等核心流程
"""

import logging
import re
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoAlertPresentException, TimeoutException
from . import config

logger = logging.getLogger(__name__)


def select_match_and_buy(driver):
    """
    選擇目標場次並直接跳轉到購票頁面
    
    Args:
        driver: Selenium WebDriver 實例
        
    Returns:
        bool: 是否成功
        
    Raises:
        Exception: 選擇失敗
    """
    try:
        # 等待頁面載入
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#gameList table"))
        )

        logger.info(f"🔍 搜尋目標場次: {config.TARGET_DATE}")
        logger.info(f"🔍 搜尋目標活動: {config.TARGET_TEXT}")

        # 找到所有購票按鈕
        buttons = driver.find_elements(By.CSS_SELECTOR, "button[data-href*='ticket/area']")

        for button in buttons:
            ticket_url = button.get_attribute("data-href")
            if ticket_url:
                logger.info(f"✅ 找到購票網址: {ticket_url}")
                # 直接跳轉到購票頁面
                driver.get(ticket_url)
                logger.info("✅ 已跳轉到購票頁面")
                return True

        logger.error("❌ 未找到任何購票按鈕")
        raise Exception("未找到購票按鈕")

    except Exception as e:
        logger.error(f"❌ 選擇場次失敗: {e}")
        raise Exception(f"選擇場次失敗: {e}")


def select_area(driver):
    """
    依序嘗試不同區域，直到找到可購票的為止
    
    Args:
        driver: Selenium WebDriver 實例
        
    Returns:
        bool: 是否成功
        
    Raises:
        Exception: 所有區域都失敗
    """
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".zone.area-list"))
        )

        # 確保選擇「電腦配位」模式（如果有）
        try:
            auto_radio = driver.find_element(By.ID, "select_form_auto")
            if not auto_radio.is_selected():
                auto_radio.click()
                logger.info("✅ 已切換至電腦配位模式")
        except Exception as e:
            logger.warning(f"⚠️ 無法切換配位模式: {e}")

        # 取得所有可購票區域
        available_areas = driver.find_elements(
            By.CSS_SELECTOR,
            ".zone.area-list li.select_form_a a, .zone.area-list li.select_form_b a"
        )

        if not available_areas:
            logger.error("❌ 沒有找到任何可購票的區域")
            raise Exception("沒有可購票區域")

        logger.info(f"🔍 找到 {len(available_areas)} 個可購票區域")

        min_ticket = int(config.TICKET_VALUE)

        for area in available_areas:
            try:
                area_id = area.get_attribute("id")
                area_name = area.text.strip()
                logger.info(f"🎯 嘗試區域: {area_name} ({area_id})")

                # 判斷區域狀態
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

                # 使用 JavaScript 獲取對應購票網址
                ticket_url = driver.execute_script(
                    "return typeof areaUrlList !== 'undefined' && areaUrlList[arguments[0]] ? areaUrlList[arguments[0]] : null;", 
                    area_id
                )

                if not ticket_url:
                    logger.warning(f"⚠️ 找不到 {area_name} 的購票網址，直接點擊")
                    driver.execute_script("arguments[0].click();", area)
                else:
                    logger.info(f"✅ 取得購票網址: {ticket_url}")
                    driver.get(ticket_url)

                # 檢查是否成功進入購票頁面
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "img[src*='captcha'], #TicketForm_verifyCode-image"))
                    )
                    logger.info(f"🎉 成功進入 {area_name} 購票頁面！")
                    return True
                except:
                    # 檢查是否跳回選區頁面
                    if driver.find_elements(By.CSS_SELECTOR, ".zone.area-list"):
                        logger.warning(f"❌ {area_name} 已售完，自動跳回選區頁面")
                        continue

                    # 檢查錯誤訊息
                    error_elements = driver.find_elements(By.CSS_SELECTOR, ".alert-danger, .error-message, .fcRed")
                    if error_elements:
                        error_text = error_elements[0].text.strip()
                        logger.error(f"❌ 購票失敗: {error_text}")
                        driver.back()
                        time.sleep(1)
                        continue

                    logger.warning(f"❌ {area_name} 購票頁面載入異常，嘗試下一個區域")
                    driver.back()
                    time.sleep(1)
                    continue

            except Exception as area_error:
                logger.error(f"❌ 處理區域 {area_name if 'area_name' in locals() else '未知'} 時發生錯誤: {area_error}")
                try:
                    driver.back()
                    time.sleep(1)
                except:
                    pass
                continue

        logger.error("❌ 所有可購票區域都已嘗試完畢，均無法成功購票")
        raise Exception("所有區域都無法購票")

    except Exception as e:
        logger.error(f"❌ 選擇區域過程發生嚴重錯誤: {e}")
        raise Exception(f"選擇區域失敗: {e}")


def select_tickets(driver):
    """
    選擇票種和數量
    
    Args:
        driver: Selenium WebDriver 實例
        
    Returns:
        bool: 是否成功
        
    Raises:
        Exception: 選擇失敗
    """
    try:
        # 等待票種列表出現
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ticketPriceList"))
        )
        logger.info("✅ 票種列表已載入")
        
        # 查找所有票種選擇器
        ticket_selects = driver.find_elements(
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
        if config.TICKET_VALUE in available_options:
            select.select_by_value(config.TICKET_VALUE)
            logger.info(f"✅ 已選擇 {config.TICKET_VALUE} 張票")
        else:
            # 選擇最大值
            numeric_options = [int(opt) for opt in available_options if opt.isdigit()]
            max_available = max(numeric_options) if numeric_options else 0
            
            if max_available > 0:
                select.select_by_value(str(max_available))
                logger.warning(f"⚠️ 想要 {config.TICKET_VALUE} 張但不可用，已自動選擇最大值: {max_available} 張")
            else:
                logger.warning(f"⚠️ 警告: 該票種目前無可選數量(僅0可選)")
                select.select_by_value("0")
        
        # 驗證選擇結果
        selected_value = select.first_selected_option.get_attribute("value")
        logger.info(f"🎉 最終選擇數量: {selected_value} 張")
        
        # 勾選同意條款
        try:
            agree = driver.find_element(By.ID, "TicketForm_agree")
            if not agree.is_selected():
                driver.execute_script("arguments[0].click();", agree)
            logger.info("✅ 條款已勾選")
        except Exception as e:
            logger.error(f"❌ 勾選條款失敗: {e}")
            raise Exception(f"勾選條款失敗: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 選擇票種失敗: {e}")
        raise Exception(f"選擇票種失敗: {e}")


def submit_booking(driver):
    """
    提交購票請求
    
    Args:
        driver: Selenium WebDriver 實例
        
    Returns:
        bool: 是否成功
        
    Raises:
        Exception: 提交失敗
    """
    btn_xpath = "//button[contains(text(),'確認張數') and @type='submit']"
    try:
        # 等待元素載入到 DOM
        next_btn = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, btn_xpath))
        )
        
        # 使用 JavaScript 點擊 (繞過畫面遮擋檢查)
        driver.execute_script("arguments[0].click();", next_btn)
        
        logger.info("✅ 已提交購票請求 (JS 點擊)")
        time.sleep(1)  # 等待頁面反應
        return True
        
    except Exception as e:
        logger.error(f"❌ 提交購票失敗: {e}")
        raise Exception(f"提交購票失敗: {e}")


def handle_captcha_error_alert(driver):
    """
    處理驗證碼錯誤時彈出的警告視窗
    
    Args:
        driver: Selenium WebDriver 實例
        
    Returns:
        bool: 是否有警告視窗彈出（True=有錯誤, False=無錯誤）
    """
    ALERT_WAIT_TIME = 3
    
    try:
        # 等待警告視窗出現
        WebDriverWait(driver, ALERT_WAIT_TIME).until(
            EC.alert_is_present(), 
            "等待警告視窗超時。"
        )
        
        # 切換到警告視窗
        alert = driver.switch_to.alert
        
        # 獲取警告視窗的文字內容
        alert_text = alert.text
        logger.warning(f"⚠️ 偵測到警告視窗，內容: {alert_text}")
        
        # 點擊「確定」按鈕
        alert.accept()
        logger.info("✅ 已點擊警告視窗的「確定」按鈕，釋放頁面鎖定。")
        time.sleep(1)  # 等待頁面刷新
        return True
        
    except TimeoutException:
        # 沒有警告視窗 = 驗證碼正確
        return False
    except NoAlertPresentException:
        return False
    except Exception as e:
        logger.error(f"❌ 處理警告視窗時發生意外錯誤: {e}")
        return False