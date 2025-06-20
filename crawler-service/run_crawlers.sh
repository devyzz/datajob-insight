#!/bin/bash

# 크롤러 순차 실행 스크립트
# Usage: ./run_crawlers.sh [mode] [mongodb_uri]
#   mode: normal(기본값) | full
#   mongodb_uri: MongoDB 연결 주소 (기본값: mongodb://localhost:27017/)
#
# Examples:
#   ./run_crawlers.sh
#   ./run_crawlers.sh full
#   ./run_crawlers.sh normal mongodb://163.163.80.133:27017/
#   ./run_crawlers.sh full mongodb://163.163.80.133:27017/

set -e

# 색깔 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 인자 파싱
MODE="${1:-normal}"
MONGODB_ARG="${2:-}"

# MongoDB URI 설정 (우선순위: 인자 > 환경변수 > 기본값)
if [ -n "$MONGODB_ARG" ]; then
    MONGODB_URI="$MONGODB_ARG"
elif [ -n "$CRAWLER_SERVICE_MONGODB_URI" ]; then
    MONGODB_URI="$CRAWLER_SERVICE_MONGODB_URI"
else
    MONGODB_URI="mongodb://localhost:27017/"
fi

# 도움말 표시
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    echo -e "${GREEN}🚀 크롤러 순차 실행 스크립트${NC}"
    echo ""
    echo -e "${YELLOW}사용법:${NC}"
    echo "  ./run_crawlers.sh [mode] [mongodb_uri]"
    echo ""
    echo -e "${YELLOW}인자:${NC}"
    echo "  mode        : normal(기본값) | full"
    echo "  mongodb_uri : MongoDB 연결 주소"
    echo ""
    echo -e "${YELLOW}예시:${NC}"
    echo "  ./run_crawlers.sh"
    echo "  ./run_crawlers.sh full"
    echo "  ./run_crawlers.sh normal mongodb://163.163.80.133:27017/"
    echo "  ./run_crawlers.sh full mongodb://163.163.80.133:27017/"
    echo ""
    echo -e "${YELLOW}환경변수:${NC}"
    echo "  CRAWLER_SERVICE_MONGODB_URI : MongoDB URI 설정"
    exit 0
fi

# 모드 검증
if [ "$MODE" != "normal" ] && [ "$MODE" != "full" ]; then
    echo -e "${RED}❌ 잘못된 모드: $MODE${NC}"
    echo -e "${YELLOW}💡 사용 가능한 모드: normal, full${NC}"
    echo -e "${BLUE}도움말: ./run_crawlers.sh --help${NC}"
    exit 1
fi

# Playwright 브라우저 설치 확인 및 설치
echo -e "${BLUE}🔍 Playwright 브라우저 설치 상태 확인 중...${NC}"
if ! poetry run python -c "import playwright; from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.chromium.launch(); p.stop()" &>/dev/null; then
    echo -e "${YELLOW}⚠️ Playwright 브라우저가 설치되지 않았습니다. 설치를 시작합니다...${NC}"
    if poetry run playwright install; then
        echo -e "${GREEN}✅ Playwright 브라우저 설치 완료${NC}"
    else
        echo -e "${RED}❌ Playwright 브라우저 설치 실패${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Playwright 브라우저 설치 확인됨${NC}"
fi

# 사이트 목록
declare -a SITES=("wanted" "saramin" "jobkorea")

echo -e "${GREEN}🚀 크롤러 서비스 순차 실행${NC}"
echo -e "${BLUE}📊 MongoDB URI: ${MONGODB_URI}${NC}"
echo -e "${BLUE}🔧 실행 모드: ${MODE}${NC}"
if [ -n "$MONGODB_ARG" ]; then
    echo -e "${BLUE}🔗 MongoDB 설정: 인자로 전달됨${NC}"
elif [ -n "$CRAWLER_SERVICE_MONGODB_URI" ]; then
    echo -e "${BLUE}🔗 MongoDB 설정: 환경변수${NC}"
else
    echo -e "${BLUE}🔗 MongoDB 설정: 기본값${NC}"
fi
echo "=================================="

# 실행 예정 명령어 표시
echo -e "${YELLOW}📋 실행할 명령어들:${NC}"
for site in "${SITES[@]}"; do
    if [ "$MODE" = "full" ]; then
        cmd="CRAWLER_SERVICE_MONGODB_URI=\"${MONGODB_URI}\" poetry run python main.py --site ${site} --full"
    else
        cmd="CRAWLER_SERVICE_MONGODB_URI=\"${MONGODB_URI}\" poetry run python main.py --site ${site}"
    fi
    echo -e "${GREEN}  ${site}:${NC} ${cmd}"
done
echo "=================================="

# 각 사이트별 크롤러 순차 실행
for site in "${SITES[@]}"; do
    echo -e "${BLUE}🎯 ${site} 크롤러 시작...${NC}"
    
    # 이전 브라우저 프로세스 정리 (좀비 프로세스 방지)
    echo -e "${YELLOW}🧹 이전 브라우저 프로세스 정리 중...${NC}"
    pkill -f "chromium\|firefox\|webkit" 2>/dev/null || true
    sleep 1

    # 명령어 구성
    if [ "$MODE" = "full" ]; then
        CMD="CRAWLER_SERVICE_MONGODB_URI=\"${MONGODB_URI}\" poetry run python main.py --site ${site} --full"
    else
        CMD="CRAWLER_SERVICE_MONGODB_URI=\"${MONGODB_URI}\" poetry run python main.py --site ${site}"
    fi

    echo -e "${YELLOW}   실행: ${CMD}${NC}"

    # 순차 실행 (출력 표시)
    if eval $CMD; then
        echo -e "${GREEN}✅ ${site} 크롤러 완료${NC}"
        
        # 다음 크롤러 시작 전 잠시 대기 (서버 부하 분산)
        if [ "$site" != "jobkorea" ]; then  # 마지막이 아니면
            echo -e "${BLUE}⏳ 3초 후 다음 크롤러 시작...${NC}"
            sleep 3
        fi
    else
        echo -e "${RED}❌ ${site} 크롤러 실행 실패${NC}"
        # 실패 시에도 브라우저 프로세스 정리
        pkill -f "chromium\|firefox\|webkit" 2>/dev/null || true
        exit 1
    fi

    echo ""
done

echo -e "${GREEN}🎉 모든 크롤러가 순차적으로 완료되었습니다!${NC}"
