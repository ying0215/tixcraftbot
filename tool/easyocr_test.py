import easyocr
import torch

# 1. 檢查 PyTorch 是否成功連結到 GPU
if torch.cuda.is_available():
    print(f"CUDA status: 成功！ PyTorch 找到 GPU: {torch.cuda.get_device_name(0)}")
else:
    print("CUDA status: 失敗，將使用 CPU 模式。")

# 2. 測試 EasyOCR 載入
# 載入英文模型 ('en')，並嘗試使用 GPU (預設)
try:
    reader = easyocr.Reader(['en'])
    print("\nEasyOCR 讀取器 (Reader) 載入成功！")
    
    # 進行一次快速測試 (這裡不會真的讀圖，只測試功能性)
    if reader.detector != None and reader.recognizer != None:
        print("EasyOCR 環境配置與核心功能檢查通過。")

except Exception as e:
    print(f"\nEasyOCR 載入失敗！錯誤訊息：{e}")