
import time
import logging
import functools
import ticketbot.config2 as config2

def retry(max_attempts=config2.RETRY_LIMIT, delay=config2.RETRY_INTERVAL, exceptions=(Exception,)):
    """
    裝飾器：自動重試指定次數
    參數：
        max_attempts : 最大重試次數
        delay        : 每次失敗後的等待秒數
        exceptions   : 要捕捉的例外類型
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logging.warning(f"{func.__name__} 第 {attempt} 次失敗：{e}")
                    if attempt < max_attempts:
                        time.sleep(delay)
                    else:
                        logging.error(f"{func.__name__} 超過最大重試次數 {max_attempts}")
                        raise
        return wrapper
    return decorator