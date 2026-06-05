from fastapi import FastAPI
from sqlalchemy import text
from db import engine
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("DB 연결 성공")
    except Exception as e:
        print(f"DB 연결 실패: {e}")
    yield

app = FastAPI(title="Bapsang API", lifespan=lifespan)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/health/db")
def health_db():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "db": str(e)}
    

# router 연결
from realtime_log.api.log_router import router

app.include_router(router)