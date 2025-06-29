import json
from typing import Dict, List, Optional
from utils.cloud_storage import save_preset, get_preset, load_all_presets, delete_preset

# 기본 프리셋 정의
DEFAULT_PRESETS = {
    "물리 교수님": {
        "subject": "물리학",
        "level": "대학교",
        "personality": {
            "friendliness": 40,
            "humor_level": 20,
            "encouragement": 60,
            "interaction_frequency": 50,
            "explanation_detail": 90,
            "theory_vs_practice": 30,
            "safety_emphasis": 80,
            "adaptability": 70,
            "natural_speech": 50,
            "question_sensitivity": 70,
            "response_speed": 60,
            "vocabulary_level": 85
        },
        "voice_settings": {
            "speed": 0.9,
            "pitch": 1.0,
            "auto_play": True
        },
        "description": "엄격하고 이론 중심의 대학교 물리학 교수님. 체계적이고 정확한 설명을 제공합니다."
    },
    
    "화학 실험 조교": {
        "subject": "화학",
        "level": "고등학교",
        "personality": {
            "friendliness": 80,
            "humor_level": 50,
            "encouragement": 85,
            "interaction_frequency": 75,
            "explanation_detail": 70,
            "theory_vs_practice": 75,
            "safety_emphasis": 95,
            "adaptability": 80,
            "natural_speech": 70,
            "question_sensitivity": 80,
            "response_speed": 70,
            "vocabulary_level": 60
        },
        "voice_settings": {
            "speed": 1.1,
            "pitch": 1.1,
            "auto_play": True
        },
        "description": "친근하고 안전을 중시하는 화학 실험 조교님. 실험 중심의 수업을 진행합니다."
    },
    
    "친근한 수학 선생님": {
        "subject": "수학",
        "level": "중학교",
        "personality": {
            "friendliness": 90,
            "humor_level": 70,
            "encouragement": 90,
            "interaction_frequency": 85,
            "explanation_detail": 60,
            "theory_vs_practice": 50,
            "safety_emphasis": 50,
            "adaptability": 85,
            "natural_speech": 80,
            "question_sensitivity": 85,
            "response_speed": 75,
            "vocabulary_level": 30
        },
        "voice_settings": {
            "speed": 1.0,
            "pitch": 1.2,
            "auto_play": True
        },
        "description": "매우 친근하고 유머가 있는 중학교 수학 선생님. 학생들을 격려하며 쉽게 설명합니다."
    },
    
    "생물학 박사": {
        "subject": "생물학",
        "level": "대학원",
        "personality": {
            "friendliness": 60,
            "humor_level": 40,
            "encouragement": 70,
            "interaction_frequency": 60,
            "explanation_detail": 95,
            "theory_vs_practice": 40,
            "safety_emphasis": 85,
            "adaptability": 75,
            "natural_speech": 60,
            "question_sensitivity": 75,
            "response_speed": 50,
            "vocabulary_level": 90
        },
        "voice_settings": {
            "speed": 0.8,
            "pitch": 0.9,
            "auto_play": True
        },
        "description": "전문적이고 상세한 설명을 제공하는 생물학 박사님. 연구 중심의 깊이 있는 수업을 진행합니다."
    },
    
    "공학 멘토": {
        "subject": "공학",
        "level": "대학교",
        "personality": {
            "friendliness": 70,
            "humor_level": 60,
            "encouragement": 80,
            "interaction_frequency": 70,
            "explanation_detail": 80,
            "theory_vs_practice": 80,
            "safety_emphasis": 90,
            "adaptability": 80,
            "natural_speech": 75,
            "question_sensitivity": 75,
            "response_speed": 70,
            "vocabulary_level": 75
        },
        "voice_settings": {
            "speed": 1.0,
            "pitch": 1.0,
            "auto_play": True
        },
        "description": "실용적이고 현실적인 공학 멘토님. 이론과 실습을 균형있게 가르칩니다."
    }
}

def load_preset(preset_name: str) -> Optional[Dict]:
    """프리셋 로드 (기본 프리셋 + 사용자 프리셋)"""
    # 먼저 기본 프리셋에서 찾기
    if preset_name in DEFAULT_PRESETS:
        return DEFAULT_PRESETS[preset_name].copy()
    
    # 사용자 프리셋에서 찾기
    return get_preset(preset_name)

def get_all_preset_names() -> List[str]:
    """모든 프리셋 이름 목록 조회"""
    preset_names = list(DEFAULT_PRESETS.keys())
    user_presets = load_all_presets()
    preset_names.extend(user_presets.keys())
    
    return sorted(list(set(preset_names)))

def get_presets_by_category() -> Dict[str, List[str]]:
    """카테고리별 프리셋 분류"""
    categories = {
        "기본 프리셋": list(DEFAULT_PRESETS.keys()),
        "사용자 프리셋": list(load_all_presets().keys())
    }
    
    return categories

def save_user_preset(name: str, config: Dict, description: str = "") -> bool:
    """사용자 프리셋 저장"""
    preset_config = {
        **config,
        "description": description,
        "is_user_preset": True
    }
    
    return save_preset(name, preset_config)

def delete_user_preset(preset_name: str) -> bool:
    """사용자 프리셋 삭제 (기본 프리셋은 삭제 불가)"""
    if preset_name in DEFAULT_PRESETS:
        return False  # 기본 프리셋은 삭제 불가
    
    return delete_preset(preset_name)

def is_default_preset(preset_name: str) -> bool:
    """기본 프리셋인지 확인"""
    return preset_name in DEFAULT_PRESETS

