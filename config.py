import os
import streamlit as st
from typing import Dict, Any

# 앱 기본 설정
APP_CONFIG = {
    "name": "AI 튜터 팩토리",
    "version": "1.0.0",
    "description": "맞춤형 AI 선생님 생성 플랫폼",
    "author": "AI Education Team",
    "max_teachers": 100,  # 최대 생성 가능한 AI 튜터 수
    "max_chat_history": 50,  # 최대 채팅 히스토리 보관 수
}

# API 설정
API_CONFIG = {
    "anthropic": {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 2000,
        "temperature": 0.7,
    },
    "google_cloud": {
        "text_to_speech": {
            "language_code": "ko-KR",
            "voice_name": "ko-KR-Standard-A",
            "audio_encoding": "MP3"
        }
    }
}

# UI 설정
UI_CONFIG = {
    "theme": {
        "primary_color": "#667eea",
        "secondary_color": "#764ba2",
        "background_color": "#ffffff",
        "text_color": "#333333"
    },
    "layout": {
        "sidebar_width": 300,
        "chat_max_height": 400,
        "blackboard_min_height": 400
    },
    "animations": {
        "typing_speed": 50,  # ms per character
        "fade_duration": 300,  # ms
    }
}

# 기본 성격 설정 범위
PERSONALITY_RANGES = {
    "friendliness": {"min": 0, "max": 100, "default": 70},
    "humor_level": {"min": 0, "max": 100, "default": 30},
    "encouragement": {"min": 0, "max": 100, "default": 80},
    "interaction_frequency": {"min": 0, "max": 100, "default": 60},
    "explanation_detail": {"min": 0, "max": 100, "default": 70},
    "theory_vs_practice": {"min": 0, "max": 100, "default": 50},
    "safety_emphasis": {"min": 0, "max": 100, "default": 90},
    "adaptability": {"min": 0, "max": 100, "default": 75},
    "natural_speech": {"min": 0, "max": 100, "default": 80},
    "question_sensitivity": {"min": 0, "max": 100, "default": 70},
    "response_speed": {"min": 0, "max": 100, "default": 60},
    "vocabulary_level": {"min": 0, "max": 100, "default": 50}
}

# 음성 설정 범위
VOICE_RANGES = {
    "speed": {"min": 0.5, "max": 2.0, "default": 1.0, "step": 0.1},
    "pitch": {"min": 0.5, "max": 2.0, "default": 1.0, "step": 0.1},
    "volume": {"min": 0.1, "max": 1.0, "default": 0.8, "step": 0.1}
}

# 지원되는 과목 목록
SUBJECTS = [
    "물리학", "화학", "생물학", "수학", "지구과학", 
    "공학", "컴퓨터과학", "의학", "약학", "간호학",
    "기타"
]

# 교육 수준
EDUCATION_LEVELS = [
    "초등학교", "중학교", "고등학교", "대학교", "대학원"
]

# 지원되는 파일 형식
SUPPORTED_FILE_TYPES = {
    "documents": ["pdf", "doc", "docx", "txt", "md"],
    "max_file_size_mb": 10,
    "max_files_per_teacher": 5
}

def get_api_key(service: str) -> str:
    """API 키 조회"""
    key_map = {
        "anthropic": "ANTHROPIC_API_KEY",
        "google_cloud": "GOOGLE_CLOUD_CREDENTIALS",
        "openai": "OPENAI_API_KEY"
    }
    
    env_key = key_map.get(service)
    if not env_key:
        return ""
    
    # 환경 변수에서 먼저 확인
    api_key = os.getenv(env_key)
    
    # Streamlit secrets에서 확인
    if not api_key and hasattr(st, 'secrets'):
        try:
            api_key = st.secrets.get(env_key)
        except:
            pass
    
    return api_key or ""

def is_api_configured(service: str) -> bool:
    """API 설정 여부 확인"""
    return bool(get_api_key(service))

def get_app_config(key: str = None) -> Any:
    """앱 설정 조회"""
    if key:
        return APP_CONFIG.get(key)
    return APP_CONFIG

def get_ui_config(section: str = None, key: str = None) -> Any:
    """UI 설정 조회"""
    if section and key:
        return UI_CONFIG.get(section, {}).get(key)
    elif section:
        return UI_CONFIG.get(section, {})
    return UI_CONFIG

