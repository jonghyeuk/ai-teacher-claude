"""
AI 튜터 팩토리 유틸리티 패키지

이 패키지는 AI 튜터 시스템의 핵심 기능들을 제공합니다:
- Claude API 연동
- 음성 처리 (TTS/STT)
- 클라우드 저장소
- 프리셋 관리

작성자: AI Education Team
버전: 1.0.0
"""

from .claude_api import (
    get_claude_client,
    generate_system_prompt,
    get_claude_response,
    generate_lesson_content,
    check_api_status
)

from .voice_handler import (
    text_to_speech,
    speech_to_text,
    create_audio_player,
    get_available_voices,
    test_voice_settings
)

from .cloude_storage import (
    save_ai_teacher,
    load_all_teachers,
    load_recent_teachers,
    get_teacher_by_id,
    delete_teacher,
    backup_all_data,
    restore_from_backup,
    get_storage_stats
)

from .preset_manager import (
    load_preset,
    get_all_preset_names,
    save_user_preset,
    delete_user_preset,
    is_default_preset,
    export_preset,
    import_preset,
    get_preset_suggestions,
    DEFAULT_PRESETS
)

# 패키지 정보
__version__ = "1.0.0"
__author__ = "AI Education Team"
__email__ = "dev@ai-tutor-factory.com"

# 지원되는 기능 확인
def check_system_capabilities():
    """시스템에서 지원 가능한 기능들을 확인합니다."""
    capabilities = {
        "claude_api": False,
        "google_tts": False,
        "file_storage": False,
        "browser_tts": False
    }
    
    try:
        # Claude API 확인
        if check_api_status():
            capabilities["claude_api"] = True
    except:
        pass
    
    try:
        # Google Cloud TTS 확인
        from google.cloud import texttospeech
        capabilities["google_tts"] = True
    except:
        pass
    
    try:
        # 파일 저장소 확인
        import os
        capabilities["file_storage"] = True
    except:
        pass
    
    # 브라우저 TTS는 항상 사용 가능하다고 가정
    capabilities["browser_tts"] = True
    
    return capabilities

def get_package_info():
    """패키지 정보를 반환합니다."""
    return {
        "name": "AI 튜터 팩토리 Utils",
        "version": __version__,
        "author": __author__,
        "email": __email__,
        "capabilities": check_system_capabilities()
    }

# 초기화 함수
def initialize_utils():
    """유틸리티 패키지를 초기화합니다."""
    print(f"AI 튜터 팩토리 Utils v{__version__} 초기화 중...")
    
    capabilities = check_system_capabilities()
    
    if capabilities["claude_api"]:
        print("✅ Claude API 연결 가능")
    else:
        print("❌ Claude API 연결 불가 - API 키를 확인하세요")
    
    if capabilities["google_tts"]:
        print("✅ Google Cloud TTS 사용 가능")
    else:
        print("⚠️ Google Cloud TTS 불가 - 브라우저 TTS 사용")
    
    if capabilities["file_storage"]:
        print("✅ 로컬 파일 저장 가능")
    else:
        print("⚠️ 로컬 파일 저장 불가 - 세션 저장 사용")
    
    print("🎓 AI 튜터 팩토리 준비 완료!")
    
    return capabilities

# 에러 핸들링을 위한 커스텀 예외들
class AITutorError(Exception):
    """AI 튜터 관련 기본 예외"""
    pass

class ClaudeAPIError(AITutorError):
    """Claude API 관련 예외"""
    pass

class VoiceProcessingError(AITutorError):
    """음성 처리 관련 예외"""
    pass

class StorageError(AITutorError):
    """저장소 관련 예외"""
    pass

class PresetError(AITutorError):
    """프리셋 관련 예외"""
    pass

# 유틸리티 함수들
def validate_teacher_config(config):
    """AI 튜터 설정의 유효성을 검사합니다."""
    required_fields = ["name", "subject", "level", "personality"]
    
    for field in required_fields:
        if field not in config:
            raise ValueError(f"필수 필드 '{field}'가 누락되었습니다.")
    
    # 성격 설정 검증
    personality = config["personality"]
    for key, value in personality.items():
        if not isinstance(value, (int, float)) or not (0 <= value <= 100):
            raise ValueError(f"성격 설정 '{key}'는 0-100 사이의 숫자여야 합니다.")
    
    return True

def sanitize_teacher_name(name):
    """AI 튜터 이름을 안전한 문자열로 변환합니다."""
    import re
    # 특수문자 제거하고 공백을 언더스코어로 변경
    sanitized = re.sub(r'[^\w\s-]', '', name)
    sanitized = re.sub(r'[-\s]+', '_', sanitized)
    return sanitized.strip('_')

def format_file_size(size_bytes):
    """바이트 크기를 읽기 쉬운 형태로 변환합니다."""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def get_supported_file_types():
    """지원되는 파일 형식 목록을 반환합니다."""
    return {
        "documents": [".pdf", ".doc", ".docx", ".txt", ".md"],
        "audio": [".mp3", ".wav", ".ogg"],
        "images": [".jpg", ".jpeg", ".png", ".gif"]
    }

# 로깅 설정
import logging

def setup_logger(name="ai_tutor_utils", level=logging.INFO):
    """로거를 설정합니다."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

# 기본 로거 생성
logger = setup_logger()

# 모듈이 임포트될 때 자동으로 정보 출력 (선택사항)
if __name__ != "__main__":
    logger.info(f"AI 튜터 팩토리 Utils v{__version__} 로드됨")

# 모든 공개 함수와 클래스를 __all__에 정의
__all__ = [
    # Claude API
    "get_claude_client",
    "generate_system_prompt", 
    "get_claude_response",
    "generate_lesson_content",
    "check_api_status",
    
    # Voice Handler
    "text_to_speech",
    "speech_to_text",
    "create_audio_player",
    "get_available_voices",
    "test_voice_settings",
    
    # Cloud Storage
    "save_ai_teacher",
    "load_all_teachers",
    "load_recent_teachers",
    "get_teacher_by_id",
    "delete_teacher",
    "backup_all_data",
    "restore_from_backup",
    "get_storage_stats",
    
    # Preset Manager
    "load_preset",
    "get_all_preset_names",
    "save_user_preset",
    "delete_user_preset",
    "is_default_preset",
    "export_preset",
    "import_preset",
    "get_preset_suggestions",
    "DEFAULT_PRESETS",
    
    # Utilities
    "check_system_capabilities",
    "get_package_info",
    "initialize_utils",
    "validate_teacher_config",
    "sanitize_teacher_name",
    "format_file_size",
    "get_supported_file_types",
    "setup_logger",
    
    # Exceptions
    "AITutorError",
    "ClaudeAPIError", 
    "VoiceProcessingError",
    "StorageError",
    "PresetError"
]
