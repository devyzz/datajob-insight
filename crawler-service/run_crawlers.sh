#!/bin/bash

# 크롤러 병렬 실행 스크립트 (심플 버전)
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
    echo -e "${GREEN}🚀 크롤러 병렬 실행 스크립트${NC}"
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

# 사이트 목록
declare -a SITES=("wanted" "saramin" "jobkorea")
declare -a PIDS=()

echo -e "${GREEN}🚀 크롤러 서비스 병렬 실행${NC}"
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

# 각 사이트별 크롤러 실행
for site in "${SITES[@]}"; do
    echo -e "${BLUE}🎯 ${site} 크롤러 시작...${NC}"
    
    # 명령어 구성
    if [ "$MODE" = "full" ]; then
        CMD="CRAWLER_SERVICE_MONGODB_URI=\"${MONGODB_URI}\" poetry run python main.py --site ${site} --full"
    else
        CMD="CRAWLER_SERVICE_MONGODB_URI=\"${MONGODB_URI}\" poetry run python main.py --site ${site}"
    fi
    
    echo -e "${YELLOW}   실행: ${CMD}${NC}"
    
    # 백그라운드 실행
    eval $CMD > /dev/null 2>&1 &
    PID=$!
    PIDS+=($PID)
    
    echo -e "${GREEN}✅ ${site} 크롤러 시작됨 (PID: ${PID})${NC}"
    
    # 2초 간격으로 실행 (DB 부하 분산)
    sleep 2
done

echo ""
echo -e "${GREEN}🎉 모든 크롤러가 백그라운드에서 실행 중!${NC}"
echo -e "${BLUE}📋 실행 중인 PID: ${PIDS[*]}${NC}"

echo ""
echo -e "${YELLOW}📊 모니터링 명령어:${NC}"
echo "  프로세스 상태: ps aux | grep 'python main.py'"
echo "  모든 크롤러 종료: pkill -f 'python main.py'"

echo ""
echo -e "${BLUE}⏳ 모든 크롤러 완료까지 대기 중...${NC}"

# 모든 프로세스 완료까지 대기
for i in "${!PIDS[@]}"; do
    PID=${PIDS[$i]}
    SITE=${SITES[$i]}
    echo -e "${YELLOW}⏳ ${SITE} 크롤러 대기 중 (PID: ${PID})...${NC}"
    wait $PID
    echo -e "${GREEN}✅ ${SITE} 크롤러 완료${NC}"
done

echo -e "${GREEN}🎉 모든 크롤러가 완료되었습니다!${NC}"
