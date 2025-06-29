import streamlit as st
import json
import uuid
from datetime import datetime
import os
from utils.claude_storage import save_ai_teacher, load_recent_teachers
from utils.preset_manager import load_preset, save_preset

# 페이지 설정
st.set_page_config(
    page_title="AI 튜터 팩토리",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 30px;
    }
    .teacher-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 10px 0;
    }
    .generate-button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        padding: 15px 30px;
        border-radius: 25px;
        font-size: 18px;
        font-weight: bold;
        cursor: pointer;
        margin: 20px 0;
    }
    .slider-container {
        background: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 15px 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # 메인 헤더
    st.markdown("""
    <div class="main-header">
        <h1>🎓 AI 튜터 팩토리</h1>
        <p>맞춤형 AI 선생님을 만들어보세요!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 사이드바 - Recent AI Teachers
    with st.sidebar:
        st.header("📋 최근 생성된 AI 튜터")
        recent_teachers = load_recent_teachers()
        
        if recent_teachers:
            for teacher in recent_teachers:
                with st.container():
                    st.markdown(f"""
                    <div class="teacher-card">
                        <h4>👨‍🏫 {teacher['name']}</h4>
                        <p><strong>분야:</strong> {teacher['subject']}</p>
                        <p><strong>수준:</strong> {teacher['level']}</p>
                        <p><small>생성: {teacher['created_at']}</small></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"▶️ {teacher['name']} 실행", key=f"run_{teacher['id']}"):
                        st.session_state.selected_teacher = teacher
                        st.switch_page("pages/teacher_mode.py")
        else:
            st.info("아직 생성된 AI 튜터가 없습니다.")
    
    # 메인 컨텐츠
    tab1, tab2 = st.tabs(["🚀 새 AI 튜터 생성", "📚 프리셋 관리"])
    
    with tab1:
        create_new_teacher()
    
    with tab2:
        manage_presets()

def create_new_teacher():
    st.header("🛠️ AI 튜터 생성기")
    
    # 기본 정보
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 기본 정보")
        teacher_name = st.text_input("AI 튜터 이름", placeholder="예: 김교수님, 박조교님")
        
        subject = st.selectbox(
            "전문 분야",
            ["물리학", "화학", "생물학", "수학", "지구과학", "공학", "기타"],
            index=0
        )
        
        if subject == "기타":
            custom_subject = st.text_input("직접 입력", placeholder="전문 분야를 입력하세요")
            subject = custom_subject if custom_subject else "기타"
        
        level = st.selectbox(
            "교육 수준",
            ["중학교", "고등학교", "대학교", "대학원"],
            index=1
        )
    
    with col2:
        st.subheader("📄 참고 자료")
        uploaded_files = st.file_uploader(
            "문서 업로드 (PDF, DOC, TXT)",
            accept_multiple_files=True,
            type=['pdf', 'doc', 'docx', 'txt']
        )
        
        use_general_knowledge = st.checkbox("일반 지식 사용", value=True)
        
        if uploaded_files:
            st.success(f"{len(uploaded_files)}개 파일 업로드됨")
    
    # 성격 설정
    st.markdown('<div class="slider-container">', unsafe_allow_html=True)
    st.subheader("🎭 AI 튜터 성격 설정")
    
    col1, col2 = st.columns(2)
    
    with col1:
        friendliness = st.slider("친근함", 0, 100, 70, help="0: 매우 엄격함 ↔ 100: 매우 친근함")
        humor_level = st.slider("유머 수준", 0, 100, 30, help="0: 진지함 ↔ 100: 유머러스")
        encouragement = st.slider("격려 수준", 0, 100, 80, help="0: 객관적 ↔ 100: 매우 격려적")
        interaction_frequency = st.slider("상호작용 빈도", 0, 100, 60, help="0: 일방적 설명 ↔ 100: 자주 질문")
    
    with col2:
        explanation_detail = st.slider("설명 상세도", 0, 100, 70, help="0: 간단명료 ↔ 100: 매우 상세")
        theory_vs_practice = st.slider("이론-실습 균형", 0, 100, 50, help="0: 이론 중심 ↔ 100: 실습 중심")
        safety_emphasis = st.slider("안전 강조", 0, 100, 90, help="실험/실습 시 안전 주의사항 강조")
        adaptability = st.slider("적응성", 0, 100, 75, help="학생 반응에 따른 설명 방식 조절")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 대화 스타일
    st.markdown('<div class="slider-container">', unsafe_allow_html=True)
    st.subheader("💬 대화 스타일")
    
    col1, col2 = st.columns(2)
    
    with col1:
        natural_speech = st.slider("자연스러운 말투", 0, 100, 80, help="끊어지는 말, 되묻기 등")
        question_sensitivity = st.slider("질문 감지 민감도", 0, 100, 70, help="학생의 질문을 얼마나 민감하게 감지할지")
    
    with col2:
        response_speed = st.slider("응답 속도", 0, 100, 60, help="0: 천천히 신중하게 ↔ 100: 빠르게 반응")
        vocabulary_level = st.slider("어휘 수준", 0, 100, 50, help="0: 쉬운 어휘 ↔ 100: 전문 용어")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 음성 설정
    st.markdown('<div class="slider-container">', unsafe_allow_html=True)
    st.subheader("🔊 음성 설정")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        voice_speed = st.slider("음성 속도", 0.5, 2.0, 1.0, 0.1)
    
    with col2:
        voice_pitch = st.slider("음성 높이", 0.5, 2.0, 1.0, 0.1)
    
    with col3:
        auto_voice = st.checkbox("자동 음성 재생", value=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 생성 버튼
    if st.button("🚀 AI 튜터 생성하기", type="primary", use_container_width=True):
        if not teacher_name:
            st.error("AI 튜터 이름을 입력해주세요!")
            return
        
        # AI 튜터 설정 저장
        teacher_config = {
            "id": str(uuid.uuid4()),
            "name": teacher_name,
            "subject": subject,
            "level": level,
            "uploaded_files": [f.name for f in uploaded_files] if uploaded_files else [],
            "use_general_knowledge": use_general_knowledge,
            "personality": {
                "friendliness": friendliness,
                "humor_level": humor_level,
                "encouragement": encouragement,
                "interaction_frequency": interaction_frequency,
                "explanation_detail": explanation_detail,
                "theory_vs_practice": theory_vs_practice,
                "safety_emphasis": safety_emphasis,
                "adaptability": adaptability,
                "natural_speech": natural_speech,
                "question_sensitivity": question_sensitivity,
                "response_speed": response_speed,
                "vocabulary_level": vocabulary_level
            },
            "voice_settings": {
                "speed": voice_speed,
                "pitch": voice_pitch,
                "auto_play": auto_voice
            },
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        # 클라우드에 저장
        save_ai_teacher(teacher_config)
        
        # 세션에 저장하고 튜터 모드로 이동
        st.session_state.selected_teacher = teacher_config
        
        st.success(f"🎉 '{teacher_name}' AI 튜터가 생성되었습니다!")
        st.balloons()
        
        # 튜터 모드로 이동
        if st.button("▶️ 지금 바로 실행하기"):
            st.switch_page("pages/teacher_mode.py")

def manage_presets():
    st.header("📚 프리셋 관리")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("기본 프리셋")
        
        presets = {
            "물리 교수님": {
                "subject": "물리학",
                "level": "대학교",
                "personality": {
                    "friendliness": 40,
                    "humor_level": 20,
                    "encouragement": 60,
                    "explanation_detail": 90,
                    "theory_vs_practice": 30
                }
            },
            "화학 실험 조교": {
                "subject": "화학",
                "level": "고등학교",
                "personality": {
                    "friendliness": 80,
                    "humor_level": 50,
                    "safety_emphasis": 95,
                    "theory_vs_practice": 70
                }
            },
            "친근한 수학 선생님": {
                "subject": "수학",
                "level": "중학교",
                "personality": {
                    "friendliness": 90,
                    "humor_level": 70,
                    "encouragement": 90,
                    "vocabulary_level": 30
                }
            }
        }
        
        for preset_name, preset_config in presets.items():
            if st.button(f"📋 {preset_name} 불러오기"):
                # 프리셋 설정을 세션에 저장
                st.session_state.preset_loaded = preset_config
                st.success(f"{preset_name} 프리셋이 로드되었습니다!")
    
    with col2:
        st.subheader("사용자 프리셋")
        st.info("현재 설정을 프리셋으로 저장하거나 기존 프리셋을 관리할 수 있습니다.")
        
        preset_name = st.text_input("프리셋 이름")
        if st.button("💾 현재 설정 저장"):
            if preset_name:
                st.success(f"'{preset_name}' 프리셋이 저장되었습니다!")
            else:
                st.error("프리셋 이름을 입력해주세요!")

if __name__ == "__main__":
    main()

# 페이지 설정
st.set_page_config(
    page_title="AI 튜터 팩토리",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 30px;
    }
    .teacher-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 10px 0;
    }
    .generate-button {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        padding: 15px 30px;
        border-radius: 25px;
        font-size: 18px;
        font-weight: bold;
        cursor: pointer;
        margin: 20px 0;
    }
    .slider-container {
        background: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 15px 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # 메인 헤더
    st.markdown("""
    <div class="main-header">
        <h1>🎓 AI 튜터 팩토리</h1>
        <p>맞춤형 AI 선생님을 만들어보세요!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 사이드바 - Recent AI Teachers
    with st.sidebar:
        st.header("📋 최근 생성된 AI 튜터")
        recent_teachers = load_recent_teachers()
        
        if recent_teachers:
            for teacher in recent_teachers:
                with st.container():
                    st.markdown(f"""
                    <div class="teacher-card">
                        <h4>👨‍🏫 {teacher['name']}</h4>
                        <p><strong>분야:</strong> {teacher['subject']}</p>
                        <p><strong>수준:</strong> {teacher['level']}</p>
                        <p><small>생성: {teacher['created_at']}</small></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"▶️ {teacher['name']} 실행", key=f"run_{teacher['id']}"):
                        st.session_state.selected_teacher = teacher
                        st.switch_page("pages/teacher_mode.py")
        else:
            st.info("아직 생성된 AI 튜터가 없습니다.")
    
    # 메인 컨텐츠
    tab1, tab2 = st.tabs(["🚀 새 AI 튜터 생성", "📚 프리셋 관리"])
    
    with tab1:
        create_new_teacher()
    
    with tab2:
        manage_presets()

def create_new_teacher():
    st.header("🛠️ AI 튜터 생성기")
    
    # 기본 정보
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 기본 정보")
        teacher_name = st.text_input("AI 튜터 이름", placeholder="예: 김교수님, 박조교님")
        
        subject = st.selectbox(
            "전문 분야",
            ["물리학", "화학", "생물학", "수학", "지구과학", "공학", "기타"],
            index=0
        )
        
        if subject == "기타":
            custom_subject = st.text_input("직접 입력", placeholder="전문 분야를 입력하세요")
            subject = custom_subject if custom_subject else "기타"
        
        level = st.selectbox(
            "교육 수준",
            ["중학교", "고등학교", "대학교", "대학원"],
            index=1
        )
    
    with col2:
        st.subheader("📄 참고 자료")
        uploaded_files = st.file_uploader(
            "문서 업로드 (PDF, DOC, TXT)",
            accept_multiple_files=True,
            type=['pdf', 'doc', 'docx', 'txt']
        )
        
        use_general_knowledge = st.checkbox("일반 지식 사용", value=True)
        
        if uploaded_files:
            st.success(f"{len(uploaded_files)}개 파일 업로드됨")
    
    # 성격 설정
    st.markdown('<div class="slider-container">', unsafe_allow_html=True)
    st.subheader("🎭 AI 튜터 성격 설정")
    
    col1, col2 = st.columns(2)
    
    with col1:
        friendliness = st.slider("친근함", 0, 100, 70, help="0: 매우 엄격함 ↔ 100: 매우 친근함")
        humor_level = st.slider("유머 수준", 0, 100, 30, help="0: 진지함 ↔ 100: 유머러스")
        encouragement = st.slider("격려 수준", 0, 100, 80, help="0: 객관적 ↔ 100: 매우 격려적")
        interaction_frequency = st.slider("상호작용 빈도", 0, 100, 60, help="0: 일방적 설명 ↔ 100: 자주 질문")
    
    with col2:
        explanation_detail = st.slider("설명 상세도", 0, 100, 70, help="0: 간단명료 ↔ 100: 매우 상세")
        theory_vs_practice = st.slider("이론-실습 균형", 0, 100, 50, help="0: 이론 중심 ↔ 100: 실습 중심")
        safety_emphasis = st.slider("안전 강조", 0, 100, 90, help="실험/실습 시 안전 주의사항 강조")
        adaptability = st.slider("적응성", 0, 100, 75, help="학생 반응에 따른 설명 방식 조절")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 대화 스타일
    st.markdown('<div class="slider-container">', unsafe_allow_html=True)
    st.subheader("💬 대화 스타일")
    
    col1, col2 = st.columns(2)
    
    with col1:
        natural_speech = st.slider("자연스러운 말투", 0, 100, 80, help="끊어지는 말, 되묻기 등")
        question_sensitivity = st.slider("질문 감지 민감도", 0, 100, 70, help="학생의 질문을 얼마나 민감하게 감지할지")
    
    with col2:
        response_speed = st.slider("응답 속도", 0, 100, 60, help="0: 천천히 신중하게 ↔ 100: 빠르게 반응")
        vocabulary_level = st.slider("어휘 수준", 0, 100, 50, help="0: 쉬운 어휘 ↔ 100: 전문 용어")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 음성 설정
    st.markdown('<div class="slider-container">', unsafe_allow_html=True)
    st.subheader("🔊 음성 설정")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        voice_speed = st.slider("음성 속도", 0.5, 2.0, 1.0, 0.1)
    
    with col2:
        voice_pitch = st.slider("음성 높이", 0.5, 2.0, 1.0, 0.1)
    
    with col3:
        auto_voice = st.checkbox("자동 음성 재생", value=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 생성 버튼
    if st.button("🚀 AI 튜터 생성하기", type="primary", use_container_width=True):
        if not teacher_name:
            st.error("AI 튜터 이름을 입력해주세요!")
            return
        
        # AI 튜터 설정 저장
        teacher_config = {
            "id": str(uuid.uuid4()),
            "name": teacher_name,
            "subject": subject,
            "level": level,
            "uploaded_files": [f.name for f in uploaded_files] if uploaded_files else [],
            "use_general_knowledge": use_general_knowledge,
            "personality": {
                "friendliness": friendliness,
                "humor_level": humor_level,
                "encouragement": encouragement,
                "interaction_frequency": interaction_frequency,
                "explanation_detail": explanation_detail,
                "theory_vs_practice": theory_vs_practice,
                "safety_emphasis": safety_emphasis,
                "adaptability": adaptability,
                "natural_speech": natural_speech,
                "question_sensitivity": question_sensitivity,
                "response_speed": response_speed,
                "vocabulary_level": vocabulary_level
            },
            "voice_settings": {
                "speed": voice_speed,
                "pitch": voice_pitch,
                "auto_play": auto_voice
            },
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        # 클라우드에 저장
        save_ai_teacher(teacher_config)
        
        # 세션에 저장하고 튜터 모드로 이동
        st.session_state.selected_teacher = teacher_config
        
        st.success(f"🎉 '{teacher_name}' AI 튜터가 생성되었습니다!")
        st.balloons()
        
        # 튜터 모드로 이동
        if st.button("▶️ 지금 바로 실행하기"):
            st.switch_page("pages/teacher_mode.py")

def manage_presets():
    st.header("📚 프리셋 관리")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("기본 프리셋")
        
        presets = {
            "물리 교수님": {
                "subject": "물리학",
                "level": "대학교",
                "personality": {
                    "friendliness": 40,
                    "humor_level": 20,
                    "encouragement": 60,
                    "explanation_detail": 90,
                    "theory_vs_practice": 30
                }
            },
            "화학 실험 조교": {
                "subject": "화학",
                "level": "고등학교",
                "personality": {
                    "friendliness": 80,
                    "humor_level": 50,
                    "safety_emphasis": 95,
                    "theory_vs_practice": 70
                }
            },
            "친근한 수학 선생님": {
                "subject": "수학",
                "level": "중학교",
                "personality": {
                    "friendliness": 90,
                    "humor_level": 70,
                    "encouragement": 90,
                    "vocabulary_level": 30
                }
            }
        }
        
        for preset_name, preset_config in presets.items():
            if st.button(f"📋 {preset_name} 불러오기"):
                # 프리셋 설정을 세션에 저장
                st.session_state.preset_loaded = preset_config
                st.success(f"{preset_name} 프리셋이 로드되었습니다!")
    
    with col2:
        st.subheader("사용자 프리셋")
        st.info("현재 설정을 프리셋으로 저장하거나 기존 프리셋을 관리할 수 있습니다.")
        
        preset_name = st.text_input("프리셋 이름")
        if st.button("💾 현재 설정 저장"):
            if preset_name:
                st.success(f"'{preset_name}' 프리셋이 저장되었습니다!")
            else:
                st.error("프리셋 이름을 입력해주세요!")

if __name__ == "__main__":
    main()
