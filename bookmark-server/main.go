package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	_ "github.com/mattn/go-sqlite3"
)

// Tender 標案結構
type Tender struct {
	Date              int      `json:"date"`
	Title             string   `json:"title"`
	Type              string   `json:"type"`
	UnitName          string   `json:"unit_name"`
	JobNumber         string   `json:"job_number"`
	URL               string   `json:"url"`
	APIURL            string   `json:"api_url"`
	MatchedCategories []string `json:"matched_categories"`
	MatchedKeywords   []string `json:"matched_keywords"`
}

// Bookmark 書籤結構
type Bookmark struct {
	ID        int       `json:"id"`
	JobNumber string    `json:"job_number"`
	Title     string    `json:"title"`
	UnitName  string    `json:"unit_name"`
	URL       string    `json:"url"`
	APIURL    string    `json:"api_url"`
	Type      string    `json:"type"`
	Date      int       `json:"date"`
	Note      string    `json:"note"`
	Priority  int       `json:"priority"`
	CreatedAt time.Time `json:"created_at"`
	Data      string    `json:"data"` // 完整 JSON 資料
}

var db *sql.DB

func initDB() {
	var err error
	dbPath := filepath.Join("..", "pcc_data", "2026", "bookmarks.db")
	
	// 確保目錄存在
	os.MkdirAll(filepath.Dir(dbPath), 0755)
	
	db, err = sql.Open("sqlite3", dbPath)
	if err != nil {
		log.Fatal(err)
	}

	// 建立書籤表
	createTableSQL := `
	CREATE TABLE IF NOT EXISTS bookmarks (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		job_number TEXT UNIQUE NOT NULL,
		title TEXT NOT NULL,
		unit_name TEXT,
		url TEXT,
		api_url TEXT,
		type TEXT,
		date INTEGER,
		note TEXT DEFAULT '',
		priority INTEGER DEFAULT 0,
		data TEXT,
		created_at DATETIME DEFAULT CURRENT_TIMESTAMP
	);
	
	CREATE INDEX IF NOT EXISTS idx_job_number ON bookmarks(job_number);
	CREATE INDEX IF NOT EXISTS idx_priority ON bookmarks(priority DESC);
	`

	_, err = db.Exec(createTableSQL)
	if err != nil {
		log.Fatal(err)
	}

	log.Println("資料庫初始化完成:", dbPath)
}

// CORS 中介軟體
func corsMiddleware(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")

		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}

		next(w, r)
	}
}

// 取得所有書籤
func getBookmarks(w http.ResponseWriter, r *http.Request) {
	rows, err := db.Query(`
		SELECT id, job_number, title, unit_name, url, api_url, type, date, note, priority, data, created_at 
		FROM bookmarks 
		ORDER BY priority DESC, created_at DESC
	`)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var bookmarks []Bookmark
	for rows.Next() {
		var b Bookmark
		var dataStr sql.NullString
		err := rows.Scan(&b.ID, &b.JobNumber, &b.Title, &b.UnitName, &b.URL, &b.APIURL, &b.Type, &b.Date, &b.Note, &b.Priority, &dataStr, &b.CreatedAt)
		if err != nil {
			continue
		}
		if dataStr.Valid {
			b.Data = dataStr.String
		}
		bookmarks = append(bookmarks, b)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(bookmarks)
}

// 新增書籤
func addBookmark(w http.ResponseWriter, r *http.Request) {
	var input struct {
		JobNumber string `json:"job_number"`
		Title     string `json:"title"`
		UnitName  string `json:"unit_name"`
		URL       string `json:"url"`
		APIURL    string `json:"api_url"`
		Type      string `json:"type"`
		Date      int    `json:"date"`
		Note      string `json:"note"`
		Priority  int    `json:"priority"`
		Data      string `json:"data"`
	}

	if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	result, err := db.Exec(`
		INSERT OR REPLACE INTO bookmarks (job_number, title, unit_name, url, api_url, type, date, note, priority, data)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	`, input.JobNumber, input.Title, input.UnitName, input.URL, input.APIURL, input.Type, input.Date, input.Note, input.Priority, input.Data)

	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	id, _ := result.LastInsertId()
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"id":      id,
		"message": "書籤已新增",
	})
}

// 刪除書籤
func deleteBookmark(w http.ResponseWriter, r *http.Request) {
	jobNumber := r.URL.Query().Get("job_number")
	if jobNumber == "" {
		http.Error(w, "缺少 job_number 參數", http.StatusBadRequest)
		return
	}

	_, err := db.Exec("DELETE FROM bookmarks WHERE job_number = ?", jobNumber)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"message": "書籤已刪除",
	})
}

// 更新書籤備註和優先級
func updateBookmark(w http.ResponseWriter, r *http.Request) {
	var input struct {
		JobNumber string `json:"job_number"`
		Note      string `json:"note"`
		Priority  int    `json:"priority"`
	}

	if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	_, err := db.Exec(`
		UPDATE bookmarks SET note = ?, priority = ? WHERE job_number = ?
	`, input.Note, input.Priority, input.JobNumber)

	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"message": "書籤已更新",
	})
}

// 檢查是否已加入書籤
func checkBookmark(w http.ResponseWriter, r *http.Request) {
	jobNumber := r.URL.Query().Get("job_number")
	if jobNumber == "" {
		http.Error(w, "缺少 job_number 參數", http.StatusBadRequest)
		return
	}

	var count int
	err := db.QueryRow("SELECT COUNT(*) FROM bookmarks WHERE job_number = ?", jobNumber).Scan(&count)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"bookmarked": count > 0,
	})
}

