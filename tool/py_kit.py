import subprocess
import sys
import os
from pathlib import Path

def find_python_installations():
    """尋找系統中所有的 Python 安裝"""
    pythons = []
    
    # 常見的 Python 安裝位置
    common_paths = [
        r"C:\Python*",
        r"C:\Program Files\Python*",
        r"C:\Program Files (x86)\Python*",
        os.path.expanduser(r"~\AppData\Local\Programs\Python\Python*"),
    ]
    
    for pattern in common_paths:
        for path in Path("C:\\").rglob("python.exe"):
            path_str = str(path)
            # 排除 Anaconda 相關路徑
            if "anaconda" not in path_str.lower() and "miniconda" not in path_str.lower():
                if path.exists():
                    pythons.append(path)
    
    # 也檢查 PATH 中的 python
    try:
        result = subprocess.run(
            ["where", "python"],
            capture_output=True,
            text=True,
            shell=True
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                path = Path(line.strip())
                if path.exists():
                    pythons.append(path)
    except:
        pass
    
    # 去重
    pythons = list(set(pythons))
    return pythons

def get_python_info(python_path):
    """取得 Python 版本資訊"""
    try:
        result = subprocess.run(
            [str(python_path), "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip() or result.stderr.strip()
    except:
        return "無法取得版本資訊"

def get_installed_packages(python_path):
    """取得該 Python 安裝的套件列表"""
    try:
        result = subprocess.run(
            [str(python_path), "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"錯誤: {result.stderr}"
    except Exception as e:
        return f"無法取得套件列表: {str(e)}"

def main():
    print("=" * 70)
    print("尋找系統中的 Python 安裝...")
    print("=" * 70)
    
    # 當前使用的 Python
    print(f"\n【當前執行的 Python】")
    print(f"路徑: {sys.executable}")
    print(f"版本: {sys.version}")
    print(f"是否為 Anaconda: {'是' if 'anaconda' in sys.version.lower() else '否'}")
    
    # 尋找所有 Python 安裝
    print(f"\n{'=' * 70}")
    print("搜尋所有 Python 安裝中...")
    pythons = find_python_installations()
    
    if not pythons:
        print("未找到其他 Python 安裝")
        return
    
    print(f"找到 {len(pythons)} 個 Python 安裝：\n")
    
    for idx, python_path in enumerate(pythons, 1):
        print(f"\n{'=' * 70}")
        print(f"【Python #{idx}】")
        print(f"路徑: {python_path}")
        
        version_info = get_python_info(python_path)
        print(f"版本: {version_info}")
        
        is_anaconda = "anaconda" in str(python_path).lower() or "anaconda" in version_info.lower()
        print(f"類型: {'Anaconda' if is_anaconda else '原生 Python'}")
        
        if not is_anaconda:
            print(f"\n正在取得套件列表...")
            packages = get_installed_packages(python_path)
            
            # 儲存到檔案
            output_file = f"python_{idx}_packages.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"Python 路徑: {python_path}\n")
                f.write(f"版本: {version_info}\n")
                f.write(f"{'=' * 70}\n\n")
                f.write(packages)
            
            print(f"✓ 套件列表已儲存至: {output_file}")
            
            # 顯示套件數量
            package_count = len([p for p in packages.split('\n') if p.strip()])
            print(f"✓ 共 {package_count} 個套件")
    
    print(f"\n{'=' * 70}")
    print("完成！")
    print("\n提示：要使用特定的 Python，請直接用完整路徑執行：")
    print('例如: "C:\\Python312\\python.exe" -m pip freeze')

if __name__ == "__main__":
    main()