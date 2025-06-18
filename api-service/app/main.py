from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # CORSMiddleware 임포트
from .db.session import engine, Base # 추가
from .models import job_grid
from .routers import job_grid 

Base.metadata.create_all(bind=engine) # 추가

app = FastAPI()

# CORS 설정 시작
origins = [
    "http://localhost:8001", # web-jobposting-service의 주소
    # 필요한 경우 다른 출처도 추가
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # 모든 HTTP 메소드 허용
    allow_headers=["*"], # 모든 HTTP 헤더 허용
)
# CORS 설정 끝


app.include_router(job_grid.router, prefix="/api", tags=["Api Server"]) # 라우터 등록
