from datetime import datetime
from enum import Enum
from db import get_connection

from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from sqlalchemy import create_engine, text

from realtime_log.service.log_service import save_log

router = APIRouter()

@router.post("/logs")
async def create_log(payload: dict):
    await save_log(payload)

    return {
        "status": "success"
    }