// 取得所有書籤的 job_number 列表（用於前端快速判斷）
func getBookmarkList(w http.ResponseWriter, r *http.Request) {
	rows, err := db.Query("SELECT job_number FROM bookmarks")
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var jobNumbers []string
	for rows.Next() {
		var jn string
		if err := rows.Scan(&jn); err == nil {
			jobNumbers = append(jobNumbers, jn)
		}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(jobNumbers)
}

// 下載書籤的標書資料
func downloadBookmarkedTenders(w http.ResponseWriter, r *http.Request) {
	rows, err := db.Query(`
		SELECT job_number, title, api_url 
		FROM bookmarks 
		ORDER BY priority DESC, created_at DESC
	`)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	type DownloadTask struct {
		JobNumber string `json:"job_number"`
		Title     string `json:"title"`
		APIURL    string `json:"api_url"`
	}

	var tasks []DownloadTask
	for rows.Next() {
		var t DownloadTask
		if err := rows.Scan(&t.JobNumber, &t.Title, &t.APIURL); err == nil {
			tasks = append(tasks, t)
		}
	}

	// 建立下載目錄
	downloadDir := filepath.Join("..", "pcc_data", "2026", "bookmarked_tenders")
	os.MkdirAll(downloadDir, 0755)

	results := make([]map[string]interface{}, 0)
	client := &http.Client{Timeout: 30 * time.Second}

	for _, task := range tasks {
		result := map[string]interface{}{
			"job_number": task.JobNumber,
			"title":      task.Title,
			"status":     "pending",
		}

		if task.APIURL == "" {
			result["status"] = "error"
			result["error"] = "無 API URL"
			results = append(results, result)
			continue
		}

		// 下載標案詳細資料
		resp, err := client.Get(task.APIURL)
		if err != nil {
			result["status"] = "error"
			result["error"] = err.Error()
			results = append(results, result)
			continue
		}

		body, err := io.ReadAll(resp.Body)
		resp.Body.Close()
		if err != nil {
			result["status"] = "error"
			result["error"] = err.Error()
			results = append(results, result)
			continue
		}

		// 儲存檔案
		filename := filepath.Join(downloadDir, fmt.Sprintf("%s.json", strings.ReplaceAll(task.JobNumber, "/", "_")))
		err = os.WriteFile(filename, body, 0644)
		if err != nil {
			result["status"] = "error"
			result["error"] = err.Error()
			results = append(results, result)
			continue
		}

		result["status"] = "success"
		result["file"] = filename
		results = append(results, result)

		// 避免請求過快
		time.Sleep(500 * time.Millisecond)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"total":      len(tasks),
		"results":    results,
		"output_dir": downloadDir,
	})
}

// 匯出書籤為 JSON
func exportBookmarks(w http.ResponseWriter, r *http.Request) {
	rows, err := db.Query(`
		SELECT id, job_number, title, unit_name, url, api_url, type, date, note, priority, data, created_at 
		FROM bookmarks 
		ORDER BY priority DESC, created_at DESC
	`)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var bookmarks []Bookmark
	for rows.Next() {
		var b Bookmark
		var dataStr sql.NullString
		err := rows.Scan(&b.ID, &b.JobNumber, &b.Title, &b.UnitName, &b.URL, &b.APIURL, &b.Type, &b.Date, &b.Note, &b.Priority, &dataStr, &b.CreatedAt)
		if err != nil {
			continue
		}
		if dataStr.Valid {
			b.Data = dataStr.String
		}
		bookmarks = append(bookmarks, b)
	}

	// 設定下載標頭
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=bookmarks_%s.json", time.Now().Format("20060102_150405")))
	json.NewEncoder(w).Encode(bookmarks)
}

func main() {
	initDB()
	defer db.Close()

	// API 路由
	http.HandleFunc("/api/bookmarks", corsMiddleware(func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case "GET":
			getBookmarks(w, r)
		case "POST":
			addBookmark(w, r)
		case "PUT":
			updateBookmark(w, r)
		case "DELETE":
			deleteBookmark(w, r)
		default:
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		}
	}))

	http.HandleFunc("/api/bookmarks/list", corsMiddleware(getBookmarkList))
	http.HandleFunc("/api/bookmarks/check", corsMiddleware(checkBookmark))
	http.HandleFunc("/api/bookmarks/download", corsMiddleware(downloadBookmarkedTenders))
	http.HandleFunc("/api/bookmarks/export", corsMiddleware(exportBookmarks))

	// 靜態檔案服務
	staticDir := filepath.Join("..", "pcc_data", "2026", "filtered_for_company")
	fs := http.FileServer(http.Dir(staticDir))
	http.Handle("/", fs)

	port := "8080"
	fmt.Println("========================================")
	fmt.Println("  標案書籤管理系統")
	fmt.Println("========================================")
	fmt.Printf("  伺服器啟動於: http://localhost:%s\n", port)
	fmt.Println("  API 端點:")
	fmt.Println("    GET    /api/bookmarks       - 取得所有書籤")
	fmt.Println("    POST   /api/bookmarks       - 新增書籤")
	fmt.Println("    PUT    /api/bookmarks       - 更新書籤")
	fmt.Println("    DELETE /api/bookmarks       - 刪除書籤")
	fmt.Println("    GET    /api/bookmarks/list  - 取得書籤列表")
	fmt.Println("    GET    /api/bookmarks/download - 下載標書")
	fmt.Println("    GET    /api/bookmarks/export   - 匯出書籤")
	fmt.Println("========================================")

	log.Fatal(http.ListenAndServe(":"+port, nil))
}
