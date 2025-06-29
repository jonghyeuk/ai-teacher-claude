import streamlit as st
import json
import time
from datetime import datetime
from utils.claude_api import get_claude_response, generate_system_prompt
from utils.voice_handler import text_to_speech, speech_to_text
import re

# 페이지 설정
st.set_page_config(
    page_title="AI 튜터 모드",
    page_icon="👨‍🏫",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS 스타일
st.markdown("""
<style>
    .teacher-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        color: white;
        margin-bottom: 20px;
    }
    
    .blackboard {
        background: #2d3748;
        color: #e2e8f0;
        padding: 20px;
        border-radius: 10px;
        font-family: 'Courier New', monospace;
        font-size: 16px;
        line-height: 1.6;
        min-height: 400px;
        border: 3px solid #4a5568;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.3);
        overflow-y: auto;
        white-space: pre-wrap;
    }
    
    .blackboard h1, .blackboard h2, .blackboard h3 {
        color: #ffd700;
        text-decoration: underline;
        margin: 20px 0 10px 0;
    }
    
    .blackboard .important {
        background: #yellow;
        color: #000;
        padding: 2px 4px;
        border-radius: 3px;
        font-weight: bold;
    }
    
    .blackboard .formula {
        background: #4a90e2;
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-size: 18px;
        text-align: center;
        margin: 10px 0;
        border-left: 4px solid #ffd700;
    }
    
    .blackboard .highlight-red {
        color: #ff6b6b;
        font-weight: bold;
    }
    
    .blackboard .highlight-blue {
        color: #4dabf7;
        font-weight: bold;
    }
    
    .blackboard .highlight-green {
        color: #51cf66;
        font-weight: bold;
    }
    
    .blackboard .circle {
        border: 2px solid #ffd700;
        border-radius: 50%;
        padding: 5px 10px;
        display: inline-block;
        margin: 2px;
    }
    
    .mic-button {
        background: #e74c3c;
        color: white;
        border: none;
        border-radius: 50%;
        width: 80px;
        height: 80px;
        font-size: 24px;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(231, 76, 60, 0.4);
        transition: all 0.3s ease;
        margin: 20px;
    }
    
    .mic-button:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 20px rgba(231, 76, 60, 0.6);
    }
    
    .mic-button.active {
        background: #27ae60;
        animation: pulse 1s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .chat-container {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        max-height: 300px;
        overflow-y: auto;
        border: 1px solid #dee2e6;
    }
    
    .user-message {
        background: #007bff;
        color: white;
        padding: 10px 15px;
        border-radius: 15px 15px 5px 15px;
        margin: 5px 0;
        margin-left: 50px;
        word-wrap: break-word;
    }
    
    .ai-message {
        background: #28a745;
        color: white;
        padding: 10px 15px;
        border-radius: 15px 15px 15px 5px;
        margin: 5px 0;
        margin-right: 50px;
        word-wrap: break-word;
    }
    
    .control-panel {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 20px 0;
    }
    
    .typing-animation {
        animation: typewriter 0.05s steps(1) infinite;
    }
    
    @keyframes typewriter {
        from { opacity: 0; }
        to { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

def initialize_teacher():
    """AI 튜터 초기화"""
    if 'selected_teacher' not in st.session_state:
        st.error("AI 튜터가 선택되지 않았습니다. 메인 페이지로 돌아가세요.")
        if st.button("🏠 메인 페이지로"):
            st.switch_page("app.py")
        return None
    
    teacher = st.session_state.selected_teacher
    
    # 대화 히스토리 초기화
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # 칠판 내용 초기화
    if 'blackboard_content' not in st.session_state:
        st.session_state.blackboard_content = f"🎓 {teacher['name']}의 {teacher['subject']} 수업\n\n📚 교육 수준: {teacher['level']}\n\n수업을 시작할 준비가 되었습니다!\n마이크 버튼을 눌러 질문하거나 수업을 요청해보세요."
    
    # 마이크 상태
    if 'is_recording' not in st.session_state:
        st.session_state.is_recording = False
    
    return teacher

def format_blackboard_text(text):
    """칠판에 표시할 텍스트 포맷팅"""
    # 수식 감지 및 포맷팅
    text = re.sub(r'\$([^$]+)\$', r'<div class="formula">\1</div>', text)
    
    # 중요한 단어 강조 (대문자나 **로 감싸진 텍스트)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<span class="important">\1</span>', text)
    
    # 색상 태그 변환
    text = re.sub(r'\[RED\]([^[]+)\[/RED\]', r'<span class="highlight-red">\1</span>', text)
    text = re.sub(r'\[BLUE\]([^[]+)\[/BLUE\]', r'<span class="highlight-blue">\1</span>', text)
    text = re.sub(r'\[GREEN\]([^[]+)\[/GREEN\]', r'<span class="highlight-green">\1</span>', text)
    
    # 원 표시 (중요한 부분)
    text = re.sub(r'\[CIRCLE\]([^[]+)\[/CIRCLE\]', r'<span class="circle">\1</span>', text)
    
    return text

def animate_blackboard_writing(text, container):
    """칠판에 글씨를 타이핑하는 애니메이션"""
    formatted_text = format_blackboard_text(text)
    
    # 실제로는 바로 표시 (실시간 타이핑은 복잡하므로 간소화)
    container.markdown(f'<div class="blackboard">{formatted_text}</div>', unsafe_allow_html=True)
    
    return formatted_text

def main():
    teacher = initialize_teacher()
    if not teacher:
        return
    
    # 헤더
    st.markdown(f"""
    <div class="teacher-header">
        <h1>👨‍🏫 {teacher['name']}</h1>
        <p>{teacher['subject']} | {teacher['level']} 수준</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 종료 버튼
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("🏠 메인으로 돌아가기"):
            # 세션 클리어
            if 'chat_history' in st.session_state:
                del st.session_state.chat_history
            if 'blackboard_content' in st.session_state:
                del st.session_state.blackboard_content
            st.switch_page("app.py")
    
    with col3:
        if st.button("🗑️ 칠판 지우기"):
            st.session_state.blackboard_content = ""
            st.rerun()
    
    # 메인 레이아웃
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 AI 칠판")
        blackboard_container = st.empty()
        
        # 칠판 내용 표시
        if st.session_state.blackboard_content:
            animate_blackboard_writing(st.session_state.blackboard_content, blackboard_container)
        else:
            blackboard_container.markdown('<div class="blackboard">칠판이 비어있습니다.</div>', unsafe_allow_html=True)
    
    with col2:
        st.subheader("🎤 음성 컨트롤")
        
        # Push-to-Talk 버튼
        mic_container = st.empty()
        
        if st.session_state.is_recording:
            if mic_container.button("🎤 녹음 중... (놓으면 전송)", key="stop_recording", help="버튼을 놓으면 음성 전송"):
                st.session_state.is_recording = False
                # 여기서 음성 인식 처리
                process_voice_input()
                st.rerun()
        else:
            if mic_container.button("🎤 눌러서 말하기", key="start_recording", help="버튼을 누르고 있는 동안 녹음"):
                st.session_state.is_recording = True
                st.rerun()
        
        # 음성 설정
        st.subheader("🔊 음성 설정")
        with st.expander("설정 조절"):
            voice_speed = st.slider("음성 속도", 0.5, 2.0, teacher['voice_settings']['speed'], 0.1)
            voice_pitch = st.slider("음성 높이", 0.5, 2.0, teacher['voice_settings']['pitch'], 0.1)
            auto_play = st.checkbox("자동 재생", teacher['voice_settings']['auto_play'])
        
        # 채팅 히스토리
        st.subheader("💬 대화 기록")
        chat_container = st.container()
        
        with chat_container:
            if st.session_state.chat_history:
                chat_html = '<div class="chat-container">'
                for message in st.session_state.chat_history[-5:]:  # 최근 5개만 표시
                    if message['role'] == 'user':
                        chat_html += f'<div class="user-message">👤 {message["content"]}</div>'
                    else:
                        chat_html += f'<div class="ai-message">🤖 {message["content"]}</div>'
                chat_html += '</div>'
                st.markdown(chat_html, unsafe_allow_html=True)
            else:
                st.info("아직 대화가 없습니다. 마이크 버튼을 눌러 시작해보세요!")
    
    # 컨트롤 패널
    with st.expander("⚙️ 고급 설정", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📝 칠판에 메모 추가"):
                custom_text = st.text_area("추가할 내용:")
                if custom_text and st.button("추가"):
                    st.session_state.blackboard_content += f"\n\n📝 메모: {custom_text}"
                    st.rerun()
        
        with col2:
            if st.button("🎯 특정 주제 요청"):
                topic = st.text_input("학습하고 싶은 주제:")
                if topic and st.button("요청"):
                    process_topic_request(topic)
                    st.rerun()
        
        with col3:
            if st.button("💾 수업 내용 저장"):
                save_lesson_content()

def process_voice_input():
    """음성 입력 처리"""
    try:
        # 실제로는 speech_to_text 함수 사용
        # 여기서는 시뮬레이션
        user_input = "안녕하세요, 전자기 유도에 대해 설명해주세요"  # 임시
        
        if user_input:
            # 사용자 메시지 추가
            st.session_state.chat_history.append({
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now()
            })
            
            # AI 응답 생성
            teacher = st.session_state.selected_teacher
            system_prompt = generate_system_prompt(teacher)
            
            ai_response = get_claude_response(user_input, system_prompt, st.session_state.chat_history)
            
            # AI 응답 추가
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now()
            })
            
            # 칠판에 내용 추가
            update_blackboard_with_response(ai_response)
            
            # 음성 재생 (설정이 켜져있다면)
            if teacher['voice_settings']['auto_play']:
                text_to_speech(ai_response, teacher['voice_settings'])
                
    except Exception as e:
        st.error(f"음성 처리 중 오류가 발생했습니다: {str(e)}")

def update_blackboard_with_response(response):
    """AI 응답을 칠판에 업데이트"""
    # 칠판 형식으로 변환
    blackboard_text = format_response_for_blackboard(response)
    
    # 기존 내용에 추가
    if st.session_state.blackboard_content:
        st.session_state.blackboard_content += f"\n\n{'='*50}\n\n{blackboard_text}"
    else:
        st.session_state.blackboard_content = blackboard_text

def format_response_for_blackboard(response):
    """응답을 칠판 형식으로 포맷팅"""
    # 제목 찾기
    lines = response.split('\n')
    formatted = ""
    
    for line in lines:
        line = line.strip()
        if not line:
            formatted += "\n"
            continue
            
        # 제목으로 보이는 라인 (짧고 중요해 보이는)
        if len(line) < 50 and ('법칙' in line or '공식' in line or '원리' in line):
            formatted += f"\n## {line}\n"
        # 수식으로 보이는 라인
        elif '=' in line and len(line) < 100:
            formatted += f"\n[BLUE]${line}$[/BLUE]\n"
        # 중요한 키워드 강조
        elif any(keyword in line for keyword in ['중요', '핵심', '주의', '기억']):
            formatted += f"\n[RED]**{line}**[/RED]\n"
        else:
            formatted += f"{line}\n"
    
    return formatted

def process_topic_request(topic):
    """특정 주제 요청 처리"""
    request = f"{topic}에 대해 상세히 설명해주세요. 칠판에 중요한 내용을 정리해서 써주세요."
    
    # 채팅 히스토리에 추가
    st.session_state.chat_history.append({
        'role': 'user',
        'content': request,
        'timestamp': datetime.now()
    })
    
    # AI 응답 생성
    teacher = st.session_state.selected_teacher
    system_prompt = generate_system_prompt(teacher)
    
    ai_response = get_claude_response(request, system_prompt, st.session_state.chat_history)
    
    # 응답 처리
    st.session_state.chat_history.append({
        'role': 'assistant',
        'content': ai_response,
        'timestamp': datetime.now()
    })
    
    update_blackboard_with_response(ai_response)

def save_lesson_content():
    """수업 내용 저장"""
    if st.session_state.blackboard_content:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        teacher_name = st.session_state.selected_teacher['name']
        
        # 파일로 저장하는 로직 (실제로는 클라우드 저장)
        content = f"# {teacher_name} 수업 내용\n날짜: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n{st.session_state.blackboard_content}"
        
        st.success(f"수업 내용이 저장되었습니다! (파일명: lesson_{timestamp}.md)")
        
        # 다운로드 버튼
        st.download_button(
            label="📥 수업 내용 다운로드",
            data=content,
            file_name=f"lesson_{teacher_name}_{timestamp}.md",
            mime="text/markdown"
        )

if __name__ == "__main__":
    main()
