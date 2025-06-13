# 🧭 Team Collaboration Guide

## 1. Branch Strategy

### 기본 브랜치

| 브랜치        | 설명                                  |
|---------------|---------------------------------------|
| `main`        | 운영/배포 대상 브랜치 (CI/CD 대상)     |
| `dev`         | 개발자 통합 브랜치                    |
| `feature/*`   | 기능 단위 브랜치 (ex: feature/crawler) |
| `bugfix/*`    | 버그 수정 브랜치                      |
| `hotfix/*`    | 운영 중 긴급 수정 브랜치              |

### 브랜치 네이밍 예시

- 기능 개발: `feature/posting-list`, `feature/kafka-setup`
- 버그 수정: `bugfix/list-pagination`, `bugfix/env-loader`

### 브랜치 정리

- 머지된 `feature/*`, `bugfix/*` 브랜치는 머지 후 삭제합니다.
- 오래된 feature 브랜치가 남아 있지 않도록 주 1회 정리합니다.

## 2. Commit Convention

### ✅ 기본 포맷

```
<type>: <summary>

<description> (optional)
```

### ✅ 예시

```
chore: initialize project structure and environment settings

- 디렉터리 구조 세팅
- .gitignore, .dockerignore 추가
- 초기 README 정리
```

### ✅ 주요 타입

| 타입       | 설명                                 |
|------------|--------------------------------------|
| `feat`     | 기능 추가                            |
| `fix`      | 버그 수정                            |
| `chore`    | 설정/환경/빌드 관련 변경             |
| `refactor` | 리팩토링 (동작 변화 없음)            |
| `docs`     | 문서 수정                            |


## 3. Pull Request & Merge Guide

### 🔼 PR 작성 규칙

- PR 제목 예시: `feat: add job posting filter`
- PR 설명에는 변경 내용 bullet point 정리
- 관련 이슈가 있으면 `Closes #이슈번호`로 연결

### 🔀 머지 규칙

- `main` ← `dev`: 리뷰 및 테스트 완료 시만 머지
- `dev` ← `feature/*`: 1명 이상의 리뷰 필수

## 4. Git Workflow 예시

1. `dev` 브랜치에서 새로운 기능 브랜치를 생성  
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b feature/posting-filter
2. 기능 개발 및 커밋 수행
3. origin/feature/*로 Push 후 Pull Request 생성
4. 코드 리뷰 후 승인되면 dev 브랜치로 머지
5. main 브랜치는 dev에서 충분히 테스트된 뒤만 머지

## 5. 코드 리뷰 가이드라인
- PR에 포함된 변경 내용이 명확히 드러나도록 올려주세요.
- 너무 큰 단위의 PR은 지양하고, 작게 나누어 자주 PR을 올리는 걸 권장합니다 :)
- 리뷰어는 다음을 확인합니다:
  - 기능 구현 의도와 코드가 일치하는지
  - 불필요한 코드/주석/테스트 출력물이 없는지
  - 기존 코드와의 충돌 가능성이 없는지
- 리뷰어는 가능하면 코드 라인 단위로 구체적인 피드백/질문을 남깁니다.