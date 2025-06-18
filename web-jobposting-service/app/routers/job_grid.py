from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from pathlib import Path

from ..services import client

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR.parent / "templates"

templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

@router.get("/grid", response_class=HTMLResponse)
async def list_job_grids(request: Request):  
    return templates.TemplateResponse(
        "job_grid.html", 
        {"request": request, "title": "채용 공고 그리드"} 
    )

@router.get("/data", response_class=JSONResponse)
async def get_job_postings_data(skip: int = 0, limit: int = 100):
    jobs_data = await client.get_job_postings_from_api(skip=skip, limit=limit)
    return jobs_data
