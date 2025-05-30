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
├── pipeline/ # 채용공고 수집 및 배치 스크립트
├── api/ # FastAPI 기반 API 서버
├── dashboard/ # Streamlit 기반 시각화
├── data/ # 수집된 데이터 파일 및 DB 스키마
├── docs/ # 아키텍처 및 설명 문서
└── requirements.txt # 공통 패키지 목록
```


