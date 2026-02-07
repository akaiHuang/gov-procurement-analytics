#!/usr/bin/env python3
"""
專門下載 2026 年政府採購標案資料
"""

import requests
import json
import time
import os
from datetime import datetime, timedelta
from pathlib import Path


def download_2026_data():
    """下載 2026 年所有標案資料"""
    
    BASE_URL = "https://pcc-api.openfun.app/api"
    OUTPUT_DIR = Path("pcc_data/2026")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'PCC-Data-Downloader/1.0'
    })
    
    # 進度檔案
    progress_file = OUTPUT_DIR / "download_progress.json"
    output_file = OUTPUT_DIR / "tenders_2026.jsonl"
    
    # 載入已下載的日期
    downloaded_dates = set()
    if progress_file.exists():
        with open(progress_file, 'r') as f:
            progress = json.load(f)
            downloaded_dates = set(progress.get('downloaded_dates', []))
    
    # 2026 年日期範圍 (到今天)
    start_date = datetime(2026, 1, 1)
    end_date = datetime(2026, 1, 7)  # 今天
    
    print("=" * 60)
    print("下載 2026 年政府採購標案資料")
    print("=" * 60)
    print(f"日期範圍: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    print(f"輸出目錄: {OUTPUT_DIR}")
    print()
    
    current_date = start_date
    total_count = 0
    
    # 開啟輸出檔案（追加模式）
    with open(output_file, 'a', encoding='utf-8') as f:
        while current_date <= end_date:
            date_str = current_date.strftime("%Y%m%d")
            
            if date_str in downloaded_dates:
                print(f"[跳過] {date_str} - 已下載")
                current_date += timedelta(days=1)
                continue
            
            print(f"[下載] {date_str}...", end=" ")
            
            try:
                url = f"{BASE_URL}/listbydate"
                params = {"date": date_str}
                
                for attempt in range(3):
                    try:
                        response = session.get(url, params=params, timeout=30)
                        
                        if response.status_code == 429:
                            wait_time = 10 * (attempt + 1)
                            print(f"(請求過快，等待 {wait_time} 秒)")
                            time.sleep(wait_time)
                            continue
                        
                        response.raise_for_status()
                        break
                    except requests.exceptions.Timeout:
                        if attempt < 2:
                            time.sleep(5)
                            continue
                        raise
                
                result = response.json()
                records = result.get('records', []) if isinstance(result, dict) else []
                
                if records:
                    for record in records:
                        record['_download_date'] = date_str
                        f.write(json.dumps(record, ensure_ascii=False) + '\n')
                    f.flush()
                    total_count += len(records)
                    print(f"✓ {len(records)} 筆")
                else:
                    print("✓ 無資料")
                
                # 更新進度
                downloaded_dates.add(date_str)
                with open(progress_file, 'w') as pf:
                    json.dump({
                        'downloaded_dates': list(downloaded_dates),
                        'total_count': total_count,
                        'last_update': datetime.now().isoformat()
                    }, pf, ensure_ascii=False, indent=2)
                
            except Exception as e:
                print(f"✗ 錯誤: {e}")
            
            current_date += timedelta(days=1)
            time.sleep(0.5)  # 避免過度請求
    
    print()
    print("=" * 60)
    print(f"下載完成！共 {total_count} 筆資料")
    print(f"儲存位置: {output_file}")
    print("=" * 60)
    
    # 依分類拆分
    split_by_category(output_file, OUTPUT_DIR)


def split_by_category(input_file, output_dir):
    """依分類拆分資料"""
    
    print()
    print("依分類拆分資料...")
    
    CATEGORIES = {
        "工程類": "engineering",
        "財物類": "goods", 
        "勞務類": "services",
    }
    
    # 建立分類目錄
    for en_name in list(CATEGORIES.values()) + ["other"]:
        (output_dir / en_name).mkdir(exist_ok=True)
    
    # 開啟所有輸出檔案
    files = {}
    for en_name in list(CATEGORIES.values()) + ["other"]:
        files[en_name] = open(output_dir / en_name / "2026.jsonl", 'w', encoding='utf-8')
    
    stats = {name: 0 for name in list(CATEGORIES.values()) + ["other"]}
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    category = data.get('brief', {}).get('category', '')
                    
                    # 判斷分類
                    target = "other"
                    for cn_name, en_name in CATEGORIES.items():
                        if category and category.startswith(cn_name):
                            target = en_name
                            break
                    
                    files[target].write(line)
                    stats[target] += 1
                except:
                    pass
    finally:
        for fh in files.values():
            fh.close()
    
    print("分類完成！")
    for name, count in stats.items():
        print(f"  {name}: {count} 筆")


if __name__ == "__main__":
    download_2026_data()
