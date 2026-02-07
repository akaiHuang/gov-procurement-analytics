#!/usr/bin/env python3
"""
篩選適合的政府標案

公司資訊：
- 資本額：200萬
- 服務項目：廣告行銷、軟體開發、網站設計、AI部署、視覺設計
"""

import json
import os
from pathlib import Path
from datetime import datetime

# 設定
INPUT_FILE = "pcc_data/2026/tenders_2026.jsonl"
OUTPUT_DIR = Path("pcc_data/2026/filtered_for_company")

# 相關關鍵字（依服務項目分類）
KEYWORDS = {
    "廣告行銷": ['廣告', '行銷', '宣傳', '推廣', '公關', '媒體', '社群', 'SEO', '品牌', '形象', 
                '企劃', '活動', '展覽', '文宣', '海報', '傳播', 'DM', 'EDM', '曝光'],
    "軟體開發": ['軟體', '程式', 'APP', '應用程式', '系統開發', '資訊系統', '開發案', '客製化',
                '模組', '功能開發', 'API', '後台', '前端', '後端', '程式設計'],
    "網站設計": ['網站', '網頁', '官網', '入口網', '平台', '網路平台', 'Web', 'RWD', 
                '響應式', '電子商務', '購物網站', '形象網站', '入口網站'],
    "AI部署": ['AI', '人工智慧', '機器學習', '深度學習', 'ChatGPT', 'GPT', 'LLM', 
              '大語言模型', '智慧', '演算法', '模型', '自動化', '智能'],
    "視覺設計": ['視覺', '設計', '美編', '美術', 'LOGO', 'CIS', 'VI', '識別系統', 
                '平面設計', '圖像', '插畫', '排版', '版面', 'UI', 'UX', '介面設計',
                '多媒體', '影片', '動畫', '剪輯', '後製']
}

# 排除關鍵字（非服務範圍）
EXCLUDE_KEYWORDS = ['工程', '營造', '建築', '土木', '機電', '水電', '消防', '空調', 
                    '監造', '結構', '鋼構', '裝修', '裝潢', '木作', '油漆', 
                    '醫療', '藥品', '器材', '儀器', '設備採購', '硬體',
                    '清潔', '保全', '警衛', '餐飲', '伙食', '便當',
                    '印刷', '油墨', '紙張']

# 可投標的公告類型
BID_TYPES = [
    '公開招標公告',
    '公開取得報價單或企劃書公告',
    '經公開評選或公開徵求之限制性招標公告',
    '選擇性招標(個案)公告'
]


def match_keywords(title, category):
    """檢查標題是否符合某個類別的關鍵字"""
    for kw in KEYWORDS.get(category, []):
        if kw.lower() in title.lower():
            return kw
    return None


def should_exclude(title):
    """檢查是否應該排除"""
    for kw in EXCLUDE_KEYWORDS:
        if kw in title:
            return True
    return False


