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

from .claude_storage import (
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
