from fastapi import FastAPI

app = FastAPI(title = "Bookstore Report API")

@app.get("/health")
def health():
    return {"status": "ok", "service":"bookstore-report"}
