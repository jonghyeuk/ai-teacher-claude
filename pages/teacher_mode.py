import streamlit as st
import json
import time
from datetime import datetime
import re

# Claude API 함수들 직접 정의 (import 오류 방지)
def get_claude_response(user_message, system_prompt, chat_history):
    """Claude API 응답 생성"""
    try:
        from anthropic import Anthropic
        
        # API 키 가져오기
        api_key = st.secrets.get('ANTHROPIC_API_KEY')
        if not api_key:
            return "API 키가 설정되지 않았습니다. Streamlit secrets에 ANTHROPIC_API_KEY를 설정해주세요."
        
        client = Anthropic(api_key=api_key)
        
        # 메시지 준비
        messages = []
        for msg in chat_history[-5:]:  # 최근 5개만
            if msg['role'] in ['user', 'assistant']:
                messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })
        
        # 현재 메시지 추가
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Claude API 호출
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1000,
            temperature=0.7,
            system=system_prompt,
            messages=messages
        )
        
        return response.content[0].text
        
    except Exception as e:
        return f"오류가 발생했습니다: {str(e)}"

def generate_system_prompt(teacher_config):
    """시스템 프롬프트 생성"""
    personality = teacher_config.get('personality', {})
    
    # 자연스러운 말투 수준에 따른 프롬프트 조정
    natural_speech_level = personality.get('natural_speech', 70)
    
    natural_speech_instruction = ""
    if natural_speech_level > 80:
        natural_speech_instruction = """
당신의 말투는 매우 자연스럽고 인간적입니다. 다음과 같이 말하세요:
- "음...", "그러니까", "아 그리고" 같은 자연스러운 추임새 사용
- 때로는 말을 끊어서 하거나 다시 정리해서 설명
- "어떻게 보면", "사실은", "잠깐만" 같은 표현 자주 사용
- 학생에게 "그죠?", "알겠어요?", "이해되나요?" 같은 확인 질문
"""
    elif natural_speech_level > 50:
        natural_speech_instruction = """
자연스럽게 말하되 적당히 정돈된 방식으로 설명하세요.
가끔 "음", "그런데" 같은 표현을 사용하고, 학생의 이해를 확인해주세요.
"""
    else:
        natural_speech_instruction = "명확하고 정돈된 방식으로 설명해주세요."
    
    return f"""당신은 {teacher_config['name']}이라는 이름의 AI 튜터입니다. 
{teacher_config['subject']} 분야의 전문가이며, {teacher_config['level']} 수준의 학생들을 가르칩니다.

당신의 성격 특성:
- 친근함: {personality.get('friendliness', 70)}/100
- 유머 수준: {personality.get('humor_level', 30)}/100
- 격려 수준: {personality.get('encouragement', 80)}/100
- 설명 상세도: {personality.get('explanation_detail', 70)}/100
- 상호작용 빈도: {personality.get('interaction_frequency', 60)}/100
- 이론-실습 균형: {personality.get('theory_vs_practice', 50)}/100 (0=이론중심, 100=실습중심)
- 안전 강조: {personality.get('safety_emphasis', 90)}/100
- 적응성: {personality.get('adaptability', 75)}/100
- 응답 속도: {personality.get('response_speed', 60)}/100
- 어휘 수준: {personality.get('vocabulary_level', 50)}/100

{natural_speech_instruction}

칠판에 쓸 중요한 내용이 있다면 **중요내용**으로 강조해주세요.
수식이나 공식은 $수식$ 형태로 표현하고, 특히 강조할 부분은 [RED]빨간색[/RED], [BLUE]파란색[/BLUE], [GREEN]초록색[/GREEN]으로 표시해주세요.

학생들에게 도움이 되는 교육적이고 참여도 높은 답변을 해주세요."""

