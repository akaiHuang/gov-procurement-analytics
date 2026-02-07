#!/usr/bin/env python3
"""
政府電子採購網資料批次下載工具
使用 g0v 社群提供的 API: https://pcc-api.openfun.app/

資料來源: https://web.pcc.gov.tw/pis/
"""

import requests
import json
import time
import os
from datetime import datetime, timedelta
from pathlib import Path


class PCCDownloader:
    """政府採購網資料下載器"""
    
    BASE_URL = "https://pcc-api.openfun.app/api"
    
    def __init__(self, output_dir="pcc_data"):
        """
        初始化下載器
        
        Args:
            output_dir: 資料輸出目錄
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PCC-Data-Downloader/1.0'
        })
    
    def _request_with_retry(self, url, params=None, max_retries=3):
        """帶重試機制的請求"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=30)
                
                # 處理 429 Too Many Requests
                if response.status_code == 429:
                    wait_time = 10 * (attempt + 1)
                    print(f"      請求過快，等待 {wait_time} 秒後重試...")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
                raise
        
        return None
    
    def get_info(self):
        """取得 API 資訊（最新/最舊資料日期、總公告數等）"""
        url = f"{self.BASE_URL}/getinfo"
        return self._request_with_retry(url)
    
    def list_by_date(self, date_str):
        """
        取得特定日期的所有標案列表
        
        Args:
            date_str: 日期字串，格式 YYYYMMDD
        
        Returns:
            標案列表
        """
        url = f"{self.BASE_URL}/listbydate"
        params = {"date": date_str}
        result = self._request_with_retry(url, params)
        
        # API 回傳格式: {"records": [...]} 或 {}
        if result and isinstance(result, dict):
            return result.get('records', [])
        return []
    
    def search_by_title(self, query, page=1):
        """
        依標案名稱搜尋
        
        Args:
            query: 搜尋關鍵字
            page: 頁數（從 1 開始）
        
        Returns:
            搜尋結果
        """
        url = f"{self.BASE_URL}/searchbytitle"
        params = {"query": query, "page": page}
        result = self._request_with_retry(url, params)
        if result and isinstance(result, dict):
            return result.get('records', [])
        return []
    
    def search_by_company(self, company_name, page=1):
        """
        依公司名稱搜尋
        
        Args:
            company_name: 公司名稱
            page: 頁數（從 1 開始）
        
        Returns:
            搜尋結果
        """
        url = f"{self.BASE_URL}/searchbycompanyname"
        params = {"query": company_name, "page": page}
        result = self._request_with_retry(url, params)
        if result and isinstance(result, dict):
            return result.get('records', [])
        return []
    
    def get_units(self):
        """取得所有機關列表"""
        url = f"{self.BASE_URL}/unit"
        return self._request_with_retry(url)
    
    def list_by_unit(self, unit_id):
        """
        取得特定機關的標案列表
        
        Args:
            unit_id: 機關代碼
        
        Returns:
            標案列表
        """
        url = f"{self.BASE_URL}/listbyunit"
        params = {"unit_id": unit_id}
        result = self._request_with_retry(url, params)
        if result and isinstance(result, dict):
            return result.get('records', [])
        return []
    
    def get_tender_detail(self, unit_id, job_number):
        """
        取得標案詳細資料
        
        Args:
            unit_id: 機關代碼
            job_number: 標案代碼
        
        Returns:
            標案詳細資料
        """
        url = f"{self.BASE_URL}/tender"
        params = {"unit_id": unit_id, "job_number": job_number}
        return self._request_with_retry(url, params)
    
    def download_date_range(self, start_date, end_date, delay=0.5):
        """
        下載指定日期範圍內的所有標案資料
        
        Args:
            start_date: 開始日期 (datetime 或 YYYYMMDD 字串)
            end_date: 結束日期 (datetime 或 YYYYMMDD 字串)
            delay: 每次請求間的延遲秒數（避免過度請求）
        """
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y%m%d")
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y%m%d")
        
        current_date = start_date
        all_data = []
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y%m%d")
            print(f"正在下載 {date_str} 的資料...")
            
            try:
                data = self.list_by_date(date_str)
                if data:
                    all_data.extend(data)
                    print(f"  找到 {len(data)} 筆標案")
                else:
                    print(f"  無資料")
            except Exception as e:
                print(f"  錯誤: {e}")
            
            current_date += timedelta(days=1)
            time.sleep(delay)  # 避免過度請求
        
        # 儲存結果
        output_file = self.output_dir / f"tenders_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n完成！共下載 {len(all_data)} 筆資料")
        print(f"已儲存至: {output_file}")
        
        return all_data
    
    def download_all_tenders_by_keyword(self, keyword, max_pages=100, delay=0.5):
        """
        依關鍵字下載所有相關標案
        
        Args:
            keyword: 搜尋關鍵字
            max_pages: 最大頁數
            delay: 每次請求間的延遲秒數
        """
        all_data = []
        page = 1
        
        while page <= max_pages:
            print(f"正在搜尋 '{keyword}' 第 {page} 頁...")
            
            try:
                data = self.search_by_title(keyword, page)
                if not data or len(data) == 0:
                    print("  已無更多資料")
                    break
                
                all_data.extend(data)
                print(f"  找到 {len(data)} 筆")
                page += 1
                
            except Exception as e:
                print(f"  錯誤: {e}")
                break
            
            time.sleep(delay)
        
        # 儲存結果
        safe_keyword = keyword.replace('/', '_').replace('\\', '_')
        output_file = self.output_dir / f"search_{safe_keyword}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n完成！共找到 {len(all_data)} 筆資料")
        print(f"已儲存至: {output_file}")
        
        return all_data
    
    def export_to_csv(self, data, filename):
        """
        將資料匯出為 CSV 格式
        
        Args:
            data: 標案資料列表
            filename: 輸出檔名
        """
        import csv
        
        if not data:
            print("無資料可匯出")
            return
        
        output_file = self.output_dir / filename
        
        # 取得所有欄位
        all_keys = set()
        for item in data:
            if isinstance(item, dict):
                all_keys.update(item.keys())
        
        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
            writer.writeheader()
            for item in data:
                if isinstance(item, dict):
                    writer.writerow(item)
        
        print(f"已匯出 CSV: {output_file}")


    def download_all_data(self, delay=0.5, save_interval=100):
        """
        下載全部歷史資料（支援斷點續傳）
        
        Args:
            delay: 每次請求間的延遲秒數
            save_interval: 每下載多少天儲存一次進度
        """
        # 取得 API 資訊
        print("正在取得 API 資訊...")
        info = self.get_info()
        
        # API 回傳格式: {"最新資料時間": "2026-01-06T00:00:00+08:00", "最舊資料時間": "1999-01-21T00:00:00+08:00", "公告數": 14153493}
        oldest_date_str = info.get('最舊資料時間', '')
        newest_date_str = info.get('最新資料時間', '')
        total_count = info.get('公告數', 0)
        
        # 解析 ISO 格式日期
        def parse_date(date_str):
            if not date_str:
                return None
            try:
                # 處理 ISO 格式 "2026-01-06T00:00:00+08:00"
                return datetime.fromisoformat(date_str.replace('+08:00', ''))
            except:
                try:
                    return datetime.strptime(date_str[:8], "%Y%m%d")
                except:
                    return None
        
        oldest_date = parse_date(oldest_date_str)
        newest_date = parse_date(newest_date_str)
        
        if oldest_date:
            print(f"資料範圍: {oldest_date.strftime('%Y-%m-%d')} ~ {newest_date.strftime('%Y-%m-%d') if newest_date else 'N/A'}")
        print(f"總公告數: {total_count:,}")
        
        if not oldest_date or not newest_date:
            print("無法取得資料範圍，嘗試使用預設範圍...")
            oldest_date = datetime(1999, 1, 21)
            newest_date = datetime.now()
        
        # 檢查進度檔案（斷點續傳）
        progress_file = self.output_dir / "download_progress.json"
        downloaded_dates = set()
        all_data_file = self.output_dir / "all_tenders.jsonl"
        
        if progress_file.exists():
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
                downloaded_dates = set(progress.get('downloaded_dates', []))
                print(f"發現進度檔案，已下載 {len(downloaded_dates)} 天的資料，繼續下載...")
        
        # 產生日期範圍
        start_date = oldest_date
        end_date = newest_date
        
        total_days = (end_date - start_date).days + 1
        current_date = start_date
        
        downloaded_count = 0
        total_tenders = 0
        days_processed = 0
        
        print(f"\n開始下載，共 {total_days} 天的資料...")
        print("=" * 60)
        
        # 使用 append 模式寫入 JSONL
        with open(all_data_file, 'a', encoding='utf-8') as data_file:
            while current_date <= end_date:
                date_str = current_date.strftime("%Y%m%d")
                
                # 跳過已下載的日期
                if date_str in downloaded_dates:
                    current_date += timedelta(days=1)
                    days_processed += 1
                    continue
                
                # 計算進度
                progress_pct = (days_processed / total_days) * 100
                
                try:
                    data = self.list_by_date(date_str)
                    count = len(data) if data else 0
                    
                    # 寫入資料（JSONL 格式，每行一筆）
                    if data:
                        for item in data:
                            item['_download_date'] = date_str
                            data_file.write(json.dumps(item, ensure_ascii=False) + '\n')
                        total_tenders += count
                    
                    downloaded_dates.add(date_str)
                    downloaded_count += 1
                    
                    print(f"[{progress_pct:5.1f}%] {date_str}: {count:4} 筆 | 累計: {total_tenders:,} 筆")
                    
                except requests.exceptions.RequestException as e:
                    print(f"[{progress_pct:5.1f}%] {date_str}: 網路錯誤 - {e}")
                    time.sleep(5)  # 網路錯誤時等待久一點
                    current_date += timedelta(days=1)
                    days_processed += 1
                    continue
                except Exception as e:
                    print(f"[{progress_pct:5.1f}%] {date_str}: 錯誤 - {e}")
                
                # 定期儲存進度
                if downloaded_count % save_interval == 0:
                    self._save_progress(progress_file, downloaded_dates, total_tenders)
                    data_file.flush()
                
                current_date += timedelta(days=1)
                days_processed += 1
                time.sleep(delay)
        
        # 最終儲存進度
        self._save_progress(progress_file, downloaded_dates, total_tenders)
        
        print("\n" + "=" * 60)
        print(f"下載完成！")
        print(f"  - 總共下載: {len(downloaded_dates)} 天")
        print(f"  - 總標案數: {total_tenders:,} 筆")
        print(f"  - 資料檔案: {all_data_file}")
        print(f"  - 進度檔案: {progress_file}")
        
        return total_tenders
    
    def _save_progress(self, progress_file, downloaded_dates, total_tenders):
        """儲存下載進度"""
        progress = {
            'downloaded_dates': list(downloaded_dates),
            'total_tenders': total_tenders,
            'last_update': datetime.now().isoformat()
        }
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
    
    def download_tender_details(self, delay=0.5, batch_size=1000):
        """
        下載所有標案的詳細資料
        需要先執行 download_all_data() 取得標案列表
        
        Args:
            delay: 每次請求間的延遲秒數
            batch_size: 每批次儲存的數量
        """
        all_data_file = self.output_dir / "all_tenders.jsonl"
        details_file = self.output_dir / "tender_details.jsonl"
        progress_file = self.output_dir / "details_progress.json"
        
        if not all_data_file.exists():
            print("請先執行 download_all_data() 下載標案列表")
            return
        
        # 讀取已下載的詳細資料 ID
        downloaded_ids = set()
        if progress_file.exists():
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
                downloaded_ids = set(progress.get('downloaded_ids', []))
                print(f"發現進度檔案，已下載 {len(downloaded_ids)} 筆詳細資料")
        
        # 讀取所有標案
        print("正在讀取標案列表...")
        tenders = []
        with open(all_data_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    tender = json.loads(line.strip())
                    tender_id = f"{tender.get('unit_id', '')}_{tender.get('job_number', '')}"
                    if tender_id not in downloaded_ids and tender.get('unit_id') and tender.get('job_number'):
                        tenders.append(tender)
                except:
                    continue
        
        print(f"需要下載 {len(tenders)} 筆詳細資料")
        
        # 下載詳細資料
        count = 0
        with open(details_file, 'a', encoding='utf-8') as f:
            for tender in tenders:
                unit_id = tender.get('unit_id', '')
                job_number = tender.get('job_number', '')
                tender_id = f"{unit_id}_{job_number}"
                
                try:
                    detail = self.get_tender_detail(unit_id, job_number)
                    if detail:
                        f.write(json.dumps(detail, ensure_ascii=False) + '\n')
                        downloaded_ids.add(tender_id)
                        count += 1
                        
                        if count % 100 == 0:
                            progress_pct = (count / len(tenders)) * 100
                            print(f"[{progress_pct:5.1f}%] 已下載 {count:,} 筆詳細資料")
                        
                        if count % batch_size == 0:
                            # 儲存進度
                            with open(progress_file, 'w', encoding='utf-8') as pf:
                                json.dump({
                                    'downloaded_ids': list(downloaded_ids),
                                    'last_update': datetime.now().isoformat()
                                }, pf, ensure_ascii=False)
                            f.flush()
                
                except Exception as e:
                    print(f"下載 {tender_id} 失敗: {e}")
                
                time.sleep(delay)
        
        # 最終儲存進度
        with open(progress_file, 'w', encoding='utf-8') as pf:
            json.dump({
                'downloaded_ids': list(downloaded_ids),
                'last_update': datetime.now().isoformat()
            }, pf, ensure_ascii=False)
        
        print(f"\n完成！共下載 {count} 筆詳細資料")
        print(f"資料檔案: {details_file}")
    
    def convert_jsonl_to_csv(self, input_file="all_tenders.jsonl", output_file="all_tenders.csv"):
        """
        將 JSONL 檔案轉換為 CSV
        
        Args:
            input_file: 輸入的 JSONL 檔名
            output_file: 輸出的 CSV 檔名
        """
        import csv
        
        input_path = self.output_dir / input_file
        output_path = self.output_dir / output_file
        
        if not input_path.exists():
            print(f"找不到檔案: {input_path}")
            return
        
        print(f"正在轉換 {input_file} 為 CSV...")
        
        # 第一遍：收集所有欄位
        all_keys = set()
        count = 0
        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    item = json.loads(line.strip())
                    all_keys.update(item.keys())
                    count += 1
                except:
                    continue
        
        print(f"  共 {count:,} 筆資料，{len(all_keys)} 個欄位")
        
        # 第二遍：寫入 CSV
        with open(input_path, 'r', encoding='utf-8') as infile, \
             open(output_path, 'w', encoding='utf-8-sig', newline='') as outfile:
            
            writer = csv.DictWriter(outfile, fieldnames=sorted(all_keys))
            writer.writeheader()
            
            for line in infile:
                try:
                    item = json.loads(line.strip())
                    writer.writerow(item)
                except:
                    continue
        
        print(f"  已儲存至: {output_path}")
    
    def get_statistics(self):
        """取得下載統計資訊"""
        progress_file = self.output_dir / "download_progress.json"
        all_data_file = self.output_dir / "all_tenders.jsonl"
        
        stats = {
            'downloaded_days': 0,
            'total_tenders': 0,
            'file_size_mb': 0,
            'last_update': None
        }
        
        if progress_file.exists():
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
                stats['downloaded_days'] = len(progress.get('downloaded_dates', []))
                stats['total_tenders'] = progress.get('total_tenders', 0)
                stats['last_update'] = progress.get('last_update')
        
        if all_data_file.exists():
            stats['file_size_mb'] = all_data_file.stat().st_size / (1024 * 1024)
        
        return stats


def main():
    """主程式 - 下載全部資料"""
    import argparse
    
    parser = argparse.ArgumentParser(description='政府電子採購網資料下載工具')
    parser.add_argument('--mode', choices=['all', 'details', 'recent', 'info', 'convert'],
                        default='all', help='執行模式')
    parser.add_argument('--days', type=int, default=7, help='recent 模式下載的天數')
    parser.add_argument('--delay', type=float, default=0.3, help='請求間隔秒數')
    parser.add_argument('--output', default='pcc_data', help='輸出目錄')
    
    args = parser.parse_args()
    
    downloader = PCCDownloader(output_dir=args.output)
    
    if args.mode == 'info':
        # 顯示 API 資訊和下載統計
        print("=" * 60)
        print("API 資訊:")
        print("=" * 60)
        info = downloader.get_info()
        print(json.dumps(info, ensure_ascii=False, indent=2))
        
        print("\n" + "=" * 60)
        print("下載統計:")
        print("=" * 60)
        stats = downloader.get_statistics()
        print(f"  已下載天數: {stats['downloaded_days']:,}")
        print(f"  總標案數: {stats['total_tenders']:,}")
        print(f"  檔案大小: {stats['file_size_mb']:.2f} MB")
        print(f"  最後更新: {stats['last_update']}")
    
    elif args.mode == 'all':
        # 下載全部歷史資料
        print("=" * 60)
        print("開始下載全部歷史資料...")
        print("提示: 可隨時按 Ctrl+C 中斷，下次執行會從中斷處繼續")
        print("=" * 60)
        try:
            downloader.download_all_data(delay=args.delay)
        except KeyboardInterrupt:
            print("\n\n使用者中斷，進度已儲存")
    
    elif args.mode == 'details':
        # 下載標案詳細資料
        print("=" * 60)
        print("開始下載標案詳細資料...")
        print("=" * 60)
        try:
            downloader.download_tender_details(delay=args.delay)
        except KeyboardInterrupt:
            print("\n\n使用者中斷，進度已儲存")
    
    elif args.mode == 'recent':
        # 下載最近 N 天的資料
        print("=" * 60)
        print(f"下載最近 {args.days} 天的資料...")
        print("=" * 60)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
        downloader.download_date_range(
            start_date.strftime("%Y%m%d"),
            end_date.strftime("%Y%m%d"),
            delay=args.delay
        )
    
    elif args.mode == 'convert':
        # 轉換為 CSV
        print("=" * 60)
        print("轉換資料為 CSV 格式...")
        print("=" * 60)
        downloader.convert_jsonl_to_csv()
    
    print("\n完成！")


if __name__ == "__main__":
    main()
