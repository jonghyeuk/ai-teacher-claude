import streamlit as st
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import tempfile

# 로컬 저장소 파일 경로
LOCAL_STORAGE_DIR = "data"
TEACHERS_FILE = os.path.join(LOCAL_STORAGE_DIR, "teachers.json")
PRESETS_FILE = os.path.join(LOCAL_STORAGE_DIR, "presets.json")

def ensure_data_directory():
    """데이터 디렉토리 생성"""
    if not os.path.exists(LOCAL_STORAGE_DIR):
        os.makedirs(LOCAL_STORAGE_DIR)

def save_ai_teacher(teacher_config: Dict) -> bool:
    """AI 튜터 설정을 저장"""
    try:
        ensure_data_directory()
        
        # 기존 데이터 로드
        teachers = load_all_teachers()
        
        # 새 튜터 추가
        teachers.append(teacher_config)
        
        # 최신 20개만 유지 (저장 공간 관리)
        teachers = teachers[-20:]
        
        # 파일에 저장
        with open(TEACHERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(teachers, f, ensure_ascii=False, indent=2)
        
        return True
        
    except Exception as e:
        st.error(f"AI 튜터 저장 실패: {str(e)}")
        return False

def load_all_teachers() -> List[Dict]:
    """모든 AI 튜터 설정 로드"""
    try:
        if os.path.exists(TEACHERS_FILE):
            with open(TEACHERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        st.warning(f"AI 튜터 로드 실패: {str(e)}")
        return []

def load_recent_teachers(limit: int = 10) -> List[Dict]:
    """최근 생성된 AI 튜터들 로드"""
    teachers = load_all_teachers()
    
    # 최신순으로 정렬
    teachers.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return teachers[:limit]

def get_teacher_by_id(teacher_id: str) -> Optional[Dict]:
    """ID로 특정 AI 튜터 조회"""
    teachers = load_all_teachers()
    
    for teacher in teachers:
        if teacher.get('id') == teacher_id:
            return teacher
    
    return None

def delete_teacher(teacher_id: str) -> bool:
    """AI 튜터 삭제"""
    try:
        teachers = load_all_teachers()
        
        # 해당 ID의 튜터 제거
        teachers = [t for t in teachers if t.get('id') != teacher_id]
        
        # 파일에 저장
        with open(TEACHERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(teachers, f, ensure_ascii=False, indent=2)
        
        return True
        
    except Exception as e:
        st.error(f"AI 튜터 삭제 실패: {str(e)}")
        return False

def save_preset(preset_name: str, preset_config: Dict) -> bool:
    """프리셋 저장"""
    try:
        ensure_data_directory()
        
        # 기존 프리셋 로드
        presets = load_all_presets()
        
        # 새 프리셋 추가/업데이트
        presets[preset_name] = {
            **preset_config,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        # 파일에 저장
        with open(PRESETS_FILE, 'w', encoding='utf-8') as f:
            json.dump(presets, f, ensure_ascii=False, indent=2)
        
        return True
        
    except Exception as e:
        st.error(f"프리셋 저장 실패: {str(e)}")
        return False

def load_all_presets() -> Dict:
    """모든 프리셋 로드"""
    try:
        if os.path.exists(PRESETS_FILE):
            with open(PRESETS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        st.warning(f"프리셋 로드 실패: {str(e)}")
        return {}

def get_preset(preset_name: str) -> Optional[Dict]:
    """특정 프리셋 조회"""
    presets = load_all_presets()
    return presets.get(preset_name)

def delete_preset(preset_name: str) -> bool:
    """프리셋 삭제"""
    try:
        presets = load_all_presets()
        
        if preset_name in presets:
            del presets[preset_name]
            
            # 파일에 저장
            with open(PRESETS_FILE, 'w', encoding='utf-8') as f:
                json.dump(presets, f, ensure_ascii=False, indent=2)
            
            return True
        
        return False
        
    except Exception as e:
        st.error(f"프리셋 삭제 실패: {str(e)}")
        return False

def export_teacher_config(teacher_id: str) -> Optional[str]:
    """AI 튜터 설정을 JSON 문자열로 내보내기"""
    teacher = get_teacher_by_id(teacher_id)
    if teacher:
        return json.dumps(teacher, ensure_ascii=False, indent=2)
    return None

def import_teacher_config(config_json: str) -> bool:
    """JSON 문자열에서 AI 튜터 설정 가져오기"""
    try:
        config = json.loads(config_json)
        
        # 필수 필드 검증
        required_fields = ['name', 'subject', 'level', 'personality']
        for field in required_fields:
            if field not in config:
                st.error(f"필수 필드 '{field}'가 누락되었습니다.")
                return False
        
        # 새 ID 생성 (중복 방지)
        import uuid
        config['id'] = str(uuid.uuid4())
        config['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # 저장
        return save_ai_teacher(config)
        
    except json.JSONDecodeError:
        st.error("잘못된 JSON 형식입니다.")
        return False
    except Exception as e:
        st.error(f"설정 가져오기 실패: {str(e)}")
        return False

def backup_all_data() -> str:
    """모든 데이터를 백업"""
    try:
        backup_data = {
            'teachers': load_all_teachers(),
            'presets': load_all_presets(),
            'backup_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return json.dumps(backup_data, ensure_ascii=False, indent=2)
        
    except Exception as e:
        st.error(f"백업 실패: {str(e)}")
        return ""

def restore_from_backup(backup_json: str) -> bool:
    """백업에서 데이터 복원"""
    try:
        backup_data = json.loads(backup_json)
        
        # 백업 데이터 검증
        if 'teachers' not in backup_data or 'presets' not in backup_data:
            st.error("잘못된 백업 파일 형식입니다.")
            return False
        
        ensure_data_directory()
        
        # 데이터 복원
        with open(TEACHERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(backup_data['teachers'], f, ensure_ascii=False, indent=2)
        
        with open(PRESETS_FILE, 'w', encoding='utf-8') as f:
            json.dump(backup_data['presets'], f, ensure_ascii=False, indent=2)
        
        return True
        
    except json.JSONDecodeError:
        st.error("잘못된 백업 파일 형식입니다.")
        return False
    except Exception as e:
        st.error(f"복원 실패: {str(e)}")
        return False

def get_storage_stats() -> Dict:
    """저장소 사용 통계"""
    try:
        teachers = load_all_teachers()
        presets = load_all_presets()
        
        # 파일 크기 계산
        teachers_size = 0
        presets_size = 0
        
        if os.path.exists(TEACHERS_FILE):
            teachers_size = os.path.getsize(TEACHERS_FILE)
        
        if os.path.exists(PRESETS_FILE):
            presets_size = os.path.getsize(PRESETS_FILE)
        
        return {
            'teachers_count': len(teachers),
            'presets_count': len(presets),
            'teachers_size_kb': round(teachers_size / 1024, 2),
            'presets_size_kb': round(presets_size / 1024, 2),
            'total_size_kb': round((teachers_size + presets_size) / 1024, 2)
        }
        
    except Exception as e:
        st.error(f"통계 조회 실패: {str(e)}")
        return {}

def clean_old_data(days: int = 30) -> int:
    """오래된 데이터 정리"""
    try:
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        teachers = load_all_teachers()
        
        # 오래된 튜터 제거
        active_teachers = []
        removed_count = 0
        
        for teacher in teachers:
            created_str = teacher.get('created_at', '')
            try:
                created_date = datetime.strptime(created_str, "%Y-%m-%d %H:%M")
                if created_date > cutoff_date:
                    active_teachers.append(teacher)
                else:
                    removed_count += 1
            except:
                # 날짜 파싱 실패 시 유지
                active_teachers.append(teacher)
        
        # 파일에 저장
        with open(TEACHERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(active_teachers, f, ensure_ascii=False, indent=2)
        
        return removed_count
        
    except Exception as e:
        st.error(f"데이터 정리 실패: {str(e)}")
        return 0

# Streamlit Cloud 호환성을 위한 대체 저장소
def use_session_storage():
    """세션 스토리지 사용 (파일 시스템 접근 불가 시)"""
    if 'teachers_storage' not in st.session_state:
        st.session_state.teachers_storage = []
    
    if 'presets_storage' not in st.session_state:
        st.session_state.presets_storage = {}

def session_save_teacher(teacher_config: Dict):
    """세션에 AI 튜터 저장"""
    use_session_storage()
    st.session_state.teachers_storage.append(teacher_config)
    
    # 최신 20개만 유지
    st.session_state.teachers_storage = st.session_state.teachers_storage[-20:]

def session_load_teachers() -> List[Dict]:
    """세션에서 AI 튜터 로드"""
    use_session_storage()
    return st.session_state.teachers_storage

# 환경에 따른 자동 선택
def get_storage_method():
    """사용 가능한 저장 방법 감지"""
    try:
        # 파일 시스템 접근 테스트
        ensure_data_directory()
        test_file = os.path.join(LOCAL_STORAGE_DIR, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        return "file"
    except:
        # 파일 시스템 접근 불가 시 세션 사용
        return "session"
