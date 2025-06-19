"""
기술스택 정규화 유틸리티
- 원티드, 사람인, 잡코리아 공통 사용
- 기술명 통합 및 카테고리 분류
- 맥락(필수/우대/경험) 추론
"""

import re
from typing import Dict, List, Optional
from enum import Enum

class TechCategory(Enum):
    LANGUAGE = "language"
    FRAMEWORK = "framework" 
    DATABASE = "database"
    CLOUD = "cloud"
    TOOL = "tool"
    RUNTIME = "runtime"
    MESSAGING = "messaging"
    MONITORING = "monitoring"
    API = "api"

class TechStackNormalizer:
    """기술스택 정규화 엔진 - 3개 플랫폼 공통 사용"""
    
    def __init__(self):
        # 기술스택 매핑 테이블 - 실제 기업에서 사용하는 기술 기준
        self.tech_mapping = {
            # ===== 프로그래밍 언어 =====
            "language": {
                "javascript": ["javascript", "js"],
                "typescript": ["typescript", "ts"], 
                "python": ["python"],
                "java": ["java"],
                "kotlin": ["kotlin"],
                "swift": ["swift"],
                "go": ["go", "golang"],
                "rust": ["rust"],
                "php": ["php"],
                "ruby": ["ruby"],
                "scala": ["scala"],
                "csharp": ["c#", "csharp"],
                "cpp": ["c++", "cpp"],
                "c": ["c언어", "c"],
                "dart": ["dart"],
                "html": ["html", "html5"],
                "css": ["css", "css3"],
            },
            
            # ===== 프레임워크/라이브러리 =====
            "framework": {
                "react": ["react", "react.js", "reactjs"],
                "vue": ["vue", "vue.js", "vuejs"],
                "angular": ["angular", "angularjs"],
                "svelte": ["svelte"],
                "nextjs": ["next.js", "nextjs", "next"],
                "nuxtjs": ["nuxt.js", "nuxtjs", "nuxt"],
                "spring": ["spring"],
                "spring_boot": ["spring boot", "springboot"],
                "django": ["django"],
                "flask": ["flask"],
                "fastapi": ["fastapi"],
                "express": ["express", "express.js", "expressjs"],
                "nestjs": ["nest.js", "nestjs"],
                "laravel": ["laravel"],
                "rails": ["rails", "ruby on rails"],
                "dotnet": [".net", "dotnet"],
                "flutter": ["flutter"],
                "react_native": ["react native"],
                "jquery": ["jquery"],
                "bootstrap": ["bootstrap"],
                "tailwind": ["tailwind", "tailwindcss"],
            },
            
            # ===== 데이터베이스 =====
            "database": {
                "mysql": ["mysql"],
                "postgresql": ["postgresql", "postgres"],
                "mongodb": ["mongodb", "mongo"],
                "redis": ["redis"],
                "oracle": ["oracle", "oracle db"],
                "sqlite": ["sqlite"],
                "mariadb": ["mariadb"],
                "elasticsearch": ["elasticsearch", "elastic search"],
                "dynamodb": ["dynamodb"],
                "cassandra": ["cassandra"],
                "influxdb": ["influxdb"],
                "neo4j": ["neo4j"],
            },
            
            # ===== 클라우드/인프라 =====
            "cloud": {
                "aws": ["aws", "amazon web services"],
                "azure": ["azure", "microsoft azure"],
                "gcp": ["gcp", "google cloud", "google cloud platform"],
                "docker": ["docker"],
                "kubernetes": ["kubernetes", "k8s"],
                "jenkins": ["jenkins"],
                "github_actions": ["github actions"],
                "gitlab_ci": ["gitlab ci", "gitlab-ci"],
                "terraform": ["terraform"],
                "ansible": ["ansible"],
                "nginx": ["nginx"],
                "apache": ["apache"],
                "cloudflare": ["cloudflare"],
            },
            
            # ===== 런타임/플랫폼 =====
            "runtime": {
                "nodejs": ["node.js", "nodejs", "node"],
                "deno": ["deno"],
                "bun": ["bun"],
            },
            
            # ===== 메시징/큐 =====
            "messaging": {
                "rabbitmq": ["rabbitmq", "rabbit mq"],
                "kafka": ["kafka", "apache kafka"],
                "redis_queue": ["redis queue"],
                "sqs": ["sqs", "amazon sqs"],
                "pubsub": ["pub/sub", "pubsub"],
            },
            
            # ===== 모니터링/로깅 =====
            "monitoring": {
                "elk_stack": ["elk", "elastic stack", "elk stack"],
                "prometheus": ["prometheus"],
                "grafana": ["grafana"],
                "cloudwatch": ["cloudwatch", "aws cloudwatch"],
                "datadog": ["datadog"],
                "newrelic": ["new relic", "newrelic"],
                "sentry": ["sentry"],
            },
            
            # ===== API/통신 =====
            "api": {
                "rest": ["rest", "restful", "rest api"],
                "graphql": ["graphql"],
                "grpc": ["grpc"],
                "websocket": ["websocket"],
                "socket_io": ["socket.io"],
            },
            
            # ===== 도구/기타 =====
            "tool": {
                "git": ["git"],
                "github": ["github"],
                "gitlab": ["gitlab"],
                "jira": ["jira"],
                "confluence": ["confluence"],
                "slack": ["slack"],
                "notion": ["notion"],
                "figma": ["figma"],
                "postman": ["postman"],
                "webpack": ["webpack"],
                "vite": ["vite"],
                "babel": ["babel"],
                "eslint": ["eslint"],
                "prettier": ["prettier"],
                "jest": ["jest"],
                "cypress": ["cypress"],
                "selenium": ["selenium"],
            }
        }
        
        # 역방향 매핑 구축 (성능 최적화)
        self.reverse_mapping = self._build_reverse_mapping()
        
        # 맥락 추론 키워드
        self.context_keywords = {
            "필수": ["필수", "required", "must"],
            "우대": ["우대", "preferred", "plus", "advantage", "welcome"],
            "경험": ["경험", "experience", "familiar", "knowledge"]
        }
    
    def _build_reverse_mapping(self) -> Dict[str, Dict]:
        """기술명 -> 정보 역방향 매핑 테이블 구축"""
        reverse_map = {}
        
        for category, techs in self.tech_mapping.items():
            for normalized_name, aliases in techs.items():
                for alias in aliases:
                    # 정규화된 키워드로 저장
                    normalized_alias = self._normalize_tech_name(alias)
                    reverse_map[normalized_alias] = {
                        "tech": normalized_name,
                        "category": category,
                        "original_aliases": aliases
                    }
        
        return reverse_map
    
    def _normalize_tech_name(self, tech_name: str) -> str:
        """기술명 정규화"""
        if not tech_name:
            return ""
        
        # 소문자 변환
        normalized = tech_name.lower()
        
        # 특수문자 및 공백 제거
        normalized = re.sub(r'[.\-_\s]+', '', normalized)
        
        return normalized.strip()
    
    def _infer_context(self, tech_name: str, full_text: str) -> str:
        """기술의 맥락(필수/우대/경험) 추론"""
        if not full_text:
            return "경험"  # 기본값
        
        tech_lower = tech_name.lower()
        text_lower = full_text.lower()
        
        # 기술명 주변 텍스트에서 맥락 키워드 찾기
        for context, keywords in self.context_keywords.items():
            for keyword in keywords:
                # "Java 필수" 또는 "필수: Java" 형태 검사
                if (f"{tech_lower} {keyword}" in text_lower or 
                    f"{keyword} {tech_lower}" in text_lower or
                    f"{keyword}:" in text_lower and tech_lower in text_lower):
                    return context
        
        return "경험"  # 기본값
    
    def normalize_tech_stack(self, raw_text: str, raw_list: List[str], 
                           full_job_text: str = "") -> dict:
        """
        기술스택 정보 정규화
        
        Args:
            raw_text: 원본 텍스트
            raw_list: 원본 리스트  
            full_job_text: 전체 채용공고 텍스트 (맥락 추론용)
            
        Returns:
            정규화된 기술스택 딕셔너리
        """
        # 처리할 기술명 리스트 결정
        tech_list = raw_list if raw_list else self._parse_tech_from_text(raw_text)
        
        normalized_techs = []
        
        for tech_name in tech_list:
            if not tech_name or len(tech_name.strip()) < 2:
                continue
                
            normalized_name = self._normalize_tech_name(tech_name)
            
            # 매핑 테이블에서 찾기
            if normalized_name in self.reverse_mapping:
                tech_info = self.reverse_mapping[normalized_name]
                
                # 맥락 추론
                context = self._infer_context(tech_name, full_job_text)
                
                normalized_tech = {
                    "tech": tech_info["tech"],
                    "category": tech_info["category"],
                    "confidence": "high",  # 매핑 테이블에 있으면 높은 신뢰도
                    "context": context
                }
                
                normalized_techs.append(normalized_tech)
            
            else:
                # 매핑되지 않은 기술은 추정으로 분류
                category = self._guess_category(tech_name)
                context = self._infer_context(tech_name, full_job_text)
                
                normalized_tech = {
                    "tech": tech_name.lower().replace(" ", "_").replace(".", ""),
                    "category": category,
                    "confidence": "low",  # 추정이므로 낮은 신뢰도
                    "context": context
                }
                
                normalized_techs.append(normalized_tech)
        
        return {
            "raw_text": raw_text,
            "raw_list": raw_list,
            "normalized": normalized_techs
        }
    
    def _parse_tech_from_text(self, text: str) -> List[str]:
        """텍스트에서 기술명 파싱"""
        if not text:
            return []
        
        # 다양한 구분자로 분리
        separators = [',', '/', '·', '•', '\n', '|', ';']
        tech_list = [text]
        
        for sep in separators:
            new_list = []
            for item in tech_list:
                new_list.extend([t.strip() for t in item.split(sep) if t.strip()])
            tech_list = new_list
        
        # 너무 짧거나 긴 항목 제거
        filtered_list = []
        for tech in tech_list:
            if 2 <= len(tech) <= 30:  # 적절한 길이의 기술명만
                filtered_list.append(tech)
        
        return filtered_list
    
    def _guess_category(self, tech_name: str) -> str:
        """알려지지 않은 기술의 카테고리 추정"""
        tech_lower = tech_name.lower()
        
        # 간단한 휴리스틱으로 카테고리 추정
        if any(word in tech_lower for word in ['db', 'database', 'sql']):
            return "database"
        elif any(word in tech_lower for word in ['cloud', 'aws', 'azure', 'gcp']):
            return "cloud" 
        elif any(word in tech_lower for word in ['.js', 'script', 'lang']):
            return "language"
        elif any(word in tech_lower for word in ['framework', 'lib', 'library']):
            return "framework"
        else:
            return "tool"  # 기본값

# 전역 인스턴스 (싱글톤 패턴)
_tech_normalizer = None

def get_tech_normalizer():
    """기술스택 정규화기 인스턴스 반환"""
    global _tech_normalizer
    if _tech_normalizer is None:
        _tech_normalizer = TechStackNormalizer()
    return _tech_normalizer

def normalize_tech_stack_data(raw_text: str, raw_list: List[str], 
                             full_job_text: str = "") -> dict:
    """
    기술스택 데이터 정규화 함수 (3개 플랫폼 공통 사용)
    
    Args:
        raw_text: tech_stack의 raw_text
        raw_list: tech_stack의 raw_list
        full_job_text: 전체 채용공고 텍스트 (맥락 추론용)
        
    Returns:
        normalized 필드가 추가된 tech_stack 딕셔너리
    """
    normalizer = get_tech_normalizer()
    return normalizer.normalize_tech_stack(raw_text, raw_list, full_job_text)