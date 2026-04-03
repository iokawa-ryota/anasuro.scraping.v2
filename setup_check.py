#!/usr/bin/env python3
"""
セットアップ・テストスクリプト

以下の処理を行います：
1. 必要なパッケージの確認
2. 設定ファイルの確認
3. サンプル店舗リスト Excel の生成（オプション）
4. Web サーバーの起動確認
"""

import sys
import os
import subprocess
from pathlib import Path

def check_python_version():
    """Python バージョンを確認"""
    print("[CHECK] Python version...")
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"[OK] Python {version}")
    
    if sys.version_info < (3, 8):
        print("[WARN] Python 3.8 or newer is recommended")
        return False
    return True

def check_packages():
    """必要なパッケージをインストール"""
    print("\n[CHECK] Python packages...")
    
    required_packages = {
        'flask': 'Flask',
        'pandas': 'pandas',
        'openpyxl': 'openpyxl',
        'selenium': 'selenium',
        'bs4': 'beautifulsoup4',
        'undetected_chromedriver': 'undetected-chromedriver',
    }
    
    missing_packages = []
    
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"[OK] {package_name} is installed")
        except ImportError:
            print(f"[MISSING] {package_name}")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n[INSTALL] Installing missing packages...")
        print(f"   {', '.join(missing_packages)}")
        
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', 
                '--upgrade'
            ] + missing_packages)
            print("[OK] Installation complete")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Installation failed: {e}")
            return False
    
    return True

def check_config_files():
    """設定ファイルを確認"""
    print("\n[CHECK] Project files...")
    
    required_files = {
        'app.py': 'Flask バックエンド',
        'index.html': 'フロントエンド UI',
        'anasuro_selective.py': 'スクレイピング処理',
        'start_silent.bat': 'startup script',
    }
    
    all_exist = True
    for filename, description in required_files.items():
        path = Path(filename)
        if path.exists():
            size = path.stat().st_size
            print(f"[OK] {filename} ({description}) - {size:,} bytes")
        else:
            print(f"[MISSING] {filename} ({description})")
            all_exist = False
    
    return all_exist

def check_store_list():
    """店舗リスト CSV を確認"""
    print("\n[CHECK] store_list.csv...")
    
    store_list_path = "D:/Users/Documents/python/saved_html/store_list.csv"
    
    if not os.path.exists(store_list_path):
        print(f"[MISSING] {store_list_path}")
        print("  Create a sample file? (y/n): ", end="")
        
        if input().lower() == 'y':
            create_sample_store_list()
            return True
        return False
    
    try:
        import pandas as pd
        df = pd.read_csv(store_list_path)
        
        required_cols = {'store_name', 'store_url', 'data_directory'}
        actual_cols = set(df.columns)
        
        print(f"[OK] {store_list_path} exists")
        print(f"  Rows: {len(df)}")
        print(f"  Columns: {', '.join(df.columns)}")
        
        if not required_cols.issubset(actual_cols):
            print("[WARN] Required columns are missing")
            print(f"   Required: {required_cols}")
            print(f"   Actual: {actual_cols}")
            return False
        
        return True
    except Exception as e:
        print(f"[ERROR] Failed to read file: {e}")
        return False

def create_sample_store_list():
    """サンプル店舗リスト CSV を生成（UTF-8 BOM付き）"""
    print("\n生成中...")

    try:
        import pandas as pd

        sample_data = {
            'store_name': [
                '店舗A - 銀座',
                '店舗B - 渋谷',
                '店舗C - 新宿',
                '店舗D - 池袋',
                '店舗E - 品川'
            ],
            'store_url': [
                'https://example.com/store-a',
                'https://example.com/store-b',
                'https://example.com/store-c',
                'https://example.com/store-d',
                'https://example.com/store-e'
            ],
            'data_directory': [
                'D:/data/store_a',
                'D:/data/store_b',
                'D:/data/store_c',
                'D:/data/store_d',
                'D:/data/store_e'
            ]
        }

        df = pd.DataFrame(sample_data)

        # ディレクトリを作成
        os.makedirs('D:/Users/Documents/python/saved_html', exist_ok=True)

        output_path = 'D:/Users/Documents/python/saved_html/store_list.csv'
        df.to_csv(output_path, index=False, encoding='utf-8-sig')

        print(f"[OK] Sample file created: {output_path}")
        print(f"  Rows: {len(df)}")

        return True
    except Exception as e:
        print(f"[ERROR] Failed to create sample file: {e}")
        return False

def print_summary():
    """サマリーを表示"""
    print("\n" + "=" * 60)
    print("Setup complete")
    print("=" * 60)
    print("\nStart the web server with:\n")
    print("  python app.py\n")
    print("Then open this URL in your browser:\n")
    print("  http://localhost:5000\n")
    print("=" * 60)

def main():
    print("\n" + "=" * 60)
    print("Slot Store Scraper Web UI - Setup")
    print("=" * 60 + "\n")
    
    checks = [
        ("Python バージョン確認", check_python_version),
        ("パッケージ確認", check_packages),
        ("設定ファイル確認", check_config_files),
        ("店舗リスト確認", check_store_list),
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"[ERROR] Unexpected error in {check_name}: {e}")
            results.append((check_name, False))
    
    print("\n" + "=" * 60)
    print("Results:")
    print("=" * 60)
    for check_name, result in results:
        status = "[OK]" if result else "[NG]"
        print(f"{status}: {check_name}")
    
    if all(result for _, result in results):
        print_summary()
    else:
        print("\n[WARN] Some checks failed")
        print("Review the messages above and fix the reported issues")
        sys.exit(1)

if __name__ == '__main__':
    main()
