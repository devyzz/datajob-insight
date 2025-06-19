"""
채용 포지션 정규화 유틸리티
- 원티드, 사람인, 잡코리아 공통 사용
- 저장 전 정규화로 일관성 있는 데이터 확보
"""

import re
from typing import Dict, List, Optional
from enum import Enum

class ConfidenceLevel(Enum):
    HIGH = "high"      # 90%+ 확신
    MEDIUM = "medium"  # 70-90% 확신  
    LOW = "low"        # 50-70% 확신

class PositionNormalizer:
    """포지션 정규화 엔진 - 3개 플랫폼 공통 사용"""
    
    def __init__(self):
        # 포지션 분류 체계 - 실제 채용시장 기반
        self.taxonomy = {
            "SOFTWARE_DEVELOPMENT": {
                "label": "소프트웨어 개발",
                "subcategories": {
                    "BACKEND": {
                        "label": "백엔드 개발",
                        "keywords": {
                            # 원티드 스타일
                            "node.js 개발자": ConfidenceLevel.HIGH,
                            "서버 개발자": ConfidenceLevel.HIGH,
                            "백엔드 개발자": ConfidenceLevel.HIGH,
                            "java 개발자": ConfidenceLevel.MEDIUM,
                            "python 개발자": ConfidenceLevel.MEDIUM,
                            "php 개발자": ConfidenceLevel.MEDIUM,
                            ".net 개발자": ConfidenceLevel.MEDIUM,
                            
                            # 사람인 스타일
                            "백엔드/서버개발": ConfidenceLevel.HIGH,
                            "서버개발": ConfidenceLevel.HIGH,
                            
                            # 잡코리아 스타일
                            "백엔드개발자": ConfidenceLevel.HIGH,
                        }
                    },
                    "FRONTEND": {
                        "label": "프론트엔드 개발",
                        "keywords": {
                            "프론트엔드 개발자": ConfidenceLevel.HIGH,
                            "프론트엔드": ConfidenceLevel.HIGH,
                            "프론트엔드개발자": ConfidenceLevel.HIGH,
                            "웹개발": ConfidenceLevel.MEDIUM,
                            "웹개발자": ConfidenceLevel.MEDIUM,
                            "웹 개발자": ConfidenceLevel.MEDIUM,
                            "웹퍼블리셔": ConfidenceLevel.MEDIUM,
                            "웹 퍼블리셔": ConfidenceLevel.MEDIUM,
                        }
                    },
                    "MOBILE": {
                        "label": "모바일 개발", 
                        "keywords": {
                            "안드로이드 개발자": ConfidenceLevel.HIGH,
                            "ios 개발자": ConfidenceLevel.HIGH,
                            "앱개발": ConfidenceLevel.HIGH,
                            "앱개발자": ConfidenceLevel.HIGH,
                            "모바일 개발자": ConfidenceLevel.HIGH,
                        }
                    },
                    "FULLSTACK": {
                        "label": "풀스택 개발",
                        "keywords": {
                            "풀스택": ConfidenceLevel.HIGH,
                            "풀스택 개발자": ConfidenceLevel.HIGH,
                            "소프트웨어 엔지니어": ConfidenceLevel.MEDIUM,
                        }
                    }
                }
            },
            "DATA_SCIENCE": {
                "label": "데이터 사이언스",
                "subcategories": {
                    "DATA_ENGINEER": {
                        "label": "데이터 엔지니어",
                        "keywords": {
                            "데이터 엔지니어": ConfidenceLevel.HIGH,
                            "데이터엔지니어": ConfidenceLevel.HIGH,
                            "빅데이터 엔지니어": ConfidenceLevel.HIGH,
                            "mlops엔지니어": ConfidenceLevel.HIGH,
                        }
                    },
                    "DATA_SCIENTIST": {
                        "label": "데이터 사이언티스트",
                        "keywords": {
                            "데이터 사이언티스트": ConfidenceLevel.HIGH,
                            "데이터사이언티스트": ConfidenceLevel.HIGH,
                        }
                    },
                    "DATA_ANALYST": {
                        "label": "데이터 분석가",
                        "keywords": {
                            "데이터분석가": ConfidenceLevel.HIGH,
                            "데이터 분석가": ConfidenceLevel.HIGH,
                            "bi 엔지니어": ConfidenceLevel.HIGH,
                        }
                    }
                }
            },
            "AI_ML": {
                "label": "AI/머신러닝",
                "subcategories": {
                    "AI_ENGINEER": {
                        "label": "AI 엔지니어",
                        "keywords": {
                            "ai/ml엔지니어": ConfidenceLevel.HIGH,
                            "ai 엔지니어": ConfidenceLevel.HIGH,
                            "머신러닝 엔지니어": ConfidenceLevel.HIGH,
                            "ai/ml연구원": ConfidenceLevel.HIGH,
                        }
                    }
                }
            },
            "INFRASTRUCTURE": {
                "label": "인프라/시스템",
                "subcategories": {
                    "DEVOPS": {
                        "label": "DevOps",
                        "keywords": {
                            "devops": ConfidenceLevel.HIGH,
                            "devops / 시스템 관리자": ConfidenceLevel.HIGH,
                            "클라우드엔지니어": ConfidenceLevel.HIGH,
                        }
                    },
                    "SYSTEM": {
                        "label": "시스템 엔지니어",
                        "keywords": {
                            "시스템엔지니어": ConfidenceLevel.HIGH,
                            "se(시스템엔지니어)": ConfidenceLevel.HIGH,
                            "시스템,네트워크 관리자": ConfidenceLevel.MEDIUM,
                        }
                    },
                    "DATABASE": {
                        "label": "데이터베이스",
                        "keywords": {
                            "dba": ConfidenceLevel.HIGH,
                        }
                    }
                }
            },
            "SECURITY": {
                "label": "보안",
                "subcategories": {
                    "SECURITY_ENGINEER": {
                        "label": "보안 엔지니어",
                        "keywords": {
                            "보안엔지니어": ConfidenceLevel.HIGH,
                            "정보보안": ConfidenceLevel.HIGH,
                            "보안관제": ConfidenceLevel.HIGH,
                        }
                    }
                }
            },
            "QA_TESTING": {
                "label": "QA/테스팅",
                "subcategories": {
                    "QA": {
                        "label": "QA 엔지니어",
                        "keywords": {
                            "qa": ConfidenceLevel.HIGH,
                            "qa/테스터": ConfidenceLevel.HIGH,
                            "qa,테스트 엔지니어": ConfidenceLevel.HIGH,
                        }
                    }
                }
            }
        }
        
        # 키워드 맵 구축 (성능 최적화)
        self.keyword_map = self._build_keyword_map()
        
    def _build_keyword_map(self) -> Dict[str, Dict]:
        """키워드를 정규화해서 매핑 테이블 생성"""
        keyword_map = {}
        
        for primary_key, primary_value in self.taxonomy.items():
            for secondary_key, secondary_value in primary_value['subcategories'].items():
                for keyword, confidence in secondary_value['keywords'].items():
                    # 키워드 정규화
                    normalized_keyword = self._normalize_text(keyword)
                    
                    keyword_map[normalized_keyword] = {
                        'primary_category': primary_key,
                        'secondary_category': secondary_key,
                        'primary_label': primary_value['label'],
                        'secondary_label': secondary_value['label'],
                        'confidence': confidence.value,
                        'is_data_role': primary_key in ['DATA_SCIENCE', 'AI_ML']
                    }
        
        return keyword_map
    
    def _normalize_text(self, text: str) -> str:
        """텍스트 정규화 - 매칭 정확도 향상"""
        if not text:
            return ""
        
        # 소문자 변환
        normalized = text.lower()
        
        # 괄호와 내용 제거 (예: "백엔드/서버개발(2,127)" -> "백엔드/서버개발")
        normalized = re.sub(r'\([^)]*\)', '', normalized)
        
        # 특수문자 제거 및 공백 정리
        normalized = re.sub(r'[/,\-\s]+', '', normalized)
        
        return normalized.strip()
    
    def normalize_position(self, raw_text: str, raw_list: List[str]) -> dict:
        """
        포지션 정보 정규화
        
        Args:
            raw_text: 원본 텍스트
            raw_list: 원본 리스트
            
        Returns:
            정규화된 포지션 딕셔너리
        """
        # raw_list 우선 사용, 없으면 raw_text 사용
        search_texts = raw_list if raw_list else [raw_text] if raw_text else []
        
        best_match = None
        best_score = 0
        
        # 각 텍스트에 대해 매칭 시도
        for text in search_texts:
            if not text:
                continue
                
            normalized_text = self._normalize_text(text)
            
            # 정확 매칭 우선
            if normalized_text in self.keyword_map:
                match_info = self.keyword_map[normalized_text]
                match_info['match_type'] = 'exact'
                match_info['score'] = 1.0
                best_match = match_info
                break
            
            # 부분 매칭 시도
            for keyword, info in self.keyword_map.items():
                if keyword in normalized_text or normalized_text in keyword:
                    score = min(len(keyword), len(normalized_text)) / max(len(keyword), len(normalized_text))
                    if score > best_score and score >= 0.7:  # 70% 이상만 인정
                        info['match_type'] = 'partial'
                        info['score'] = score
                        best_match = info
                        best_score = score
        
        # 매칭 결과가 있으면 정규화된 데이터 반환
        if best_match:
            return {
                "raw_text": raw_text,
                "raw_list": raw_list,
                "normalized": {
                    "primary_category": best_match['primary_category'],
                    "secondary_category": best_match['secondary_category'],
                    "primary_label": best_match['primary_label'],
                    "secondary_label": best_match['secondary_label'],
                    "confidence": best_match['confidence'],
                    "is_data_role": best_match['is_data_role']
                }
            }
        
        # 매칭 실패시 기본값
        return {
            "raw_text": raw_text,
            "raw_list": raw_list,
            "normalized": {
                "primary_category": "UNKNOWN",
                "secondary_category": "UNKNOWN",
                "primary_label": "미분류",
                "secondary_label": "미분류",
                "confidence": "low",
                "is_data_role": False
            }
        }

# 전역 인스턴스 (싱글톤 패턴)
_position_normalizer = None

def get_position_normalizer():
    """포지션 정규화기 인스턴스 반환 (싱글톤)"""
    global _position_normalizer
    if _position_normalizer is None:
        _position_normalizer = PositionNormalizer()
    return _position_normalizer

def normalize_position_data(raw_text: str, raw_list: List[str]) -> dict:
    """
    포지션 데이터 정규화 함수 (3개 플랫폼 공통 사용)
    
    Args:
        raw_text: position의 raw_text
        raw_list: position의 raw_list
        
    Returns:
        normalized 필드가 추가된 position 딕셔너리
    """
    normalizer = get_position_normalizer()
    return normalizer.normalize_position(raw_text, raw_list)