def export_preset(preset_name: str) -> Optional[str]:
    """프리셋을 JSON 문자열로 내보내기"""
    preset = load_preset(preset_name)
    if preset:
        export_data = {
            "preset_name": preset_name,
            "preset_config": preset,
            "export_version": "1.0"
        }
        return json.dumps(export_data, ensure_ascii=False, indent=2)
    return None

def import_preset(preset_json: str) -> tuple[bool, str]:
    """JSON 문자열에서 프리셋 가져오기"""
    try:
        data = json.loads(preset_json)
        
        # 데이터 검증
        if "preset_name" not in data or "preset_config" not in data:
            return False, "잘못된 프리셋 파일 형식입니다."
        
        preset_name = data["preset_name"]
        preset_config = data["preset_config"]
        
        # 필수 필드 검증
        required_fields = ["subject", "level", "personality"]
        for field in required_fields:
            if field not in preset_config:
                return False, f"필수 필드 '{field}'가 누락되었습니다."
        
        # 프리셋 저장
        if save_user_preset(preset_name, preset_config):
            return True, f"프리셋 '{preset_name}'이 성공적으로 가져와졌습니다."
        else:
            return False, "프리셋 저장에 실패했습니다."
            
    except json.JSONDecodeError:
        return False, "잘못된 JSON 형식입니다."
    except Exception as e:
        return False, f"프리셋 가져오기 실패: {str(e)}"

def get_preset_suggestions(subject: str = "", level: str = "") -> List[str]:
    """과목과 수준에 따른 프리셋 추천"""
    suggestions = []
    
    all_presets = {**DEFAULT_PRESETS, **load_all_presets()}
    
    for name, preset in all_presets.items():
        match_score = 0
        
        # 과목 일치
        if subject and preset.get("subject", "").lower() == subject.lower():
            match_score += 2
        
        # 수준 일치
        if level and preset.get("level", "").lower() == level.lower():
            match_score += 2
        
        # 부분 일치
        if subject and subject.lower() in preset.get("subject", "").lower():
            match_score += 1
        
        if level and level.lower() in preset.get("level", "").lower():
            match_score += 1
        
        if match_score > 0:
            suggestions.append((name, match_score))
    
    # 점수 순으로 정렬하여 이름만 반환
    suggestions.sort(key=lambda x: x[1], reverse=True)
    return [name for name, score in suggestions[:5]]

def create_custom_preset_from_config(teacher_config: Dict, preset_name: str) -> bool:
    """AI 튜터 설정에서 프리셋 생성"""
    preset_config = {
        "subject": teacher_config.get("subject"),
        "level": teacher_config.get("level"),
        "personality": teacher_config.get("personality", {}),
        "voice_settings": teacher_config.get("voice_settings", {}),
        "description": f"{teacher_config.get('name', '익명')}님의 설정을 기반으로 생성된 프리셋"
    }
    
    return save_user_preset(preset_name, preset_config)

def apply_preset_to_config(preset_name: str, base_config: Dict) -> Dict:
    """프리셋을 기존 설정에 적용"""
    preset = load_preset(preset_name)
    if not preset:
        return base_config
    
    # 프리셋의 설정을 기본 설정에 병합
    updated_config = base_config.copy()
    
    for key in ["subject", "level", "personality", "voice_settings"]:
        if key in preset:
            updated_config[key] = preset[key]
    
    return updated_config

def get_personality_profile(preset_name: str) -> Dict:
    """프리셋의 성격 프로필 분석"""
    preset = load_preset(preset_name)
    if not preset or "personality" not in preset:
        return {}
    
    personality = preset["personality"]
    
    # 성격 특성 분석
    profile = {
        "teaching_style": "이론 중심" if personality.get("theory_vs_practice", 50) < 50 else "실습 중심",
        "interaction_level": "일방적" if personality.get("interaction_frequency", 50) < 50 else "상호작용적",
        "difficulty_level": "기초" if personality.get("vocabulary_level", 50) < 50 else "고급",
        "communication_style": "격식적" if personality.get("friendliness", 50) < 50 else "친근함",
        "humor_tendency": "진지함" if personality.get("humor_level", 50) < 30 else "유머러스"
    }
    
    return profile

def validate_preset(preset_config: Dict) -> tuple[bool, List[str]]:
    """프리셋 설정 유효성 검사"""
    errors = []
    
    # 필수 필드 검사
    required_fields = ["subject", "level", "personality"]
    for field in required_fields:
        if field not in preset_config:
            errors.append(f"필수 필드 '{field}'가 누락되었습니다.")
    
    # personality 필드 검사
    if "personality" in preset_config:
        personality = preset_config["personality"]
        required_personality_fields = [
            "friendliness", "humor_level", "encouragement", "explanation_detail"
        ]
        
        for field in required_personality_fields:
            if field not in personality:
                errors.append(f"성격 설정 '{field}'가 누락되었습니다.")
            elif not isinstance(personality[field], (int, float)) or not (0 <= personality[field] <= 100):
                errors.append(f"성격 설정 '{field}'는 0-100 사이의 숫자여야 합니다.")
    
    # voice_settings 검사
    if "voice_settings" in preset_config:
        voice = preset_config["voice_settings"]
        if "speed" in voice and not isinstance(voice["speed"], (int, float)):
            errors.append("음성 속도는 숫자여야 합니다.")
        if "pitch" in voice and not isinstance(voice["pitch"], (int, float)):
            errors.append("음성 높이는 숫자여야 합니다.")
    
    return len(errors) == 0, errors
