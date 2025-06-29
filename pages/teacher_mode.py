import streamlit as st
import json
import time
from datetime import datetime
from utils.claude_api import ClaudeAPI
from utils.voice_handler import VoiceHandler
from utils.cloud_storage import CloudStorage
from utils.blackboard import SmartBlackboard
import uuid

# 페이지 설정
st.set_page_config(
    page_title="AI 튜터 모드",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 커스텀 CSS
st.markdown("""
<style>
    .teacher-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .blackboard {
        background: #1e3a3a;
        color: #00ff00;
        font-family: 'Courier New', monospace;
        padding: 2rem;
        border-radius: 10px;
        min-height: 400px;
        margin: 1rem 0;
        border: 3px solid #4a6741;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.5);
        position: relative;
        overflow-y: auto;
    }
    
    .blackboard-text {
        font-size: 1.2rem;
        line-height: 1.8;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    
    .highlight-red { color: #ff6b6b; font-weight: bold; }
    .highlight-yellow { color: #ffd93d; font-weight: bold; }
    .highlight-blue { color: #6bcf7f; font-weight: bold; }
    .highlight-orange { color: #ff8c42; font-weight: bold; }
    .underline { text-decoration: underline; }
    .circle { 
        border: 2px solid #ff6b6b; 
        border-radius: 50%; 
        padding: 0.2rem 0.5rem; 
        display: inline-block; 
        margin: 0.2rem;
    }
    
    .mic-button {
        background: linear-gradient(45deg, #ff4757, #ff3742);
        color: white;
        border: none;
        border-radius: 50%;
        width: 80px;
        height: 80px;
        font-size: 2rem;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(255,71,87,0.4);
        transition: all 0.3s ease;
    }
    
    .mic-button:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 20px rgba(255,71,87,0.6);
    }
    
    .mic-button.recording {
        background: linear-gradient(45deg, #ff6b6b, #ff5252);
        animation: pulse 1.5s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
    
    .control-panel {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
    
    .status-bar {
        background: #e9ecef;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .math-formula {
        background: rgba(255,255,255,0.1);
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 3px solid #ffd93d;
        margin: 0.5rem 0;
        font-family: 'Times New Roman', serif;
    }
    
    .typing-cursor {
        animation: blink 1s infinite;
    }
    
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0; }
    }
    
    .voice-controls {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 1rem;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_teacher_session():
    """AI 튜터 세션 초기화"""
    if 'teacher_config' not in st.session_state:
        st.session_state.teacher_config = None
    if 'claude_api' not in st.session_state:
        st.session_state.claude_api = ClaudeAPI()
    if 'voice_handler' not in st.session_state:
        st.session_state.voice_handler = VoiceHandler()
    if 'blackboard' not in st.session_state:
        st.session_state.blackboard = SmartBlackboard()
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'is_recording' not in st.session_state:
        st.session_state.is_recording = False
    if 'is_speaking' not in st.session_state:
        st.session_state.is_speaking = False
    if 'blackboard_content' not in st.session_state:
        st.session_state.blackboard_content = ""

def load_teacher_config(teacher_id):
    """AI 튜터 설정 로드"""
    try:
        cloud_storage = CloudStorage()
        config = cloud_storage.load_teacher(teacher_id)
        st.session_state.teacher_config = config
        return config
    except Exception as e:
        st.error(f"AI 튜터 로딩 실패: {str(e)}")
        return None

def render_teacher_header(config):
    """AI 튜터 헤더"""
    ai_name = config['ai_identity']['ai_name']
    ai_title = config['ai_identity']['ai_title']
    field = config['specialty_settings']['selected_field']
    level = config['specialty_settings']['education_level']
    
    level_text = {
        'middle_school': '중학교',
        'high_school': '고등학교', 
        'university': '대학교',
        'graduate': '대학원'
    }.get(level, level)
    
    st.markdown(f"""
    <div class="teacher-header">
        <h1>🎓 {ai_name} {ai_title}</h1>
        <p>📚 {field} 전문 | 🎯 {level_text} 수준</p>
        <p><small>음성 명령으로 AI와 상호작용하세요</small></p>
    </div>
    """, unsafe_allow_html=True)

def render_blackboard():
    """스마트 칠판 렌더링"""
    st.markdown("### 📝 AI 칠판")
    
    # 칠판 영역
    blackboard_placeholder = st.empty()
    
    with blackboard_placeholder.container():
        st.markdown(f"""
        <div class="blackboard">
            <div class="blackboard-text" id="blackboard-content">
                {st.session_state.blackboard_content}
                <span class="typing-cursor">|</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    return blackboard_placeholder

def render_voice_controls():
    """음성 컨트롤 패널"""
    st.markdown("### 🎤 음성 컨트롤")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # 메인 마이크 버튼
        mic_container = st.empty()
        
        recording_status = "recording" if st.session_state.is_recording else ""
        mic_text = "🎙️ 녹음 중..." if st.session_state.is_recording else "🎤 PUSH TO TALK"
        
        if st.button(
            mic_text,
            key="main_mic_button",
            help="길게 눌러서 음성 입력",
            use_container_width=True
        ):
            toggle_recording()
    
    # 상태 표시
    status_container = st.empty()
    
    if st.session_state.is_recording:
        status_container.markdown("""
        <div class="status-bar" style="background: #ffe6e6; color: #d63031;">
            🔴 음성 입력 중... 마이크에 대고 말씀하세요
        </div>
        """, unsafe_allow_html=True)
    elif st.session_state.is_speaking:
        status_container.markdown("""
        <div class="status-bar" style="background: #e6f3ff; color: #0984e3;">
            🗣️ AI가 응답하는 중...
        </div>
        """, unsafe_allow_html=True)
    else:
        status_container.markdown("""
        <div class="status-bar" style="background: #e8f5e8; color: #00b894;">
            ✅ 준비 완료 - 마이크 버튼을 눌러 질문하세요
        </div>
        """, unsafe_allow_html=True)
    
    return status_container

def toggle_recording():
    """녹음 상태 토글"""
    if st.session_state.is_recording:
        # 녹음 중지
        st.session_state.is_recording = False
        process_voice_input()
    else:
        # 녹음 시작
        st.session_state.is_recording = True
        st.session_state.voice_handler.start_recording()

def process_voice_input():
    """음성 입력 처리"""
    try:
        # 음성을 텍스트로 변환
        user_input = st.session_state.voice_handler.speech_to_text()
        
        if user_input:
            # 대화 히스토리에 추가
            st.session_state.conversation_history.append({
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now().isoformat()
            })
            
            # AI 응답 생성
            generate_ai_response(user_input)
            
        else:
            st.warning("음성을 인식하지 못했습니다. 다시 시도해주세요.")
            
    except Exception as e:
        st.error(f"음성 처리 오류: {str(e)}")

def generate_ai_response(user_input):
    """AI 응답 생성 및 칠판 업데이트"""
    try:
        st.session_state.is_speaking = True
        
        # Claude API 호출
        config = st.session_state.teacher_config
        response = st.session_state.claude_api.generate_response(
            user_input, 
            config, 
            st.session_state.conversation_history
        )
        
        # 응답을 대화 히스토리에 추가
        st.session_state.conversation_history.append({
            'role': 'assistant',
            'content': response['text'],
            'timestamp': datetime.now().isoformat(),
            'blackboard_content': response.get('blackboard_content', '')
        })
        
        # 칠판 업데이트 (타이핑 애니메이션)
        update_blackboard_with_animation(response.get('blackboard_content', ''))
        
        # 음성 출력
        if config['voice_settings']['auto_speak']:
            st.session_state.voice_handler.text_to_speech(
                response['text'], 
                config['voice_settings']
            )
        
        st.session_state.is_speaking = False
        
    except Exception as e:
        st.error(f"AI 응답 생성 오류: {str(e)}")
        st.session_state.is_speaking = False

def update_blackboard_with_animation(content):
    """칠판 내용을 타이핑 애니메이션으로 업데이트"""
    if not content:
        return
    
    # 기존 내용에 새 내용 추가
    if st.session_state.blackboard_content:
        st.session_state.blackboard_content += "\n\n"
    
    # 타이핑 애니메이션 시뮬레이션
    for i in range(len(content)):
        st.session_state.blackboard_content += content[i]
        time.sleep(0.05)  # 타이핑 속도 조절

def format_blackboard_content(text):
    """칠판 내용 포맷팅 (색상, 강조 등)"""
    # 수식 감지 및 포맷팅
    if any(math_symbol in text for math_symbol in ['=', '+', '-', '×', '÷', '∫', '∑']):
        text = f'<div class="math-formula">{text}</div>'
    
    # 중요 키워드 강조
    important_keywords = ['중요', '주의', '핵심', '공식', '법칙', '원리']
    for keyword in important_keywords:
        text = text.replace(keyword, f'<span class="highlight-red">{keyword}</span>')
    
    # 숫자 강조
    import re
    text = re.sub(r'\b\d+\b', r'<span class="highlight-yellow">\g<0></span>', text)
    
    return text

def render_conversation_history():
    """대화 히스토리 표시"""
    if not st.session_state.conversation_history:
        st.info("아직 대화가 없습니다. 마이크 버튼을 눌러 질문해보세요!")
        return
    
    st.markdown("### 💬 대화 히스토리")
    
    with st.expander("대화 기록 보기", expanded=False):
        for msg in st.session_state.conversation_history[-10:]:  # 최근 10개만 표시
            if msg['role'] == 'user':
                st.markdown(f"**🙋‍♂️ 학생:** {msg['content']}")
            else:
                st.markdown(f"**🎓 AI 튜터:** {msg['content']}")
            st.markdown(f"<small>{msg['timestamp'][:19]}</small>", unsafe_allow_html=True)
            st.markdown("---")

def render_control_panel():
    """컨트롤 패널"""
    st.markdown("### ⚙️ 컨트롤 패널")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🗑️ 칠판 지우기", use_container_width=True):
            st.session_state.blackboard_content = ""
            st.rerun()
    
    with col2:
        if st.button("🔄 대화 초기화", use_container_width=True):
            st.session_state.conversation_history = []
            st.session_state.blackboard_content = ""
            st.rerun()
    
    with col3:
        if st.button("⏸️ 음성 중지", use_container_width=True):
            st.session_state.voice_handler.stop_speech()
            st.session_state.is_speaking = False
    
    with col4:
        if st.button("🏠 메인으로", use_container_width=True):
            st.switch_page("app.py")

def render_quick_commands():
    """빠른 명령어 버튼들"""
    st.markdown("### ⚡ 빠른 명령어")
    
    col1, col2, col3 = st.columns(3)
    
    commands = [
        ("개념 설명해줘", "💡 개념 설명"),
        ("실험 방법 알려줘", "🧪 실험 방법"),
        ("예시 들어줘", "📝 예시"),
        ("문제 풀어줘", "🎯 문제 풀이"),
        ("정리해줘", "📋 정리"),
        ("질문 받아줘", "❓ 질문 받기")
    ]
    
    for i, (command, button_text) in enumerate(commands):
        col = [col1, col2, col3][i % 3]
        with col:
            if st.button(button_text, key=f"quick_cmd_{i}", use_container_width=True):
                # 음성 없이 직접 AI에게 명령 전달
                st.session_state.conversation_history.append({
                    'role': 'user',
                    'content': command,
                    'timestamp': datetime.now().isoformat()
                })
                generate_ai_response(command)
                st.rerun()

def main():
    """메인 함수"""
    initialize_teacher_session()
    
    # URL 파라미터에서 teacher_id 가져오기
    query_params = st.experimental_get_query_params()
    teacher_id = query_params.get('id', [None])[0]
    
    if not teacher_id:
        st.error("AI 튜터 ID가 없습니다. 메인 페이지에서 AI 튜터를 생성해주세요.")
        if st.button("🏠 메인 페이지로 돌아가기"):
            st.switch_page("app.py")
        return
    
    # AI 튜터 설정 로드
    if st.session_state.teacher_config is None:
        config = load_teacher_config(teacher_id)
        if not config:
            return
    else:
        config = st.session_state.teacher_config
    
    # 헤더 렌더링
    render_teacher_header(config)
    
    # 메인 레이아웃
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 칠판 영역
        blackboard_placeholder = render_blackboard()
        
        # 음성 컨트롤
        render_voice_controls()
    
    with col2:
        # 빠른 명령어
        render_quick_commands()
        
        # 컨트롤 패널
        render_control_panel()
        
        # 대화 히스토리
        render_conversation_history()
    
    # 실시간 업데이트를 위한 자동 새로고침 (선택적)
    if st.session_state.is_recording or st.session_state.is_speaking:
        time.sleep(1)
        st.rerun()

if __name__ == "__main__":
    main()
