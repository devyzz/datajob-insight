from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routers import job_grid
from .core.config import settings
from pathlib import Path
import os
import logging


app = FastAPI(title=settings.APP_NAME)

# 정적 파일 마운트 (CSS, JS)
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 라우터 포함
app.include_router(job_grid.router, prefix="/jobs", tags=["Job Grid Web"]) 


@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}"}
