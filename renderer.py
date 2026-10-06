from datetime import datetime
from pathlib import Path
import asyncio
from playwright.async_api import async_playwright

def build_html(metrics: dict) -> str:
    ov = metrics["overview"]
    generated_at = datetime.now().strftime("%B %d, %Y at %H:%M")

    def rating_stars(rating_text: str) -> str:
        mapping = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
        count = mapping.get(rating_text, 0)
        return "★" * count + "☆" * (5 - count)

    # top expensive rows
    expensive_rows = ""
    for i, book in enumerate(metrics["top_expensive"], 1):
        expensive_rows += f"""
        <tr>
            <td>{i}</td>
            <td>{book['title']}</td>
            <td>£{book['price_gbp']:.2f}</td>
            <td>{rating_stars(book['rating_text'])}</td>
            <td>{book['availability']}</td>
        </tr>"""

    # top cheapest rows
    cheapest_rows = ""
    for i, book in enumerate(metrics["top_cheapest"], 1):
        cheapest_rows += f"""
        <tr>
            <td>{i}</td>
            <td>{book['title']}</td>
            <td>£{book['price_gbp']:.2f}</td>
            <td>{rating_stars(book['rating_text'])}</td>
            <td>{book['availability']}</td>
        </tr>"""

    # by rating rows
    rating_rows = ""
    for row in metrics["by_rating"]:
        rating_rows += f"""
        <tr>
            <td>{rating_stars(row['rating_text'])} ({row['rating_text']})</td>
            <td>{row['book_count']}</td>
            <td>£{row['avg_price']:.2f}</td>
            <td>£{row['total_value']:.2f}</td>
        </tr>"""

    # price bucket rows
    bucket_rows = ""
    for row in metrics["price_buckets"]:
        bucket_rows += f"""
        <tr>
            <td>{row['price_range']}</td>
            <td>{row['book_count']}</td>
            <td>£{row['avg_price']:.2f}</td>
        </tr>"""

    # top rated rows
    rated_rows = ""
    for i, book in enumerate(metrics["top_rated"], 1):
        rated_rows += f"""
        <tr>
            <td>{i}</td>
            <td>{book['title']}</td>
            <td>{rating_stars(book['rating_text'])}</td>
            <td>£{book['price_gbp']:.2f}</td>
            <td>{book['availability']}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Bookstore Report</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #1a1a1a; background: #fff; padding: 40px; font-size: 13px; }}
  .header {{ border-bottom: 3px solid #2d5bff; padding-bottom: 16px; margin-bottom: 28px; }}
  .header h1 {{ font-size: 26px; color: #2d5bff; }}
  .header p {{ color: #555; margin-top: 4px; font-size: 12px; }}
  .overview {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 32px; }}
  .card {{ background: #f5f7ff; border-left: 4px solid #2d5bff; padding: 14px 16px; border-radius: 4px; }}
  .card .label {{ font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; }}
  .card .value {{ font-size: 22px; font-weight: 700; color: #1a1a1a; margin-top: 4px; }}
  .section {{ margin-bottom: 32px; break-inside: avoid; }}
  .section h2 {{ font-size: 15px; font-weight: 700; color: #2d5bff; border-bottom: 1px solid #e0e0e0; padding-bottom: 6px; margin-bottom: 12px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  thead {{ background: #2d5bff; color: white; }}
  thead th {{ padding: 9px 12px; text-align: left; font-size: 12px; font-weight: 600; }}
  tbody tr {{ border-bottom: 1px solid #f0f0f0; }}
  tbody tr:nth-child(even) {{ background: #fafafa; }}
  tbody td {{ padding: 8px 12px; }}
  .footer {{ margin-top: 40px; border-top: 1px solid #e0e0e0; padding-top: 12px; color: #999; font-size: 11px; text-align: center; }}

  @media print {{
    body {{ padding: 20px; }}
    .section {{ break-inside: avoid; }}
    thead {{ display: table-header-group; }}
  }}
</style>
</head>
<body>

<div class="header">
  <h1>📚 Bookstore Inventory Report</h1>
  <p>Generated on {generated_at} · Source: books.toscrape.com</p>
</div>

<div class="overview">
  <div class="card">
    <div class="label">Total Books</div>
    <div class="value">{ov['total_books']}</div>
  </div>
  <div class="card">
    <div class="label">Avg Price</div>
    <div class="value">£{ov['avg_price']}</div>
  </div>
  <div class="card">
    <div class="label">Total Stock Value</div>
    <div class="value">£{ov['total_value']}</div>
  </div>
  <div class="card">
    <div class="label">Avg Rating</div>
    <div class="value">{ov['avg_rating']} / 5</div>
  </div>
  <div class="card">
    <div class="label">Min Price</div>
    <div class="value">£{ov['min_price']}</div>
  </div>
  <div class="card">
    <div class="label">Max Price</div>
    <div class="value">£{ov['max_price']}</div>
  </div>
  <div class="card">
    <div class="label">Total Stock Units</div>
    <div class="value">{ov['total_stock']}</div>
  </div>
</div>

<div class="section">
  <h2>Top 5 Most Expensive Books</h2>
  <table>
    <thead><tr><th>#</th><th>Title</th><th>Price</th><th>Rating</th><th>Stock</th></tr></thead>
    <tbody>{expensive_rows}</tbody>
  </table>
</div>

<div class="section">
  <h2>Top 5 Cheapest Books</h2>
  <table>
    <thead><tr><th>#</th><th>Title</th><th>Price</th><th>Rating</th><th>Stock</th></tr></thead>
    <tbody>{cheapest_rows}</tbody>
  </table>
</div>

<div class="section">
  <h2>Top Rated Books (4★ and above)</h2>
  <table>
    <thead><tr><th>#</th><th>Title</th><th>Rating</th><th>Price</th><th>Stock</th></tr></thead>
    <tbody>{rated_rows}</tbody>
  </table>
</div>

<div class="section">
  <h2>Books by Rating</h2>
  <table>
    <thead><tr><th>Rating</th><th>Count</th><th>Avg Price</th><th>Total Value</th></tr></thead>
    <tbody>{rating_rows}</tbody>
  </table>
</div>

<div class="section">
  <h2>Books by Price Range</h2>
  <table>
    <thead><tr><th>Price Range</th><th>Count</th><th>Avg Price</th></tr></thead>
    <tbody>{bucket_rows}</tbody>
  </table>
</div>

<div class="footer">
  Bookstore Report · Auto-generated · Data sourced from books.toscrape.com
</div>

</body>
</html>"""


async def render_pdf(html: str, output_path: str) -> str:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html, wait_until="networkidle")
        await page.pdf(
            path=output_path,
            format="A4",
            margin={"top": "20mm", "bottom": "20mm", "left": "15mm", "right": "15mm"},
            print_background=True,
        )
        await browser.close()
    return output_path


def generate_pdf(html: str, output_path: str) -> str:
    return asyncio.run(render_pdf(html, output_path))


if __name__ == "__main__":
    from aggregator import get_report_metrics
    from datetime import date

    metrics = get_report_metrics()
    html = build_html(metrics)
    path = f"reports/report_{date.today()}.pdf"
    result = generate_pdf(html, path)
    print(f"PDF generated: {result}")