# Bookstore Report Generator

A FastAPI-based report pipeline that queries a SQLite database of scraped bookstore data, renders the metrics into a styled HTML template, generates a downloadable PDF using Playwright, and exposes REST API endpoints to trigger and serve reports.

Built as part of the FlyRank AI internship (Week 3 · Report Generator assignment).

## What it does

- Queries aggregated metrics from 60 scraped books (prices, ratings, stock levels)
- Renders a multi-section styled HTML report with tables and summary cards
- Generates a PDF using Playwright (Chromium) with proper page-break handling
- Exposes three REST endpoints: generate, fetch metadata, download file
- Prevents duplicate work via idempotency — reports generated once per day unless `force=true` is passed
- Logs every generated report to the database with its file path and timestamp

## The 4-step pipeline

```
Query (SQL aggregation)
    ↓
Render (HTML template → Playwright → PDF)
    ↓
Store (save .pdf to disk, log path in database)
    ↓
Serve (API endpoints for generation and download)
```

## Tech stack

- **FastAPI** — API layer
- **SQLite** — database (books inventory + report log)
- **Playwright (Chromium)** — headless browser for HTML-to-PDF rendering
- **Python** — aggregation, templating, pipeline logic

## Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/SanjaraT/report-generator
   cd report-generator
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate      # Windows
   # source venv/bin/activate # Mac/Linux
   ```

3. Install dependencies:
   ```bash
   pip install fastapi uvicorn playwright aiofiles python-dotenv
   playwright install chromium
   ```

4. Seed the database (runs automatically on server start, or manually):
   ```bash
   python database.py
   ```

5. Start the server:
   ```bash
   uvicorn main:app --reload
   ```

6. Open interactive docs at `http://localhost:8000/docs`

## API reference

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | None | Check server status |
| POST | `/reports` | None | Generate today's report (idempotent) |
| GET | `/reports/{id}` | None | Fetch report metadata by ID |
| GET | `/reports/{id}/file` | None | Download the PDF |

### POST /reports

Generates a PDF report from the current bookstore data and stores it.

**Request body (optional):**
```json
{ "force": false }
```

- `force: false` (default) — returns existing report if one was already generated today
- `force: true` — regenerates and overwrites today's report

**Response (201 Created):**
```json
{
  "message": "Report generated successfully",
  "report": {
    "id": 1,
    "generated_at": "2026-09-15T13:42:00.123456",
    "file_path": "reports/report_2026-09-15.pdf",
    "report_date": "2026-09-15"
  }
}
```

**Response when report already exists (200 OK):**
```json
{
  "message": "Report already exists for today. Pass force=true to regenerate.",
  "report": { ... }
}
```

### GET /reports/{id}

Returns metadata for a specific report.

**Response (200 OK):**
```json
{
  "id": 1,
  "generated_at": "2026-09-15T13:42:00.123456",
  "file_path": "reports/report_2026-09-15.pdf",
  "report_date": "2026-09-15"
}
```

**Response (404 Not Found):**
```json
{ "detail": "Report 99 not found" }
```

### GET /reports/{id}/file

Downloads the generated PDF directly.

- Returns the PDF as `application/pdf`
- 404 if the report ID doesn't exist or the file was deleted from disk

## Idempotency

Calling `POST /reports` multiple times on the same day returns the already-generated report without re-running the pipeline. This prevents duplicate work and avoids overwriting a valid PDF unnecessarily. Pass `{"force": true}` to override this behavior and regenerate.

## Report contents

The generated PDF includes:

- **Overview cards** — total books, average price, min/max price, total stock value, average rating, total stock units
- **Top 5 most expensive books** — title, price, rating, stock
- **Top 5 cheapest books** — title, price, rating, stock
- **Top rated books** — books rated 4★ and above
- **Books by rating** — count, average price, and total value per star rating
- **Books by price range** — bucketed into Under £20 / £20-£35 / £35-£50 / £50+

## Project structure

```
bookstore_report/
├── main.py           — FastAPI app, all API endpoints
├── database.py       — SQLite setup, table creation, data seeding
├── aggregator.py     — SQL aggregation queries (COUNT, AVG, SUM, GROUP BY)
├── renderer.py       — HTML template builder + Playwright PDF generator
├── books.json        — source data (60 books scraped from books.toscrape.com)
├── reports/          — generated PDF files (gitignored)
├── report.db         — SQLite database (gitignored)
├── .env.example      — environment variable template
├── .gitignore        — excludes .db files, PDFs, venv
└── README.md
```

## Proof of operation

### Generating a report
```
POST /reports
→ 201 Created
→ { "message": "Report generated successfully", "report": { "id": 1, ... } }
```

### Idempotency check (second call same day)
```
POST /reports
→ 200 OK
→ { "message": "Report already exists for today. Pass force=true to regenerate.", ... }
```

### Forced regeneration
```
POST /reports  body: { "force": true }
→ 201 Created
→ fresh generated_at timestamp, same file path
```

### Downloading the PDF
```
GET /reports/1/file
→ 200 OK, Content-Type: application/pdf
→ file downloads as bookstore_report_2026-xx-xx.pdf
```

## Aggregation SQL used

```sql
-- Overview metrics
SELECT COUNT(*), ROUND(AVG(price_gbp), 2), ROUND(MIN(price_gbp), 2),
       ROUND(MAX(price_gbp), 2), ROUND(SUM(price_gbp), 2),
       ROUND(AVG(rating), 2), SUM(availability)
FROM books;

-- Top 5 most expensive
SELECT title, price_gbp, rating_text, availability
FROM books ORDER BY price_gbp DESC LIMIT 5;

-- Grouped by rating
SELECT rating_text, COUNT(*), ROUND(AVG(price_gbp), 2), ROUND(SUM(price_gbp), 2)
FROM books GROUP BY rating ORDER BY rating DESC;

-- Price range buckets
SELECT CASE WHEN price_gbp < 20 THEN 'Under £20'
            WHEN price_gbp < 35 THEN '£20 - £35'
            WHEN price_gbp < 50 THEN '£35 - £50'
            ELSE '£50 and above' END as price_range,
       COUNT(*), ROUND(AVG(price_gbp), 2)
FROM books GROUP BY price_range;
```