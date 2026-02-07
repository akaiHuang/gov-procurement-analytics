#!/usr/bin/env python3
"""
政府採購標案資料分類整理腳本
將 all_tenders.jsonl 按照年份和類別拆分成多個檔案
"""

import json
import os
from collections import defaultdict
from pathlib import Path
from datetime import datetime

# 設定路徑
SOURCE_FILE = "pcc_data/all_tenders.jsonl"
OUTPUT_DIR = "pcc_data/categorized"

# 主要分類對應
MAIN_CATEGORIES = {
    "工程類": "engineering",      # 工程類
    "財物類": "goods",            # 財物類
    "勞務類": "services",         # 勞務類
}

def get_main_category(category_str):
    """從分類字串中提取主要分類"""
    if not category_str:
        return "other", "其他"
    
    for cn_name, en_name in MAIN_CATEGORIES.items():
        if category_str.startswith(cn_name):
            return en_name, cn_name
    
    return "other", "其他"

def get_year(date_int):
    """從日期整數中提取年份"""
    if not date_int:
        return "unknown"
    return str(date_int)[:4]

def create_directory_structure():
    """建立目錄結構"""
    base_dir = Path(OUTPUT_DIR)
    
    # 建立主要分類目錄
    for en_name in list(MAIN_CATEGORIES.values()) + ["other"]:
        category_dir = base_dir / en_name
        category_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"✓ 已建立目錄結構於 {base_dir}")
    return base_dir

def split_tenders():
    """執行分類拆分"""
    print("=" * 60)
    print("政府採購標案資料分類整理")
    print("=" * 60)
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 建立目錄
    base_dir = create_directory_structure()
    
    # 用於追蹤檔案句柄
    file_handles = {}
    
    # 統計資訊
    stats = defaultdict(lambda: defaultdict(int))
    total_count = 0
    error_count = 0
    
    try:
        print(f"讀取來源檔案: {SOURCE_FILE}")
        print("處理中...")
        print()
        
        with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())
                    
                    # 取得分類資訊
                    category_str = data.get('brief', {}).get('category', '')
                    main_cat_en, main_cat_cn = get_main_category(category_str)
                    
                    # 取得年份
                    year = get_year(data.get('date'))
                    
                    # 建立檔案路徑
                    output_file = base_dir / main_cat_en / f"{year}.jsonl"
                    
                    # 取得或建立檔案句柄
                    file_key = str(output_file)
                    if file_key not in file_handles:
                        file_handles[file_key] = open(output_file, 'w', encoding='utf-8')
                    
                    # 寫入資料
                    file_handles[file_key].write(line)
                    
                    # 更新統計
                    stats[main_cat_cn][year] += 1
                    total_count += 1
                    
                    # 進度顯示
                    if line_num % 500000 == 0:
                        print(f"  已處理 {line_num:,} 筆...")
                        
                except json.JSONDecodeError as e:
                    error_count += 1
                except Exception as e:
                    error_count += 1
                    if error_count <= 5:
                        print(f"  警告: 第 {line_num} 行處理錯誤: {e}")
    
    finally:
        # 關閉所有檔案句柄
        for fh in file_handles.values():
            fh.close()
    
    print()
    print("=" * 60)
    print("分類完成！")
    print("=" * 60)
    print(f"總計處理: {total_count:,} 筆")
    print(f"錯誤數量: {error_count:,} 筆")
    print(f"結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 輸出統計報告
    print("=" * 60)
    print("分類統計")
    print("=" * 60)
    
    for category in ["工程類", "財物類", "勞務類", "其他"]:
        if category in stats:
            cat_total = sum(stats[category].values())
            en_name = MAIN_CATEGORIES.get(category, "other")
            print(f"\n【{category}】({en_name}/) - 共 {cat_total:,} 筆")
            for year in sorted(stats[category].keys()):
                count = stats[category][year]
                print(f"  {year}: {count:,} 筆")
    
    # 建立索引文件
    create_index(base_dir, stats)
    
    return stats

def create_index(base_dir, stats):
    """建立分類索引 README"""
    readme_path = base_dir / "README.md"
    
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write("# 政府採購標案資料分類目錄\n\n")
        f.write(f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 目錄結構\n\n")
        f.write("```\n")
        f.write("categorized/\n")
        f.write("├── engineering/    # 工程類標案\n")
        f.write("├── goods/          # 財物類標案\n")
        f.write("├── services/       # 勞務類標案\n")
        f.write("├── other/          # 其他類標案\n")
        f.write("└── README.md       # 本說明檔\n")
        f.write("```\n\n")
        
        f.write("## 資料格式\n\n")
        f.write("每個 JSONL 檔案以年份命名（如 `2021.jsonl`），每行一筆標案資料。\n\n")
        
        f.write("### 欄位說明\n\n")
        f.write("| 欄位 | 說明 |\n")
        f.write("|------|------|\n")
        f.write("| `date` | 公告日期 (YYYYMMDD) |\n")
        f.write("| `filename` | 檔案名稱 |\n")
        f.write("| `brief.type` | 公告類型 |\n")
        f.write("| `brief.title` | 標案名稱 |\n")
        f.write("| `brief.category` | 分類 |\n")
        f.write("| `job_number` | 標案編號 |\n")
        f.write("| `unit_id` | 機關 ID |\n")
        f.write("| `unit_name` | 機關名稱 |\n")
        f.write("| `url` | 標案網址路徑 |\n\n")
        
        f.write("## 統計資訊\n\n")
        
        total_all = 0
        for category in ["工程類", "財物類", "勞務類", "其他"]:
            if category in stats:
                en_name = MAIN_CATEGORIES.get(category, "other")
                cat_total = sum(stats[category].values())
                total_all += cat_total
                f.write(f"### {category} (`{en_name}/`)\n\n")
                f.write(f"共 **{cat_total:,}** 筆\n\n")
                f.write("| 年份 | 筆數 |\n")
                f.write("|------|------|\n")
                for year in sorted(stats[category].keys()):
                    count = stats[category][year]
                    f.write(f"| {year} | {count:,} |\n")
                f.write("\n")
        
        f.write(f"## 總計\n\n**{total_all:,}** 筆標案資料\n")
    
    print(f"\n✓ 已建立索引文件: {readme_path}")

if __name__ == "__main__":
    split_tenders()
