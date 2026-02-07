# Gov Procurement Analytics

### Taiwan Government Tender Intelligence

> Transform opaque government procurement data into searchable, filterable business intelligence -- powered by g0v community APIs and automated analysis pipelines.

---

## Why This Exists

Taiwan's government procurement market represents billions in annual spending, yet the official portal (web.pcc.gov.tw) makes it nearly impossible to efficiently discover relevant opportunities. Tenders are buried in paginated lists with no meaningful filtering, no category-based search, and no way to match opportunities to a company's actual capabilities.

This project closes that gap. It batch-downloads procurement data via the g0v community API, applies intelligent keyword filtering across service categories (advertising, software development, web design, AI deployment, visual design), excludes irrelevant sectors (construction, medical, cleaning), and generates a browsable web interface with bookmark functionality. What used to take hours of manual searching now runs in minutes.

---

## Architecture

```
g0v Community API (pcc-api.openfun.app)
              |
    Batch Download Engine
    (rate-limited, resumable, with progress tracking)
              |
   +----------+----------+
   |                     |
 Raw JSONL Storage     Category Splitter
 (by date/year)        (engineering/goods/services/other)
              |
    Keyword Filter Engine
    (5 service categories, exclusion rules, bid-type filtering)
              |
   +----------+----------+----------+
   |          |          |          |
 Category    Summary    Interactive  Bookmark
 JSONL       Report     Web UI       Server
 Files       (Markdown) (HTML/CSS/JS) (Go + SQLite)
```

### Core Pipeline

| Script | Purpose |
|--------|---------|
| `download_pcc_data.py` | Full-featured batch downloader with retry logic, rate limiting, date-range support, keyword search, and CSV export. The `PCCDownloader` class provides a clean API for custom data retrieval. |
| `download_2026.py` | Focused downloader for current-year tenders with resumable progress tracking and automatic category splitting. |
| `filter_tenders.py` | Intelligent tender matching engine. Classifies tenders across 5 service categories using 80+ keywords, applies exclusion rules for irrelevant sectors, and generates categorized output with summary reports. |
| `split_tenders.py` | Large-dataset organizer. Splits bulk JSONL files by procurement category (engineering, goods, services) and year, with automatic index generation. |
| `generate_web.py` | Generates a full interactive web application (31KB) with category filters, search, bookmarking, and a responsive gradient UI for browsing filtered tenders. |
| `bookmark-server/` | Go-based REST API server with SQLite persistence for saving, managing, and annotating bookmarked tenders. |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Data Ingestion** | Python, requests (with retry/rate-limit) |
| **Data Source** | g0v Community API (pcc-api.openfun.app) |
| **Data Format** | JSONL (line-delimited JSON) |
| **Filtering** | Python (80+ keywords, 5 categories, exclusion rules) |
| **Web Interface** | Generated HTML/CSS/JS (responsive, interactive) |
| **Bookmark Server** | Go, SQLite, net/http |
| **UI Testing** | Dedicated `uitest/` directory |

---

## Quick Start

```bash
# Install dependencies
pip install requests

# Download current-year tender data
python download_2026.py

# Filter tenders matching your company's capabilities
python filter_tenders.py

# Generate interactive web browser
python generate_web.py

# Start bookmark server (optional)
cd bookmark-server && go run main.go
```

### Programmatic Usage

```python
from download_pcc_data import PCCDownloader

downloader = PCCDownloader(output_dir="my_data")

# Download by date range
downloader.download_date_range("20260101", "20260131")

# Search by keyword
downloader.download_all_tenders_by_keyword("software development")

# Export to CSV
data = downloader.search_by_title("cloud services")
downloader.export_to_csv(data, "cloud_tenders.csv")
```

---

## Service Category Matching

The filter engine matches tenders against these professional service categories:

| Category | Sample Keywords |
|----------|----------------|
| **Advertising & Marketing** | branding, PR, media, social, SEO, events, campaigns |
| **Software Development** | software, APP, API, system development, custom modules |
| **Web Design** | website, RWD, responsive, e-commerce, portal |
| **AI Deployment** | AI, machine learning, LLM, GPT, automation, algorithms |
| **Visual Design** | UI/UX, graphic design, multimedia, video, animation |

Automatically excludes: construction, medical, cleaning, security, catering, printing, and other irrelevant sectors.

---

## Data Source & Licensing

- **Official Source**: [Government E-Procurement System](https://web.pcc.gov.tw/pis/)
- **API Provider**: [g0v Community](https://pcc-api.openfun.app/) (open source civic tech)
- **Data License**: Government open data -- free for personal, educational, and reporting use. Commercial use should reference official open data sets.

---

## Author

**Huang Akai (Kai)** -- Founder @ Universal FAW Labs | Creative Technologist | Ex-Ogilvy | 15+ years experience

---

## License

MIT
