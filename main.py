from fastapi import FastAPI

app = FastAPI(title="Bapsang API")

@app.get("/health")
def health():
    return {"status": "ok"}