def get_personality_config(personality_type: str = None) -> Any:
    """성격 설정 조회"""
    if personality_type:
        return PERSONALITY_RANGES.get(personality_type, {})
    return PERSONALITY_RANGES

def get_voice_config(voice_setting: str = None) -> Any:
    """음성 설정 조회"""
    if voice_setting:
        return VOICE_RANGES.get(voice_setting, {})
    return VOICE_RANGES

def validate_file_upload(file) -> tuple[bool, str]:
    """파일 업로드 유효성 검사"""
    if not file:
        return False, "파일이 선택되지 않았습니다."
    
    # 파일 확장자 검사
    file_extension = file.name.split('.')[-1].lower()
    if file_extension not in SUPPORTED_FILE_TYPES["documents"]:
        return False, f"지원되지 않는 파일 형식입니다. 지원 형식: {', '.join(SUPPORTED_FILE_TYPES['documents'])}"
    
    # 파일 크기 검사
    if file.size > SUPPORTED_FILE_TYPES["max_file_size_mb"] * 1024 * 1024:
        return False, f"파일 크기가 {SUPPORTED_FILE_TYPES['max_file_size_mb']}MB를 초과합니다."
    
    return True, "유효한 파일입니다."

def get_default_teacher_config() -> Dict:
    """기본 AI 튜터 설정 반환"""
    return {
        "name": "",
        "subject": SUBJECTS[0],
        "level": EDUCATION_LEVELS[2],  # 고등학교
        "personality": {
            key: config["default"] 
            for key, config in PERSONALITY_RANGES.items()
        },
        "voice_settings": {
            key: config["default"] 
            for key, config in VOICE_RANGES.items()
        },
        "uploaded_files": [],
        "use_general_knowledge": True
    }

def load_environment():
    """환경 변수 로드"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # python-dotenv가 설치되지 않은 경우 무시

def check_system_requirements() -> Dict[str, bool]:
    """시스템 요구사항 확인"""
    requirements = {
        "python_version": True,  # Streamlit이 실행되므로 Python은 OK
        "anthropic_api": is_api_configured("anthropic"),
        "google_cloud_api": is_api_configured("google_cloud"),
        "streamlit_version": True,  # 실행 중이므로 OK
    }
    
    try:
        import anthropic
        requirements["anthropic_library"] = True
    except ImportError:
        requirements["anthropic_library"] = False
    
    try:
        from google.cloud import texttospeech
        requirements["google_cloud_library"] = True
    except ImportError:
        requirements["google_cloud_library"] = False
    
    return requirements

def get_system_info() -> Dict:
    """시스템 정보 조회"""
    import sys
    import platform
    
    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "streamlit_version": st.__version__,
        "app_version": APP_CONFIG["version"],
        "requirements_status": check_system_requirements()
    }

# 개발/프로덕션 환경 설정
ENVIRONMENT = os.getenv("STREAMLIT_ENV", "development")
DEBUG = ENVIRONMENT == "development"

if DEBUG:
    # 개발 환경 설정
    APP_CONFIG["debug"] = True
    API_CONFIG["anthropic"]["temperature"] = 0.8
else:
    # 프로덕션 환경 설정
    APP_CONFIG["debug"] = False
    API_CONFIG["anthropic"]["temperature"] = 0.7

# 로깅 설정
LOGGING_CONFIG = {
    "level": "DEBUG" if DEBUG else "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "app.log" if not DEBUG else None
}

def setup_logging():
    """로깅 설정"""
    import logging
    
    level = getattr(logging, LOGGING_CONFIG["level"])
    format_str = LOGGING_CONFIG["format"]
    
    if LOGGING_CONFIG["file"]:
        logging.basicConfig(
            level=level,
            format=format_str,
            filename=LOGGING_CONFIG["file"],
            filemode='a'
        )
    else:
        logging.basicConfig(level=level, format=format_str)
    
    return logging.getLogger(__name__)

# 초기화 함수
def initialize_app():
    """앱 초기화"""
    load_environment()
    
    if DEBUG:
        logger = setup_logging()
        logger.info("AI 튜터 팩토리 앱이 시작되었습니다 (개발 모드)")
    
    return True
