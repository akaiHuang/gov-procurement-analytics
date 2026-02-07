#!/usr/bin/env python3
"""
產生標案瀏覽網頁（含書籤功能）
"""

import json
from pathlib import Path
from datetime import datetime

INPUT_FILE = "pcc_data/2026/filtered_for_company/all_matched.jsonl"
OUTPUT_FILE = "pcc_data/2026/filtered_for_company/index.html"

def load_tenders():
    """載入標案資料"""
    tenders = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            tenders.append(json.loads(line))
    return tenders

def generate_html(tenders):
    """產生 HTML"""
    
    # 統計各類別數量
    category_counts = {}
    for t in tenders:
        for cat in t.get('matched_categories', []):
            category_counts[cat] = category_counts.get(cat, 0) + 1
    
    html = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>適合公司的政府標案 - 2026年</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        header {{
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            color: #333;
            font-size: 28px;
            margin-bottom: 10px;
        }}
        
        .subtitle {{
            color: #666;
            font-size: 14px;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            cursor: pointer;
            transition: transform 0.3s;
        }}
        
        .stat-card:hover {{
            transform: scale(1.05);
        }}
        
        .stat-card.alt {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}
        
        .stat-card.green {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }}
        
        .stat-card.orange {{
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        }}
        
        .stat-card.blue {{
            background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
            color: #333;
        }}
        
        .stat-card.bookmark {{
            background: linear-gradient(135deg, #f5af19 0%, #f12711 100%);
        }}
        
        .stat-number {{
            font-size: 32px;
            font-weight: bold;
        }}
        
        .stat-label {{
            font-size: 13px;
            opacity: 0.9;
            margin-top: 5px;
        }}
        
        .filters {{
            background: white;
            border-radius: 16px;
            padding: 20px 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            align-items: center;
        }}
        
        .search-box {{
            flex: 1;
            min-width: 250px;
        }}
        
        .search-box input {{
            width: 100%;
            padding: 12px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 30px;
            font-size: 16px;
            transition: all 0.3s;
        }}
        
        .search-box input:focus {{
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
        }}
        
        .filter-group {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        
        .filter-btn {{
            padding: 10px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 30px;
            background: white;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
        }}
        
        .filter-btn:hover {{
            border-color: #667eea;
            color: #667eea;
        }}
        
        .filter-btn.active {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-color: transparent;
        }}
        
        .filter-btn.bookmark-filter {{
            background: linear-gradient(135deg, #f5af19 0%, #f12711 100%);
            color: white;
            border-color: transparent;
        }}
        
        .tender-list {{
            display: grid;
            gap: 15px;
        }}
        
        .tender-card {{
            background: white;
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            transition: all 0.3s;
            position: relative;
        }}
        
        .tender-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 20px 60px rgba(0,0,0,0.15);
        }}
        
        .tender-card.bookmarked {{
            border-left: 5px solid #f5af19;
        }}
        
        .tender-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 15px;
        }}
        
        .tender-title {{
            font-size: 18px;
            font-weight: 600;
            color: #333;
            line-height: 1.4;
            flex: 1;
            margin-right: 15px;
        }}
        
        .tender-date {{
            background: #f0f0f0;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 13px;
            color: #666;
            white-space: nowrap;
        }}
        
        .tender-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 15px;
        }}
        
        .meta-item {{
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 14px;
            color: #666;
        }}
        
        .tender-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 15px;
        }}
        
        .tag {{
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
        }}
        
        .tag-category {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        
        .tag-keyword {{
            background: #e8f4fd;
            color: #1976d2;
        }}
        
        .tag-type {{
            background: #fff3e0;
            color: #e65100;
        }}
        
        .tender-actions {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        
        .btn {{
            padding: 10px 20px;
            border-radius: 30px;
            font-size: 14px;
            font-weight: 500;
            text-decoration: none;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            border: none;
            cursor: pointer;
        }}
        
        .btn-primary {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        
        .btn-primary:hover {{
            transform: scale(1.05);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }}
        
        .btn-secondary {{
            background: #f5f5f5;
            color: #333;
        }}
        
        .btn-secondary:hover {{
            background: #e0e0e0;
        }}
        
        .btn-bookmark {{
            background: #fff3e0;
            color: #e65100;
        }}
        
        .btn-bookmark:hover {{
            background: #ffe0b2;
        }}
        
        .btn-bookmark.active {{
            background: linear-gradient(135deg, #f5af19 0%, #f12711 100%);
            color: white;
        }}
        
        .btn-download {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
        }}
        
        .no-results {{
            background: white;
            border-radius: 16px;
            padding: 60px;
            text-align: center;
            color: #666;
        }}
        
        .no-results-icon {{
            font-size: 60px;
            margin-bottom: 20px;
        }}
        
        .tender-count {{
            background: white;
            border-radius: 16px;
            padding: 15px 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            font-size: 16px;
            color: #666;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }}
        
        .tender-count strong {{
            color: #667eea;
        }}
        
        .bookmark-note {{
            margin-top: 15px;
            padding: 15px;
            background: #fff8e1;
            border-radius: 10px;
            display: none;
        }}
        
        .bookmark-note.show {{
            display: block;
        }}
        
        .bookmark-note textarea {{
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 8px;
            resize: vertical;
            min-height: 60px;
            font-family: inherit;
        }}
        
        .bookmark-note-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .priority-select {{
            padding: 5px 10px;
            border-radius: 20px;
            border: 1px solid #ddd;
        }}
        
        /* Toast 通知 */
        .toast {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #333;
            color: white;
            padding: 15px 25px;
            border-radius: 10px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.3);
            z-index: 1000;
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.3s;
        }}
        
        .toast.show {{
            transform: translateY(0);
            opacity: 1;
        }}
        
        .toast.success {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }}
        
        .toast.error {{
            background: linear-gradient(135deg, #f5576c 0%, #f093fb 100%);
        }}
        
        /* 連線狀態 */
        .connection-status {{
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 20px;
            border-radius: 30px;
            font-size: 14px;
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .connection-status.connected {{
            background: #e8f5e9;
            color: #2e7d32;
        }}
        
        .connection-status.disconnected {{
            background: #ffebee;
            color: #c62828;
        }}
        
        .status-dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }}
        
        .connected .status-dot {{
            background: #4caf50;
        }}
        
        .disconnected .status-dot {{
            background: #f44336;
        }}
        
        @media (max-width: 768px) {{
            .filters {{
                flex-direction: column;
            }}
            
            .search-box {{
                width: 100%;
            }}
            
            .tender-header {{
                flex-direction: column;
                gap: 10px;
            }}
            
            .tender-date {{
                align-self: flex-start;
            }}
            
            .stats {{
                grid-template-columns: repeat(3, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <div class="connection-status disconnected" id="connectionStatus">
        <span class="status-dot"></span>
        <span id="statusText">未連接伺服器</span>
    </div>
    
    <div class="toast" id="toast"></div>
    
    <div class="container">
        <header>
            <h1>🎯 適合公司的政府標案</h1>
            <p class="subtitle">篩選時間：{datetime.now().strftime('%Y-%m-%d %H:%M')} | 資料範圍：2026年1月</p>
            
            <div class="stats">
                <div class="stat-card" onclick="setCategory('all', this)">
                    <div class="stat-number">{len(tenders)}</div>
                    <div class="stat-label">全部標案</div>
                </div>
                <div class="stat-card bookmark" onclick="showBookmarksOnly()">
                    <div class="stat-number" id="bookmarkCount">0</div>
                    <div class="stat-label">⭐ 書籤</div>
                </div>
                <div class="stat-card alt" onclick="setCategory('廣告行銷')">
                    <div class="stat-number">{category_counts.get('廣告行銷', 0)}</div>
                    <div class="stat-label">廣告行銷</div>
                </div>
                <div class="stat-card green" onclick="setCategory('軟體開發')">
                    <div class="stat-number">{category_counts.get('軟體開發', 0)}</div>
                    <div class="stat-label">軟體開發</div>
                </div>
                <div class="stat-card orange" onclick="setCategory('網站設計')">
                    <div class="stat-number">{category_counts.get('網站設計', 0)}</div>
                    <div class="stat-label">網站設計</div>
                </div>
                <div class="stat-card blue" onclick="setCategory('AI部署')">
                    <div class="stat-number">{category_counts.get('AI部署', 0)}</div>
                    <div class="stat-label">AI部署</div>
                </div>
            </div>
        </header>
        
        <div class="filters">
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="🔍 搜尋標案名稱、機關..." onkeyup="filterTenders()">
            </div>
            <div class="filter-group">
                <button class="filter-btn active" id="filterAll" onclick="setCategory('all', this)">全部</button>
                <button class="filter-btn" onclick="setCategory('廣告行銷', this)">廣告行銷</button>
                <button class="filter-btn" onclick="setCategory('軟體開發', this)">軟體開發</button>
                <button class="filter-btn" onclick="setCategory('網站設計', this)">網站設計</button>
                <button class="filter-btn" onclick="setCategory('AI部署', this)">AI部署</button>
                <button class="filter-btn" onclick="setCategory('視覺設計', this)">視覺設計</button>
                <button class="filter-btn" id="filterBookmark" onclick="showBookmarksOnly()">⭐ 書籤</button>
            </div>
        </div>
        
        <div class="tender-count" id="tenderCount">
            <span>顯示 <strong>{len(tenders)}</strong> 筆標案</span>
            <div>
                <button class="btn btn-download" onclick="downloadBookmarkedTenders()" id="downloadBtn" style="display:none;">
                    📥 下載書籤標書
                </button>
                <button class="btn btn-secondary" onclick="exportBookmarks()" id="exportBtn" style="display:none;">
                    📤 匯出書籤
                </button>
            </div>
        </div>
        
        <div class="tender-list" id="tenderList">
        </div>
    </div>
    
    <script>
        const API_BASE = 'http://localhost:8080/api';
        const tenders = {json.dumps(tenders, ensure_ascii=False)};
        
        let currentCategory = 'all';
        let searchText = '';
        let showOnlyBookmarks = false;
        let bookmarkedJobs = new Set();
        let bookmarkNotes = {{}};
        let isConnected = false;
        
        // 檢查伺服器連線
        async function checkConnection() {{
            try {{
                const response = await fetch(API_BASE + '/bookmarks/list');
                if (response.ok) {{
                    isConnected = true;
                    const jobs = await response.json();
                    bookmarkedJobs = new Set(jobs || []);
                    updateConnectionStatus(true);
                    updateBookmarkCount();
                    document.getElementById('downloadBtn').style.display = bookmarkedJobs.size > 0 ? 'inline-flex' : 'none';
                    document.getElementById('exportBtn').style.display = bookmarkedJobs.size > 0 ? 'inline-flex' : 'none';
                    return true;
                }}
            }} catch (e) {{
                console.log('伺服器未啟動');
            }}
            isConnected = false;
            updateConnectionStatus(false);
            // 從 localStorage 讀取本地書籤
            loadLocalBookmarks();
            return false;
        }}
        
        function updateConnectionStatus(connected) {{
            const status = document.getElementById('connectionStatus');
            const text = document.getElementById('statusText');
            if (connected) {{
                status.className = 'connection-status connected';
                text.textContent = '已連接伺服器';
            }} else {{
                status.className = 'connection-status disconnected';
                text.textContent = '離線模式（書籤儲存於本機）';
            }}
        }}
        
        function loadLocalBookmarks() {{
            const saved = localStorage.getItem('tender_bookmarks');
            if (saved) {{
                const data = JSON.parse(saved);
                bookmarkedJobs = new Set(data.jobs || []);
                bookmarkNotes = data.notes || {{}};
            }}
            updateBookmarkCount();
        }}
        
        function saveLocalBookmarks() {{
            localStorage.setItem('tender_bookmarks', JSON.stringify({{
                jobs: Array.from(bookmarkedJobs),
                notes: bookmarkNotes
            }}));
        }}
        
        function updateBookmarkCount() {{
            document.getElementById('bookmarkCount').textContent = bookmarkedJobs.size;
            document.getElementById('downloadBtn').style.display = bookmarkedJobs.size > 0 && isConnected ? 'inline-flex' : 'none';
            document.getElementById('exportBtn').style.display = bookmarkedJobs.size > 0 && isConnected ? 'inline-flex' : 'none';
        }}
        
        function showToast(message, type = 'success') {{
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.className = 'toast show ' + type;
            setTimeout(() => {{
                toast.className = 'toast';
            }}, 3000);
        }}
        
        async function toggleBookmark(jobNumber, tender) {{
            const isBookmarked = bookmarkedJobs.has(jobNumber);
            
            if (isConnected) {{
                try {{
                    if (isBookmarked) {{
                        // 刪除書籤
                        await fetch(API_BASE + '/bookmarks?job_number=' + encodeURIComponent(jobNumber), {{
                            method: 'DELETE'
                        }});
                        bookmarkedJobs.delete(jobNumber);
                        showToast('已移除書籤');
                    }} else {{
                        // 新增書籤
                        await fetch(API_BASE + '/bookmarks', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{
                                job_number: jobNumber,
                                title: tender.title,
                                unit_name: tender.unit_name,
                                url: tender.url,
                                api_url: tender.api_url,
                                type: tender.type,
                                date: tender.date,
                                data: JSON.stringify(tender)
                            }})
                        }});
                        bookmarkedJobs.add(jobNumber);
                        showToast('已加入書籤 ⭐');
                    }}
                }} catch (e) {{
                    showToast('操作失敗: ' + e.message, 'error');
                }}
            }} else {{
                // 離線模式
                if (isBookmarked) {{
                    bookmarkedJobs.delete(jobNumber);
                    showToast('已移除書籤（本機）');
                }} else {{
                    bookmarkedJobs.add(jobNumber);
                    showToast('已加入書籤（本機）⭐');
                }}
                saveLocalBookmarks();
            }}
            
            updateBookmarkCount();
            renderTenders(getFilteredTenders());
        }}
        
        async function updateNote(jobNumber, note, priority) {{
            if (isConnected) {{
                try {{
                    await fetch(API_BASE + '/bookmarks', {{
                        method: 'PUT',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            job_number: jobNumber,
                            note: note,
                            priority: parseInt(priority)
                        }})
                    }});
                    showToast('備註已儲存');
                }} catch (e) {{
                    showToast('儲存失敗', 'error');
                }}
            }} else {{
                bookmarkNotes[jobNumber] = {{ note, priority }};
                saveLocalBookmarks();
                showToast('備註已儲存（本機）');
            }}
        }}
        
        async function downloadBookmarkedTenders() {{
            if (!isConnected) {{
                showToast('請先啟動伺服器', 'error');
                return;
            }}
            
            showToast('開始下載標書...');
            
            try {{
                const response = await fetch(API_BASE + '/bookmarks/download');
                const result = await response.json();
                
                const success = result.results.filter(r => r.status === 'success').length;
                showToast(`下載完成！成功 ${{success}}/${{result.total}} 筆`);
            }} catch (e) {{
                showToast('下載失敗: ' + e.message, 'error');
            }}
        }}
        
        async function exportBookmarks() {{
            if (!isConnected) {{
                // 離線匯出
                const data = [];
                tenders.forEach(t => {{
                    if (bookmarkedJobs.has(t.job_number)) {{
                        data.push(t);
                    }}
                }});
                
                const blob = new Blob([JSON.stringify(data, null, 2)], {{ type: 'application/json' }});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'bookmarks_' + new Date().toISOString().slice(0,10) + '.json';
                a.click();
                return;
            }}
            
            window.open(API_BASE + '/bookmarks/export', '_blank');
        }}
        
        function formatDate(dateNum) {{
            const str = String(dateNum);
            return str.slice(0, 4) + '/' + str.slice(4, 6) + '/' + str.slice(6, 8);
        }}
        
        function getFilteredTenders() {{
            let filtered = tenders;
            
            // 書籤篩選
            if (showOnlyBookmarks) {{
                filtered = filtered.filter(t => bookmarkedJobs.has(t.job_number));
            }}
            
            // 類別篩選
            if (currentCategory !== 'all') {{
                filtered = filtered.filter(t => 
                    t.matched_categories.includes(currentCategory)
                );
            }}
            
            // 文字搜尋
            if (searchText) {{
                filtered = filtered.filter(t => 
                    t.title.toLowerCase().includes(searchText) ||
                    (t.unit_name && t.unit_name.toLowerCase().includes(searchText)) ||
                    t.matched_keywords.some(kw => kw.toLowerCase().includes(searchText))
                );
            }}
            
            return filtered;
        }}
        
        function renderTenders(data) {{
            const list = document.getElementById('tenderList');
            const count = document.getElementById('tenderCount');
            
            if (data.length === 0) {{
                list.innerHTML = `
                    <div class="no-results">
                        <div class="no-results-icon">${{showOnlyBookmarks ? '⭐' : '🔍'}}</div>
                        <h3>${{showOnlyBookmarks ? '尚無書籤' : '找不到符合條件的標案'}}</h3>
                        <p>${{showOnlyBookmarks ? '點擊標案卡片上的「加入書籤」來收藏感興趣的標案' : '請嘗試其他搜尋條件'}}</p>
                    </div>
                `;
                count.querySelector('span').innerHTML = '顯示 <strong>0</strong> 筆標案';
                return;
            }}
            
            count.querySelector('span').innerHTML = `顯示 <strong>${{data.length}}</strong> 筆標案`;
            
            list.innerHTML = data.map(tender => {{
                const isBookmarked = bookmarkedJobs.has(tender.job_number);
                const tenderJson = JSON.stringify(tender).replace(/\\\\/g, '\\\\\\\\').replace(/'/g, "\\\\'");
                return `
                <div class="tender-card ${{isBookmarked ? 'bookmarked' : ''}}">
                    <div class="tender-header">
                        <div class="tender-title">${{tender.title}}</div>
                        <div class="tender-date">${{formatDate(tender.date)}}</div>
                    </div>
                    
                    <div class="tender-meta">
                        <div class="meta-item">
                            <span>🏛️</span>
                            <span>${{tender.unit_name || '未知機關'}}</span>
                        </div>
                        <div class="meta-item">
                            <span>📋</span>
                            <span>${{tender.job_number}}</span>
                        </div>
                    </div>
                    
                    <div class="tender-tags">
                        <span class="tag tag-type">${{tender.type}}</span>
                        ${{tender.matched_categories.map(cat => `<span class="tag tag-category">${{cat}}</span>`).join('')}}
                        ${{tender.matched_keywords.map(kw => `<span class="tag tag-keyword">${{kw}}</span>`).join('')}}
                    </div>
                    
                    <div class="tender-actions">
                        <a href="${{tender.url}}" target="_blank" class="btn btn-primary">
                            <span>查看詳情</span>
                            <span>→</span>
                        </a>
                        <button class="btn btn-bookmark ${{isBookmarked ? 'active' : ''}}" onclick='toggleBookmark("${{tender.job_number}}", ${{tenderJson}})'>
                            <span>${{isBookmarked ? '⭐ 已收藏' : '☆ 加入書籤'}}</span>
                        </button>
                        ${{isBookmarked ? `<button class="btn btn-secondary" onclick="toggleNote('${{tender.job_number}}')">📝 備註</button>` : ''}}
                    </div>
                    
                    ${{isBookmarked ? `
                    <div class="bookmark-note" id="note-${{tender.job_number}}">
                        <div class="bookmark-note-header">
                            <span>📝 備註</span>
                            <select class="priority-select" onchange="updateNote('${{tender.job_number}}', document.getElementById('noteText-${{tender.job_number}}').value, this.value)">
                                <option value="0">一般</option>
                                <option value="1">重要</option>
                                <option value="2">非常重要</option>
                            </select>
                        </div>
                        <textarea id="noteText-${{tender.job_number}}" placeholder="輸入備註..." onblur="updateNote('${{tender.job_number}}', this.value, this.parentElement.querySelector('.priority-select').value)"></textarea>
                    </div>
                    ` : ''}}
                </div>
            `}}).join('');
        }}
        
        function toggleNote(jobNumber) {{
            const note = document.getElementById('note-' + jobNumber);
            note.classList.toggle('show');
        }}
        
        function filterTenders() {{
            searchText = document.getElementById('searchInput').value.toLowerCase();
            renderTenders(getFilteredTenders());
        }}
        
        function setCategory(category, btn) {{
            currentCategory = category;
            showOnlyBookmarks = false;
            
            // 更新按鈕狀態
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active', 'bookmark-filter'));
            if (btn) {{
                btn.classList.add('active');
            }} else {{
                document.getElementById('filterAll').classList.add('active');
            }}
            
            renderTenders(getFilteredTenders());
        }}
        
        function showBookmarksOnly() {{
            showOnlyBookmarks = true;
            currentCategory = 'all';
            
            // 更新按鈕狀態
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active', 'bookmark-filter'));
            document.getElementById('filterBookmark').classList.add('active', 'bookmark-filter');
            
            renderTenders(getFilteredTenders());
        }}
        
        // 初始化
        (async function init() {{
            await checkConnection();
            renderTenders(tenders);
            
            // 定期檢查連線
            setInterval(checkConnection, 10000);
        }})();
    </script>
</body>
</html>
'''
    
    return html


def main():
    print("載入標案資料...")
    tenders = load_tenders()
    print(f"共 {len(tenders)} 筆")
    
    print("產生網頁...")
    html = generate_html(tenders)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✓ 網頁已產生: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
