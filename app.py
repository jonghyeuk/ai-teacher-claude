import streamlit as st
import json
import os
from datetime import datetime
import uuid
from utils.preset_manager import PresetManager
from utils.cloud_storage import CloudStorage

# 페이지 설정
st.set_page_config(
    page_title="AI 튜터 팩토리",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .section-header {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .generate-button {
        background: linear-gradient(45deg, #FE6B8B 30%, #FF8E53 90%);
        color: white;
        padding: 0.5rem 2rem;
        border: none;
        border-radius: 25px;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .recent-ai-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .slider-container {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """세션 상태 초기화"""
    if 'preset_manager' not in st.session_state:
        st.session_state.preset_manager = PresetManager()
    if 'cloud_storage' not in st.session_state:
        st.session_state.cloud_storage = CloudStorage()
    if 'generated_teachers' not in st.session_state:
        st.session_state.generated_teachers = []

def render_header():
    """메인 헤더 렌더링"""
    st.markdown("""
    <div class="main-header">
        <h1>🎓 AI 튜터 팩토리</h1>
        <p>나만의 전문 AI 선생님을 만들어보세요</p>
    </div>
    """, unsafe_allow_html=True)

def render_core_settings():
    """핵심 기능 설정"""
    st.markdown('<div class="section-header"><h3>🔧 핵심 기능 설정</h3></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="slider-container">', unsafe_allow_html=True)
        experiment_detail = st.slider(
            "🧪 실험 단계 설명 상세도",
            min_value=1, max_value=10, value=7,
            help="실험 단계를 얼마나 자세히 설명할지"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="slider-container">', unsafe_allow_html=True)
        question_sensitivity = st.slider(
            "💬 질문 감지 민감도",
            min_value=1, max_value=10, value=6,
            help="학생의 질문을 얼마나 민감하게 감지할지"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="slider-container">', unsafe_allow_html=True)
        safety_focus = st.slider(
            "⚠️ 안전 주의사항 강조",
            min_value=1, max_value=10, value=8,
            help="안전 관련 내용을 얼마나 강조할지"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="slider-container">', unsafe_allow_html=True)
        theory_practice_balance = st.slider(
            "⚖️ 이론-실습 균형",
            min_value=1, max_value=10, value=5,
            help="1=실습위주, 10=이론위주"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    return {
        'experiment_detail': experiment_detail,
        'question_sensitivity': question_sensitivity,
        'safety_focus': safety_focus,
        'theory_practice_balance': theory_practice_balance
    }

def render_style_settings():
    """대화 스타일 설정"""
    st.markdown('<div class="section-header"><h3>🗣️ 대화 스타일 설정</h3></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="slider-container">', unsafe_allow_html=True)
        naturalness = st.slider(
            "🌊 자연스러운 말투",
            min_value=1, max_value=10, value=8,
            help="끊어지는 말, 되묻기 등 자연스러운 표현"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="slider-container">', unsafe_allow_html=True)
        adaptability = st.slider(
            "🔄 적응성",
            min_value=1, max_value=10, value=7,
            help="학생 반응에 따른 설명 조절"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="slider-container">', unsafe_allow_html=True)
        encouragement = st.slider(
            "👏 격려 수준",
            min_value=1, max_value=10, value=6,
            help="실시간 피드백과 격려 빈도"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    return {
        'naturalness': naturalness,
        'adaptability': adaptability,
        'encouragement': encouragement
    }

def render_personality_settings():
    """개성 & 스타일 설정"""
    st.markdown('<div class="section-header"><h3>🎭 개성 & 스타일 설정</h3></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="slider-container">', unsafe_allow_html=True)
        friendliness = st.slider(
            "😊 친근함",
            min_value=1, max_value=10, value=7,
            help="1=엄격함, 10=매우 친근함"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="slider-container">', unsafe_allow_html=True)
        humor = st.slider(
            "😄 유머 수준",
            min_value=1, max_value=10, value=5,
            help="대화에 포함될 유머의 양"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="slider-container">', unsafe_allow_html=True)
        explanation_style = st.slider(
            "📖 설명 방식",
            min_value=1, max_value=10, value=5,
            help="1=체험우선, 10=이론우선"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="slider-container">', unsafe_allow_html=True)
        interaction_frequency = st.slider(
            "🔄 상호작용 빈도",
            min_value=1, max_value=10, value=6,
            help="학생과의 상호작용 빈도"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    return {
        'friendliness': friendliness,
        'humor': humor,
        'explanation_style': explanation_style,
        'interaction_frequency': interaction_frequency
    }

def render_specialty_settings():
    """전문 분야 & 교육 수준 설정"""
    st.markdown('<div class="section-header"><h3>📚 전문 분야 & 교육 수준</h3></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔬 전문 분야")
        predefined_fields = [
            ('electromagnetic', '전자기학 (Electromagnetics)'),
            ('thermodynamics', '열역학 (Thermodynamics)'),
            ('quantum', '양자역학 (Quantum Mechanics)'),
            ('organic_chemistry', '유기화학 (Organic Chemistry)'),
            ('inorganic_chemistry', '무기화학 (Inorganic Chemistry)'),
            ('analytical_chemistry', '분석화학 (Analytical Chemistry)'),
            ('physical_chemistry', '물리화학 (Physical Chemistry)'),
            ('custom', '직접 입력...')
        ]
        
        selected_field = st.selectbox(
            "전문 분야 선택",
            options=[field[0] for field in predefined_fields],
            format_func=lambda x: next(field[1] for field in predefined_fields if field[0] == x),
            index=0
        )
        
        custom_field = ""
        if selected_field == 'custom':
            custom_field = st.text_input("전문 분야 직접 입력", placeholder="예: 생물학, 지구과학, 컴퓨터과학 등")
    
    with col2:
        st.subheader("🎓 교육 수준")
        education_level = st.selectbox(
            "대상 학습자 수준",
            options=['middle_school', 'high_school', 'university', 'graduate'],
            format_func=lambda x: {
                'middle_school': '🏫 중학교 수준',
                'high_school': '🏫 고등학교 수준', 
                'university': '🏛️ 대학교 수준',
                'graduate': '🎓 대학원 수준'
            }[x],
            index=1
        )
        
        # 교육 수준별 설명
        level_descriptions = {
            'middle_school': "쉬운 어휘, 기본 개념 중심, 생활 예시 활용",
            'high_school': "적절한 전문용어, 공식 설명, 실험 중심",
            'university': "전문 용어 사용, 이론적 배경, 심화 내용",
            'graduate': "고급 이론, 최신 연구, 논문 수준 설명"
        }
        st.info(level_descriptions[education_level])
    
    return {
        'selected_field': selected_field,
        'custom_field': custom_field,
        'education_level': education_level
    }

def render_document_upload():
    """참고 문서 업로드"""
    st.markdown('<div class="section-header"><h3>📄 참고 문서 업로드</h3></div>', unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "참고할 문서를 업로드하세요",
        type=['pdf', 'doc', 'docx', 'txt', 'md'],
        accept_multiple_files=True,
        help="AI가 참고할 강의 자료, 교재, 논문 등을 업로드하세요"
    )
    
    if uploaded_files:
        st.success(f"📁 {len(uploaded_files)}개 파일이 업로드되었습니다:")
        for file in uploaded_files:
            st.write(f"• {file.name} ({file.size} bytes)")
    
    use_general_knowledge = st.checkbox(
        "일반적인 물리화학 지식도 함께 사용",
        value=True,
        help="체크 해제 시 업로드된 문서와 선택된 전문 분야에만 집중"
    )
    
    return {
        'uploaded_files': uploaded_files,
        'use_general_knowledge': use_general_knowledge
    }

def render_ai_identity():
    """AI 정체성 설정"""
    st.markdown('<div class="section-header"><h3>👤 AI 선생님 정체성</h3></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        ai_name = st.text_input(
            "🏷️ AI 선생님 이름",
            value="김교수님",
            placeholder="예: 박조교님, 이선생님, 최박사님 등"
        )
        
        ai_title = st.selectbox(
            "👨‍🏫 직책/호칭",
            options=['교수님', '조교님', '선생님', '박사님', '연구원님', '튜터'],
            index=0
        )
    
    with col2:
        ai_background = st.text_area(
            "📋 간단한 배경 설명 (선택사항)",
            placeholder="예: 서울대학교 물리학과 교수로 20년간 전자기학을 연구하고 있습니다.",
            height=100
        )
    
    return {
        'ai_name': ai_name,
        'ai_title': ai_title, 
        'ai_background': ai_background
    }

def render_voice_settings():
    """음성 설정"""
    st.markdown('<div class="section-header"><h3>🎤 음성 설정</h3></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        voice_speed = st.slider(
            "🗣️ 음성 속도",
            min_value=0.5, max_value=2.0, value=1.0, step=0.1,
            help="말하는 속도 조절"
        )
    
    with col2:
        voice_pitch = st.slider(
            "🎵 음성 높이",
            min_value=0.5, max_value=2.0, value=1.0, step=0.1,
            help="목소리 톤 조절"
        )
    
    with col3:
        voice_volume = st.slider(
            "🔊 볼륨",
            min_value=0.0, max_value=1.0, value=0.8, step=0.1,
            help="음성 크기 조절"
        )
    
    auto_speak = st.checkbox(
        "🔄 AI 답변 자동 음성 재생",
        value=True,
        help="AI가 답변할 때 자동으로 음성으로 읽어줍니다"
    )
    
    return {
        'voice_speed': voice_speed,
        'voice_pitch': voice_pitch,
        'voice_volume': voice_volume,
        'auto_speak': auto_speak
    }

def generate_teacher_config(core_settings, style_settings, personality_settings, 
                          specialty_settings, document_settings, ai_identity, voice_settings):
    """AI 튜터 설정 생성"""
    config = {
        'id': str(uuid.uuid4()),
        'created_at': datetime.now().isoformat(),
        'core_settings': core_settings,
        'style_settings': style_settings,
        'personality_settings': personality_settings,
        'specialty_settings': specialty_settings,
        'document_settings': document_settings,
        'ai_identity': ai_identity,
        'voice_settings': voice_settings,
        'version': '1.0'
    }
    return config

def render_generate_button(config):
    """AI 생성 버튼"""
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(
            f"🚀 {config['ai_identity']['ai_name']} 생성하기",
            key="generate_teacher",
            help="설정한 조건으로 AI 튜터를 생성합니다"
        ):
            # 생성 과정 표시
            with st.spinner('AI 튜터를 생성하는 중...'):
                # 클라우드에 저장
                teacher_id = st.session_state.cloud_storage.save_teacher(config)
                
                # 세션에 추가
                st.session_state.generated_teachers.insert(0, {
                    'id': teacher_id,
                    'name': config['ai_identity']['ai_name'],
                    'title': config['ai_identity']['ai_title'],
                    'field': config['specialty_settings']['selected_field'],
                    'level': config['specialty_settings']['education_level'],
                    'created_at': config['created_at']
                })
                
                st.success(f"✅ {config['ai_identity']['ai_name']} 생성 완료!")
                st.balloons()
                
                # 새 창에서 AI 튜터 모드 열기
                teacher_url = f"?mode=teacher&id={teacher_id}"
                st.markdown(f"""
                <div style="text-align: center; margin: 1rem 0;">
                    <a href="{teacher_url}" target="_blank" 
                       style="background: linear-gradient(45deg, #FE6B8B 30%, #FF8E53 90%); 
                              color: white; padding: 1rem 2rem; text-decoration: none; 
                              border-radius: 25px; font-weight: bold; font-size: 1.2rem;">
                        🎓 {config['ai_identity']['ai_name']} 시작하기
                    </a>
                </div>
                """, unsafe_allow_html=True)

def render_recent_teachers():
    """최근 생성된 AI 선생님들"""
    st.markdown('<div class="section-header"><h3>📋 Recent AI Teachers</h3></div>', unsafe_allow_html=True)
    
    if not st.session_state.generated_teachers:
        st.info("아직 생성된 AI 선생님이 없습니다. 위에서 새로운 AI 튜터를 만들어보세요!")
        return
    
    for teacher in st.session_state.generated_teachers[:5]:  # 최근 5개만 표시
        with st.container():
            st.markdown(f"""
            <div class="recent-ai-card">
                <h4>👨‍🏫 {teacher['name']} {teacher['title']}</h4>
                <p><strong>전문분야:</strong> {teacher['field']} | <strong>수준:</strong> {teacher['level']}</p>
                <p><small>생성일: {teacher['created_at'][:16]}</small></p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button(f"🎓 시작", key=f"start_{teacher['id']}"):
                    teacher_url = f"?mode=teacher&id={teacher['id']}"
                    st.markdown(f'<meta http-equiv="refresh" content="0;url={teacher_url}">', unsafe_allow_html=True)
            
            with col2:
                if st.button(f"🗑️ 삭제", key=f"delete_{teacher['id']}"):
                    st.session_state.generated_teachers = [
                        t for t in st.session_state.generated_teachers if t['id'] != teacher['id']
                    ]
                    st.rerun()

def main():
    """메인 함수"""
    initialize_session_state()
    
    # URL 파라미터 확인
    query_params = st.experimental_get_query_params()
    if 'mode' in query_params and query_params['mode'][0] == 'teacher':
        # AI 튜터 모드로 리다이렉트
        teacher_id = query_params.get('id', [None])[0]
        if teacher_id:
            st.switch_page("pages/teacher_mode.py")
        return
    
    render_header()
    
    # 사이드바에 최근 AI들 표시
    with st.sidebar:
        render_recent_teachers()
    
    # 메인 설정 영역
    with st.container():
        # 모든 설정 수집
        core_settings = render_core_settings()
        style_settings = render_style_settings()
        personality_settings = render_personality_settings()
        specialty_settings = render_specialty_settings()
        document_settings = render_document_upload()
        ai_identity = render_ai_identity()
        voice_settings = render_voice_settings()
        
        # 설정 미리보기
        with st.expander("⚙️ 설정 미리보기", expanded=False):
            st.json({
                "AI 이름": ai_identity['ai_name'],
                "전문 분야": specialty_settings['selected_field'],
                "교육 수준": specialty_settings['education_level'],
                "성격 특성": f"친근함: {personality_settings['friendliness']}/10, 유머: {personality_settings['humor']}/10"
            })
        
        # AI 튜터 설정 생성
        config = generate_teacher_config(
            core_settings, style_settings, personality_settings,
            specialty_settings, document_settings, ai_identity, voice_settings
        )
        
        # 생성 버튼
        render_generate_button(config)

if __name__ == "__main__":
    main()