# 음성 함수들 - 브라우저 TTS 사용
def text_to_speech(text, voice_settings):
    """텍스트를 음성으로 변환 - 브라우저 TTS 사용"""
    try:
        # 텍스트 정리 (특수문자 제거)
        clean_text = text.replace('"', '').replace("'", "").replace('\n', ' ')
        clean_text = clean_text.replace('**', '').replace('*', '')
        clean_text = re.sub(r'\[.*?\]', '', clean_text)  # 색상 태그 제거
        
        # 음성 설정
        speed = voice_settings.get('speed', 1.0)
        pitch = voice_settings.get('pitch', 1.0)
        
        # 브라우저 TTS JavaScript 코드
        tts_html = f"""
        <script>
        function speakText() {{
            // 기존 음성 정지
            speechSynthesis.cancel();
            
            const text = `{clean_text}`;
            const utterance = new SpeechSynthesisUtterance(text);
            
            // 한국어 설정
            utterance.lang = 'ko-KR';
            utterance.rate = {speed};
            utterance.pitch = {pitch};
            utterance.volume = 0.8;
            
            // 한국어 음성 찾기
            const voices = speechSynthesis.getVoices();
            const koreanVoice = voices.find(voice => 
                voice.lang.includes('ko') || 
                voice.name.includes('Korean') ||
                voice.name.includes('한국')
            );
            
            if (koreanVoice) {{
                utterance.voice = koreanVoice;
                console.log('한국어 음성 사용:', koreanVoice.name);
            }} else {{
                console.log('기본 음성 사용');
            }}
            
            // 이벤트 핸들러
            utterance.onstart = function() {{
                console.log('음성 재생 시작');
            }};
            
            utterance.onend = function() {{
                console.log('음성 재생 완료');
            }};
            
            utterance.onerror = function(event) {{
                console.error('음성 재생 오류:', event.error);
            }};
            
            // 음성 재생
            speechSynthesis.speak(utterance);
        }}
        
        // 음성 목록이 로드되면 실행
        if (speechSynthesis.getVoices().length > 0) {{
            speakText();
        }} else {{
            speechSynthesis.onvoiceschanged = function() {{
                speakText();
            }};
        }}
        </script>
        
        <div style="padding: 10px; background: #e8f5e8; border-radius: 5px; margin: 5px 0;">
            🔊 음성 재생 중: "{clean_text[:50]}{'...' if len(clean_text) > 50 else ''}"
        </div>
        """
        
        # Streamlit에서 HTML 렌더링
        st.components.v1.html(tts_html, height=80)
        
    except Exception as e:
        st.warning(f"음성 재생 오류: {str(e)}")
        st.info("브라우저에서 음성 재생을 허용해주세요.")

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
        background: linear-gradient(135deg, #1a3d3a 0%, #2d5652 50%, #1a3d3a 100%);
        color: #ffffff;
        padding: 30px;
        border-radius: 15px;
        font-family: 'Georgia', serif;
        font-size: 18px;
        line-height: 1.8;
        min-height: 400px;
        border: 8px solid #8B4513;
        box-shadow: 
            inset 0 0 30px rgba(0,0,0,0.3),
            0 10px 20px rgba(0,0,0,0.2);
        overflow-y: auto;
        white-space: pre-wrap;
        position: relative;
    }
    
    .blackboard::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: 
            radial-gradient(circle at 20% 30%, rgba(255,255,255,0.1) 1px, transparent 1px),
            radial-gradient(circle at 60% 70%, rgba(255,255,255,0.05) 1px, transparent 1px),
            radial-gradient(circle at 80% 20%, rgba(255,255,255,0.08) 1px, transparent 1px);
        pointer-events: none;
    }
    
    .blackboard h1, .blackboard h2, .blackboard h3 {
        color: #FFD700;
        text-decoration: underline;
        margin: 25px 0 15px 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    
    .blackboard .important {
        background: #FFD700;
        color: #000;
        padding: 3px 8px;
        border-radius: 5px;
        font-weight: bold;
        box-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .blackboard .formula {
        background: linear-gradient(135deg, #4169E1, #6495ED);
        color: white;
        padding: 15px;
        border-radius: 10px;
        font-size: 20px;
        text-align: center;
        margin: 15px 0;
        border-left: 6px solid #FFD700;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        font-family: 'Courier New', monospace;
    }
    
    .blackboard .highlight-red {
        color: #FF6B6B;
        font-weight: bold;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }
    
    .blackboard .highlight-blue {
        color: #4DABF7;
        font-weight: bold;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }
    
    .blackboard .highlight-green {
        color: #51CF66;
        font-weight: bold;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }
    
    .blackboard .circle {
        border: 3px solid #FFD700;
        border-radius: 50%;
        padding: 8px 15px;
        display: inline-block;
        margin: 5px;
        background: rgba(255, 215, 0, 0.1);
        box-shadow: 0 3px 8px rgba(0,0,0,0.3);
    }
    
    .typing-text {
        display: inline;
    }
    
    .cursor {
        display: inline-block;
        background-color: #FFD700;
        width: 3px;
        animation: blink 1s infinite;
    }
    
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0; }
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
        
        # 칠판 내용 표시
        if st.session_state.blackboard_content:
            # 단순한 칠판 표시
            st.markdown(f'''
            <div class="blackboard">
                <h2>📚 AI 칠판</h2>
                <div>{format_blackboard_text(st.session_state.blackboard_content)}</div>
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown('''
            <div class="blackboard">
                <h2>📚 AI 칠판</h2>
                <div style="text-align: center; color: #ccc; margin-top: 50px;">
                    칠판이 비어있습니다.<br>
                    질문을 입력하면 AI가 여기에 설명을 써드립니다.
                </div>
            </div>
            ''', unsafe_allow_html=True)
    
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
        
        # 텍스트 입력 추가 (테스트용)
        st.subheader("💬 텍스트 입력")
        user_text = st.text_input("질문을 입력하세요:", key="text_input", placeholder="예: 전자기 유도에 대해 설명해주세요")
        
        if st.button("📝 텍스트 전송", key="send_text"):
            if user_text:
                process_text_input(user_text)
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
            st.subheader("📝 칠판 메모")
            custom_text = st.text_area("추가할 내용:", key="memo_textarea")
            if st.button("📝 칠판에 메모 추가", key="add_memo_btn"):
                if custom_text:
                    st.session_state.blackboard_content += f"\n\n📝 메모: {custom_text}"
                    st.rerun()
        
        with col2:
            st.subheader("🎯 주제 요청")
            topic = st.text_input("학습하고 싶은 주제:", key="topic_input")
            if st.button("🎯 특정 주제 요청", key="request_topic_btn"):
                if topic:
                    process_topic_request(topic)
                    st.rerun()
        
        with col3:
            st.subheader("💾 수업 저장")
            if st.button("💾 수업 내용 저장", key="save_lesson_btn"):
                save_lesson_content()

def process_text_input(user_input):
    """텍스트 입력 처리 - 안전한 방식"""
    try:
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
            
            # Claude API 호출
            try:
                st.info("🤔 AI가 생각하고 있습니다...")
                ai_response = get_claude_response(user_input, system_prompt, st.session_state.chat_history)
                
                if ai_response:
                    # AI 응답 추가
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': ai_response,
                        'timestamp': datetime.now()
                    })
                    
                    # ✅ 안전한 칠판 업데이트 + TTS
                    if teacher.get('voice_settings', {}).get('auto_play', True):
                        st.success("✅ AI 응답 완료! 🔊 음성으로 읽어드립니다...")
                        update_blackboard_with_response(ai_response)
                        
                        # TTS 재생
                        text_to_speech(ai_response, teacher.get('voice_settings', {}))
                    else:
                        # 음성 없이 칠판만 업데이트
                        blackboard_text = format_response_for_blackboard(ai_response)
                        if st.session_state.blackboard_content:
                            st.session_state.blackboard_content += f"\n\n{'='*50}\n\n{blackboard_text}"
                        else:
                            st.session_state.blackboard_content = blackboard_text
                        st.success("✅ AI 응답 완료! (음성 재생 꺼짐)")
                        
                    # 페이지 자동 새로고침으로 칠판 업데이트
                    st.rerun()
                else:
                    st.error("❌ AI 응답이 비어있습니다.")
                    
            except Exception as e:
                st.error(f"❌ Claude API 호출 오류: {str(e)}")
                st.exception(e)
                
    except Exception as e:
        st.error(f"텍스트 처리 중 오류가 발생했습니다: {str(e)}")
        st.exception(e)

def process_voice_input():
    """음성 입력 처리"""
    # 음성은 나중에 구현하고, 일단 테스트 메시지로
    test_message = "안녕하세요, 전자기 유도에 대해 설명해주세요"
    process_text_input(test_message)

def update_blackboard_with_response(response):
    """AI 응답을 칠판에 안전하게 표시 + 타이핑 애니메이션"""
    # 칠판 형식으로 변환
    blackboard_text = format_response_for_blackboard(response)
    
    # 기존 내용에 추가
    if st.session_state.blackboard_content:
        st.session_state.blackboard_content += f"\n\n{'='*50}\n\n{blackboard_text}"
    else:
        st.session_state.blackboard_content = blackboard_text
    
    # 타이핑 애니메이션 효과 HTML
    create_typing_animation(response)

def create_typing_animation(response):
    """타이핑 애니메이션 HTML 생성"""
    # 텍스트 정리
    clean_text = response.replace('"', '').replace("'", '').replace('\n', ' ')[:200]
    
    typing_html = f"""
    <div style="background: #e8f5e8; padding: 15px; border-radius: 10px; margin: 10px 0;">
        <h4>🎓 AI 튜터가 칠판에 쓰고 있습니다...</h4>
        <div id="typing-status">타이핑 중...</div>
    </div>
    
    <script>
    // 타이핑 애니메이션 시뮬레이션
    let dots = '';
    let counter = 0;
    const maxDots = 3;
    const typingSpeed = 300; // 밀리초
    
    function animateTyping() {{
        counter++;
        dots += '.';
        if (dots.length > maxDots) {{
            dots = '';
        }}
        
        const statusElement = document.getElementById('typing-status');
        if (statusElement) {{
            statusElement.innerHTML = `✍️ 칠판에 쓰는 중${{dots}}`;
        }}
        
        // 3초 후에 완료 메시지
        if (counter >= 10) {{
            if (statusElement) {{
                statusElement.innerHTML = '✅ 완료! 칠판을 확인하세요.';
            }}
            return;
        }}
        
        setTimeout(animateTyping, typingSpeed);
    }}
    
    // 애니메이션 시작
    setTimeout(animateTyping, 500);
    </script>
    """
    
    # Streamlit에 안전하게 표시
    st.components.v1.html(typing_html, height=100)

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
        if len(line) < 50 and ('법칙' in line or '공식' in line or '원리' in line or '정의' in line):
            formatted += f"\n## {line}\n"
        # 수식으로 보이는 라인
        elif '=' in line and len(line) < 100:
            formatted += f"\n[BLUE]${line}$[/BLUE]\n"
        # 중요한 키워드 강조
        elif any(keyword in line for keyword in ['중요', '핵심', '주의', '기억', '포인트']):
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
