# DataJob Insight Dashboard

채용공고 데이터를 분석하여 인사이트를 제공하는 웹 대시보드입니다.

## 프로젝트 구조

```
web-dashboard-service/
├── app.py                    # 메인 Streamlit 애플리케이션
├── pages/                    # 페이지별 모듈 (기존)
├── requirements.txt          # Python 의존성
├── Dockerfile               # Docker 설정
└── README.md                # 프로젝트 문서
```

##  실행 방법

### 로컬 실행
```bash
# 의존성 설치
pip install -r requirements.txt

# 대시보드 실행
streamlit run app.py
```

### Docker 실행
```bash
# 이미지 빌드
docker build -t datajob-dashboard .

# 컨테이너 실행
docker run -p 8501:8501 datajob-dashboard
```

## 주요 기능

- **대시보드 홈**: 프로젝트 개요 및 데이터 현황
- **기업규모별 분석**: 기업 규모별 채용 트렌드
- **기술스택 트렌드**: 인기 기술 및 프레임워크 분석
- **플랫폼별 현황**: 채용 플랫폼별 현황 비교
- **요구사항 분석**: 학력, 경력 등 채용 요구사항 분석
- **상세 데이터 탐색**: 원본 데이터 검색 및 탐색

## 설정

- `_common/config/settings.py`의 설정을 자동으로 사용
- `API_SERVICE_BASE_URL`: API 서비스 URL (기본값: http://localhost:8000)

## 개발 가이드

### 새로운 페이지 추가
1. `app.py`에 새로운 함수 추가
2. `page_names_to_funcs` 딕셔너리에 페이지 등록

### API 통신
- `get_jobs_from_api()`: 채용공고 데이터 가져오기
- `get_job_statistics()`: 통계 정보 가져오기

## 문제 해결

- **데이터 로드 실패**: API 서비스가 실행 중인지 확인
- **포트 충돌**: 다른 포트로 변경하여 실행
- **의존성 오류**: `pip install -r requirements.txt` 재실행 