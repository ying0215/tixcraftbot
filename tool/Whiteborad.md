是否需要建立所有 7 個模組檔案？ 還是部分已存在？
 ticketbot/
   ├── __init__.py 存在
   ├── main.py (原始版本) 存在
   ├── test1.py (重構版本) 存在
   ├── config.py 存在
   ├── log.py 存在
   ├── driver.py 存在 
   ├── cookies.py 存在
   ├── captcha.py 存在
   ├── purchase.py 存在
   ├── arg_parser.py 存在
   └── OCR.py
OCR.py 的內容是否完整？ 需要確認 ocr_image() 和 get_reader() 函數
OCR.py正常
是否需要保留 main.py？ 還是可以被 test1.py 完全取代？
如果 test1.py 可以正常執行，直接覆蓋main.py
錯誤處理策略：各模組失敗時是返回 False 還是拋出異常？拋出異常
