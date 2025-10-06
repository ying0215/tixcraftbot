import easyocr
import cv2
import torch

# 初始化 OCR 辨識器，只載入一次避免重複耗時
_reader_cache = {}

def get_reader(langs):
    """取得或建立 EasyOCR Reader，避免重複初始化"""
    lang_key = tuple(langs)
    if lang_key not in _reader_cache:
        print(f"✅ 初始化 EasyOCR Reader (語言: {langs})...")
        _reader_cache[lang_key] = easyocr.Reader(langs)
        print("✅ Reader 初始化完成。")
    return _reader_cache[lang_key]


def ocr_image(image_path: str, langs=['en']):
    """
    OCR 單一張圖片，回傳辨識結果。
    :param image_path: 圖片路徑 (str)
    :param langs: 語言設定 (list, 預設 ['en'])
    :return: list of dicts: [{'text': str, 'confidence': float, 'bbox': list}, ...]
    """
    try:
        # 讀取圖片
        img = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("❌ 無法讀取圖片，檔案可能壞掉或不是有效的圖片格式。")

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # OCR 辨識
        reader = get_reader(langs)
        results = reader.readtext(img_rgb)

        output = []
        for (bbox, text, prob) in results:
            output.append({
                "text": text.lower(),  # 強制轉小寫
                "confidence": prob,
                "bbox": bbox
            })
        return output

    except Exception as e:
        print(f"⚠️ OCR 辨識失敗: {e}")
        return []
    
def ocr_test():
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