def filter_tenders():
    """篩選適合的標案"""
    
    print("=" * 70)
    print("篩選適合公司的政府標案")
    print("=" * 70)
    print(f"公司服務: 廣告行銷、軟體開發、網站設計、AI部署、視覺設計")
    print(f"資本額: 200萬")
    print()
    
    # 建立輸出目錄
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 儲存結果
    results = {cat: [] for cat in KEYWORDS.keys()}
    all_matches = []
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                tender_type = data.get('brief', {}).get('type', '')
                
                # 只看可投標的公告
                if tender_type not in BID_TYPES:
                    continue
                
                title = data.get('brief', {}).get('title', '')
                
                # 排除不相關的案子
                if should_exclude(title):
                    continue
                
                # 檢查是否符合任一類別
                matched_categories = []
                for category in KEYWORDS.keys():
                    kw = match_keywords(title, category)
                    if kw:
                        matched_categories.append((category, kw))
                
                if matched_categories:
                    tender_info = {
                        'date': data.get('date'),
                        'title': title,
                        'type': tender_type,
                        'unit_name': data.get('unit_name', '未知機關'),
                        'job_number': data.get('job_number'),
                        'url': f"https://web.pcc.gov.tw{data.get('url', '')}",
                        'api_url': data.get('tender_api_url', ''),
                        'matched_categories': [c[0] for c in matched_categories],
                        'matched_keywords': [c[1] for c in matched_categories],
                        'raw_data': data
                    }
                    
                    all_matches.append(tender_info)
                    
                    # 依類別分類儲存
                    for category, _ in matched_categories:
                        results[category].append(tender_info)
                        
            except Exception as e:
                pass
    
    # 輸出結果
    print(f"找到 {len(all_matches)} 筆適合的標案")
    print()
    
    # 儲存全部結果
    all_file = OUTPUT_DIR / "all_matched.jsonl"
    with open(all_file, 'w', encoding='utf-8') as f:
        for item in all_matches:
            # 移除 raw_data 以減少檔案大小
            output = {k: v for k, v in item.items() if k != 'raw_data'}
            f.write(json.dumps(output, ensure_ascii=False) + '\n')
    
    # 依類別儲存
    for category, items in results.items():
        if items:
            safe_name = category.replace('/', '_')
            cat_file = OUTPUT_DIR / f"{safe_name}.jsonl"
            with open(cat_file, 'w', encoding='utf-8') as f:
                for item in items:
                    output = {k: v for k, v in item.items() if k != 'raw_data'}
                    f.write(json.dumps(output, ensure_ascii=False) + '\n')
    
    # 產生摘要報告
    generate_report(results, all_matches)
    
    return results


def generate_report(results, all_matches):
    """產生摘要報告"""
    
    report_file = OUTPUT_DIR / "README.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# 適合公司的政府標案\n\n")
        f.write(f"篩選時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 公司資訊\n\n")
        f.write("- **資本額**: 200萬\n")
        f.write("- **服務項目**: 廣告行銷、軟體開發、網站設計、AI部署、視覺設計\n\n")
        
        f.write("## 統計摘要\n\n")
        f.write(f"共找到 **{len(all_matches)}** 筆可能適合的標案\n\n")
        f.write("| 類別 | 筆數 |\n")
        f.write("|------|------|\n")
        for category, items in results.items():
            f.write(f"| {category} | {len(items)} |\n")
        f.write("\n")
        
        f.write("## 檔案說明\n\n")
        f.write("| 檔案 | 說明 |\n")
        f.write("|------|------|\n")
        f.write("| `all_matched.jsonl` | 全部符合條件的標案 |\n")
        for category in KEYWORDS.keys():
            safe_name = category.replace('/', '_')
            f.write(f"| `{safe_name}.jsonl` | {category}相關標案 |\n")
        f.write("\n")
        
        f.write("## 標案列表\n\n")
        
        for category, items in results.items():
            if items:
                f.write(f"### {category} ({len(items)} 筆)\n\n")
                for item in items[:50]:  # 每類最多顯示 50 筆
                    f.write(f"#### {item['title']}\n\n")
                    f.write(f"- **機關**: {item['unit_name']}\n")
                    f.write(f"- **日期**: {item['date']}\n")
                    f.write(f"- **類型**: {item['type']}\n")
                    f.write(f"- **標案編號**: {item['job_number']}\n")
                    f.write(f"- **連結**: [查看詳情]({item['url']})\n")
                    f.write(f"- **符合關鍵字**: {', '.join(item['matched_keywords'])}\n")
                    f.write("\n")
                
                if len(items) > 50:
                    f.write(f"*（僅顯示前 50 筆，完整資料請查看 JSONL 檔案）*\n\n")
    
    print(f"✓ 已產生報告: {report_file}")
    print()
    
    # 印出摘要
    print("=" * 70)
    print("篩選結果摘要")
    print("=" * 70)
    for category, items in results.items():
        print(f"  {category}: {len(items)} 筆")
    print()
    print(f"輸出目錄: {OUTPUT_DIR}")
    print()
    
    # 顯示部分結果
    print("=" * 70)
    print("部分標案預覽")
    print("=" * 70)
    for item in all_matches[:15]:
        print(f"\n【{item['type']}】{item['title']}")
        print(f"  機關: {item['unit_name']}")
        print(f"  日期: {item['date']}")
        print(f"  類別: {', '.join(item['matched_categories'])}")
        print(f"  網址: {item['url']}")


if __name__ == "__main__":
    filter_tenders()
