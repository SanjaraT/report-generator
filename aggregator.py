from database import get_connection

def get_report_metrics():
    conn = get_connection()

    # total books and overall stats
    overview = conn.execute("""
        SELECT
            COUNT(*) as total_books,
            ROUND(AVG(price_gbp), 2) as avg_price,
            ROUND(MIN(price_gbp), 2) as min_price,
            ROUND(MAX(price_gbp), 2) as max_price,
            ROUND(SUM(price_gbp), 2) as total_value,
            ROUND(AVG(rating), 2) as avg_rating,
            SUM(availability) as total_stock
        FROM books
    """).fetchone()

    # top 5 most expensive books
    top_expensive = conn.execute("""
        SELECT title, price_gbp, rating_text, availability
        FROM books
        ORDER BY price_gbp DESC
        LIMIT 5
    """).fetchall()

    # top 5 cheapest books
    top_cheapest = conn.execute("""
        SELECT title, price_gbp, rating_text, availability
        FROM books
        ORDER BY price_gbp ASC
        LIMIT 5
    """).fetchall()

    # books grouped by rating
    by_rating = conn.execute("""
        SELECT
            rating_text,
            rating,
            COUNT(*) as book_count,
            ROUND(AVG(price_gbp), 2) as avg_price,
            ROUND(SUM(price_gbp), 2) as total_value
        FROM books
        GROUP BY rating
        ORDER BY rating DESC
    """).fetchall()

    # price range buckets
    price_buckets = conn.execute("""
        SELECT
            CASE
                WHEN price_gbp < 20 THEN 'Under £20'
                WHEN price_gbp < 35 THEN '£20 - £35'
                WHEN price_gbp < 50 THEN '£35 - £50'
                ELSE '£50 and above'
            END as price_range,
            COUNT(*) as book_count,
            ROUND(AVG(price_gbp), 2) as avg_price
        FROM books
        GROUP BY price_range
        ORDER BY MIN(price_gbp)
    """).fetchall()

    # top 5 highest rated + most expensive (quality picks)
    top_rated = conn.execute("""
        SELECT title, price_gbp, rating_text, rating, availability
        FROM books
        WHERE rating >= 4
        ORDER BY rating DESC, price_gbp DESC
        LIMIT 5
    """).fetchall()

    conn.close()

    return {
        "overview": dict(overview),
        "top_expensive": [dict(r) for r in top_expensive],
        "top_cheapest": [dict(r) for r in top_cheapest],
        "by_rating": [dict(r) for r in by_rating],
        "price_buckets": [dict(r) for r in price_buckets],
        "top_rated": [dict(r) for r in top_rated],
    }

if __name__ == "__main__":
    import json
    metrics = get_report_metrics()
    print(json.dumps(metrics, indent=2))