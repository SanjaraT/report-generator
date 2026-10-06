from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel 
from datetime import date, datetime
from pathlib import Path
from typing import Optional
import os

from database import get_connection, init_db
from aggregator import get_report_metrics
from renderer import build_html, generate_pdf

init_db()

Path("reports").mkdir(exist_ok = True)

app = FastAPI(title = "Bookstore Report API")

class ReportRequest(BaseModel):
    force: Optional[bool] = False

@app.get("/health")
def health():
    return {"status": "ok", "service":"bookstore-report"}
@app.post("/reports", status_code=201)
def create_report(body: ReportRequest = ReportRequest()):
    today = str(date.today())
    conn = get_connection()

    # check if a report already exists for today (idempotency — Stage 5)
    existing = conn.execute(
        "SELECT * FROM reports WHERE report_date = ?", (today,)
    ).fetchone()

    if existing and not body.force:
        conn.close()
        return {
            "message": "Report already exists for today. Pass force=true to regenerate.",
            "report": {
                "id": existing["id"],
                "generated_at": existing["generated_at"],
                "file_path": existing["file_path"],
                "report_date": existing["report_date"],
            }
        }

    # generate the report
    metrics = get_report_metrics()
    html = build_html(metrics)
    output_path = f"reports/report_{today}.pdf"
    generate_pdf(html, output_path)

    generated_at = datetime.now().isoformat()

    if existing and body.force:
        # update existing record
        conn.execute(
            "UPDATE reports SET generated_at = ?, file_path = ? WHERE report_date = ?",
            (generated_at, output_path, today)
        )
        conn.commit()
        report_id = existing["id"]
    else:
        # insert new record
        cur = conn.execute(
            "INSERT INTO reports (generated_at, file_path, report_date) VALUES (?, ?, ?)",
            (generated_at, output_path, today)
        )
        conn.commit()
        report_id = cur.lastrowid

    conn.close()

    return {
        "message": "Report generated successfully",
        "report": {
            "id": report_id,
            "generated_at": generated_at,
            "file_path": output_path,
            "report_date": today,
        }
    }


# ── Stage 4: GET /reports/:id — fetch report metadata ───────────────────────
@app.get("/reports/{report_id}")
def get_report(report_id: int):
    conn = get_connection()
    report = conn.execute(
        "SELECT * FROM reports WHERE id = ?", (report_id,)
    ).fetchone()
    conn.close()

    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

    return {
        "id": report["id"],
        "generated_at": report["generated_at"],
        "file_path": report["file_path"],
        "report_date": report["report_date"],
    }


# ── Stage 4: GET /reports/:id/file — download the PDF ───────────────────────
@app.get("/reports/{report_id}/file")
def download_report(report_id: int):
    conn = get_connection()
    report = conn.execute(
        "SELECT * FROM reports WHERE id = ?", (report_id,)
    ).fetchone()
    conn.close()

    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

    file_path = report["file_path"]
    if not Path(file_path).exists():
        raise HTTPException(status_code=404, detail="PDF file not found on disk")


    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"bookstore_report_{report['report_date']}.pdf"
    )
