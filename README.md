# 데이터 직군 채용 트렌드 분석 프로젝트

> 본 프로젝트는 **이어드림스쿨 데이터 엔지니어링 트랙 1차 미니 프로젝트**로 진행되었으며,  
> 채용 플랫폼 데이터를 수집·분석하여 실무에 가까운 데이터 파이프라인 구축과 시각화까지 경험하는 것이 목표입니다!

---

## 📌 프로젝트 개요

> **프로젝트 목적**: 실전 중심의 데이터 수집 · 적재 · API · 시각화 전 과정 구성

- 사람인, 원티드, 점핏, 잡플래닛 등 채용 플랫폼에서 데이터 직군 관련 공고를 수집
- 기업 규모, 직무 유형, 기술 키워드 등을 기준으로 트렌드 분석
- 정기적인 배치 실행을 통해 데이터 자동 수집 및 DB 적재
- FastAPI 기반 API 서버와 Streamlit 기반 대시보드 구현


---

## 🧱 기술 스택

| 구성 요소      | 사용 기술                                  |
|----------------|---------------------------------------------|
| 데이터 수집     | Python, requests, BeautifulSoup, Selenium   |
| 배치 실행       | Python + Crontab (or Airflow 대체 가능)     |
| 저장소         | PostgreSQL or SQLite                        |
| API 서버       | FastAPI                                     |
| 대시보드 시각화 | Streamlit, Plotly                           |
| 협업 및 배포    | GitHub, Docker (선택적)                    |

---

## 📁 디렉토리 구조
```bash
datajob-insight/
│
├── _common/                          # 여러 서비스에서 공통으로 사용하는 코드 모듈
│   ├── config/                       # 공통 환경변수 로더, 설정값, DB 연결 정보
│   ├── schema/                       # 공통 Pydantic 모델, JSON/SQL 스키마 정의
│   └── utils/                        # 날짜 파싱, HTML 정제, 로깅 등 유틸 함수
│
├── _infra/                           # 개발 및 배포를 위한 인프라 설정 
│   ├── mongodb/                      # MongoDB 설정 파일 및 실행 스크립트
│   └── postgres/                     # PostgreSQL 초기화 SQL 및 설정 파일
│
├── api-service/                      # FastAPI 기반 공통 백엔드 API 서버
│   ├── app/
│   │   ├── db/                       # DB 연결, CRUD 유틸 함수
│   │   ├── models/                   # 내부용 Pydantic 모델 (요청/응답 정의)
│   │   ├── routers/                  # 라우터 (jobs, stats 등 도메인 단위 API 분리)
│   │   └── main.py                   # FastAPI 앱 실행 진입점
│   ├── Dockerfile
│   └── requirements.txt
│
├── crawler-service/                 # 채용 플랫폼 크롤링 서비스 (원티드, 사람인 등)
│   ├── Dockerfile
│   └── requirements.txt
│
├── etl-service/                     # 수집된 원본 데이터를 정제하고 저장하는 ETL 서비스
│   ├── Dockerfile
│   └── requirements.txt
│
├── web-dashboard-service/          # Streamlit 기반 기술 트렌드 대시보드 웹 앱
│   ├── app.py                       # Streamlit 앱 진입점
│   ├── pages/                       # 여러 탭 구성 시 각 탭에 해당하는 페이지
│   │   └── dashboard.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── web-jobposting-service/         # FastAPI + Jinja2 + jqGrid 기반 채용 리스트 웹 앱
│   ├── main.py                      # FastAPI 앱 진입점 (HTML 렌더링)
│   ├── templates/                   # HTML 템플릿 (list.html 등)
│   ├── static/                      # 정적 자산 (jqGrid JS, CSS, 사용자 정의 스크립트)
│   │   ├── css/
│   │   │   └── jqgrid.css           # jqGrid 테이블 스타일 정의
│   │   └── js/
│   │       └── grid.js              # jqGrid 초기화 및 Ajax 설정 스크립트
│   ├── Dockerfile
│   └── requirements.txt
│
├── .env                             # 공통 환경변수 파일 (.env.template으로 관리 권장)
├── README.md                        # 프로젝트 설명, 구조, 실행 방법 등
└── docker-compose.yml              # 전체 서비스 실행을 위한 통합 Docker Compose 설정
```


