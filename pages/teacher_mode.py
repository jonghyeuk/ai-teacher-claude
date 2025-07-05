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

# 🔊 새로운 TTS 함수 - 전광판 효과 포함
def play_immediate_tts(text, voice_settings=None):
    """확실히 작동하는 TTS with 전광판 효과"""
    if voice_settings is None:
        voice_settings = {'speed': 1.0, 'pitch': 1.0}
    
    # 텍스트 정리 (길이 제한 + 특수문자 제거)
    clean_text = text.replace('\n', ' ').replace('"', '').replace("'", '')
    clean_text = re.sub(r'\[.*?\]', '', clean_text)  # [RED] 같은 태그 제거
    clean_text = clean_text.replace('**', '').replace('*', '')[:400]  # 400자 제한
    
    speed = voice_settings.get('speed', 1.0)
    pitch = voice_settings.get('pitch', 1.0)
    
    # 전광판 효과가 있는 TTS HTML
    tts_html = f"""
    <div id="tts-container" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 15px; margin: 20px 0; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.3);">
        
        <!-- 전광판 헤더 -->
        <div id="led-display" style="background: #000; color: #00ff00; padding: 15px; border-radius: 10px; font-family: 'Courier New', monospace; font-size: 18px; margin-bottom: 20px; border: 3px solid #333; box-shadow: inset 0 0 10px rgba(0,255,0,0.3);">
            <div id="led-text">🔊 AI 선생님 준비 중...</div>
        </div>
        
        <!-- 음성 파형 애니메이션 -->
        <div id="voice-wave" style="display: none; margin: 20px 0;">
            <div style="display: flex; justify-content: center; align-items: center; height: 60px;">
                <div class="wave-bar" style="width: 4px; height: 10px; background: #00ff00; margin: 0 2px; animation: wave 1s infinite ease-in-out;"></div>
                <div class="wave-bar" style="width: 4px; height: 20px; background: #00ff00; margin: 0 2px; animation: wave 1s infinite ease-in-out 0.1s;"></div>
                <div class="wave-bar" style="width: 4px; height: 30px; background: #00ff00; margin: 0 2px; animation: wave 1s infinite ease-in-out 0.2s;"></div>
                <div class="wave-bar" style="width: 4px; height: 25px; background: #00ff00; margin: 0 2px; animation: wave 1s infinite ease-in-out 0.3s;"></div>
                <div class="wave-bar" style="width: 4px; height: 40px; background: #00ff00; margin: 0 2px; animation: wave 1s infinite ease-in-out 0.4s;"></div>
                <div class="wave-bar" style="width: 4px; height: 15px; background: #00ff00; margin: 0 2px; animation: wave 1s infinite ease-in-out 0.5s;"></div>
                <div class="wave-bar" style="width: 4px; height: 35px; background: #00ff00; margin: 0 2px; animation: wave 1s infinite ease-in-out 0.6s;"></div>
            </div>
        </div>
        
        <!-- 컨트롤 버튼들 -->
        <div style="margin: 20px 0;">
            <button onclick="playVoiceNow()" id="play-btn" style="padding: 15px 30px; background: #4CAF50; color: white; border: none; border-radius: 25px; font-weight: bold; cursor: pointer; margin: 10px; box-shadow: 0 5px 15px rgba(76, 175, 80, 0.4); font-size: 16px;">
                🔊 음성 재생
            </button>
            
            <button onclick="stopVoiceNow()" id="stop-btn" style="padding: 15px 30px; background: #f44336; color: white; border: none; border-radius: 25px; font-weight: bold; cursor: pointer; margin: 10px; box-shadow: 0 5px 15px rgba(244, 67, 54, 0.4); font-size: 16px;">
                🛑 정지
            </button>
            
            <button onclick="replayVoice()" id="replay-btn" style="padding: 15px 30px; background: #ff9800; color: white; border: none; border-radius: 25px; font-weight: bold; cursor: pointer; margin: 10px; box-shadow: 0 5px 15px rgba(255, 152, 0, 0.4); font-size: 16px;">
                🔄 다시 듣기
            </button>
        </div>
        
        <!-- 상태 정보 -->
        <div id="voice-status" style="margin-top: 15px; font-size: 14px; opacity: 0.9;">
            시스템 준비 중...
        </div>
        
        <!-- 텍스트 미리보기 -->
        <div id="text-preview" style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; margin-top: 20px; font-size: 14px; max-height: 100px; overflow-y: auto;">
            "{clean_text[:150]}{'...' if len(clean_text) > 150 else ''}"
        </div>
    </div>
    
    <style>
    @keyframes wave {{
        0%, 40%, 100% {{ transform: scaleY(0.4); }}
        20% {{ transform: scaleY(1.0); }}
    }}
    
    @keyframes blink {{
        0%, 50% {{ opacity: 1; }}
        51%, 100% {{ opacity: 0.3; }}
    }}
    
    @keyframes led-scroll {{
        0% {{ transform: translateX(100%); }}
        100% {{ transform: translateX(-100%); }}
    }}
    
    .led-scrolling {{
        animation: led-scroll 10s linear infinite;
    }}
    
    .voice-active {{
        animation: blink 0.8s infinite;
    }}
    </style>
    
    <script>
    // 전역 변수
    let ttsUtterance = null;
    let isVoicePlaying = false;
    let voiceSpeed = {speed};
    let voicePitch = {pitch};
    let fullText = `{clean_text}`;
    
    // LED 디스플레이 업데이트
    function updateLED(message, isScrolling = false) {{
        const ledText = document.getElementById('led-text');
        if (ledText) {{
            ledText.textContent = message;
            if (isScrolling) {{
                ledText.classList.add('led-scrolling');
            }} else {{
                ledText.classList.remove('led-scrolling');
            }}
        }}
    }}
    
    // 상태 업데이트
    function updateStatus(message) {{
        const status = document.getElementById('voice-status');
        if (status) status.textContent = message;
    }}
    
    // 음성 파형 표시/숨김
    function toggleWave(show) {{
        const wave = document.getElementById('voice-wave');
        if (wave) {{
            wave.style.display = show ? 'block' : 'none';
        }}
    }}
    
    // 컨테이너 효과
    function setContainerEffect(effect) {{
        const container = document.getElementById('tts-container');
        if (container) {{
            container.className = effect;
        }}
    }}
    
    // 음성 재생 함수
    function playVoiceNow() {{
        try {{
            console.log('TTS 재생 시작:', fullText.substring(0, 50));
            
            // 기존 음성 정지
            speechSynthesis.cancel();
            isVoicePlaying = false;
            
            // LED 업데이트
            updateLED('🔊 음성 재생 시작...', true);
            updateStatus('음성 엔진 초기화 중...');
            
            // 새 음성 생성
            ttsUtterance = new SpeechSynthesisUtterance(fullText);
            
            // 음성 설정
            ttsUtterance.lang = 'ko-KR';
            ttsUtterance.rate = voiceSpeed;
            ttsUtterance.pitch = voicePitch;
            ttsUtterance.volume = 1.0;
            
            // 이벤트 핸들러
            ttsUtterance.onstart = function() {{
                isVoicePlaying = true;
                updateLED('🎤 AI 선생님이 말하고 있습니다...', false);
                updateStatus(`🔊 재생 중... (속도: ${{Math.round(voiceSpeed * 100)}}%)`)
                toggleWave(true);
                setContainerEffect('voice-active');
                
                // 버튼 상태 변경
                const playBtn = document.getElementById('play-btn');
                if (playBtn) {{
                    playBtn.textContent = '🔊 재생 중...';
                    playBtn.style.background = '#FFC107';
                }}
                
                console.log('TTS 재생 시작됨');
            }};
            
            ttsUtterance.onend = function() {{
                isVoicePlaying = false;
                updateLED('✅ 음성 재생 완료!', false);
                updateStatus('재생 완료! 다시 들으시려면 "다시 듣기"를 눌러주세요.');
                toggleWave(false);
                setContainerEffect('');
                
                // 버튼 상태 복원
                const playBtn = document.getElementById('play-btn');
                if (playBtn) {{
                    playBtn.textContent = '🔊 음성 재생';
                    playBtn.style.background = '#4CAF50';
                }}
                
                console.log('TTS 재생 완료');
            }};
            
            ttsUtterance.onerror = function(event) {{
                isVoicePlaying = false;
                updateLED('❌ 음성 재생 오류', false);
                updateStatus('오류: ' + event.error + ' - 다시 시도해주세요.');
                toggleWave(false);
                setContainerEffect('');
                console.error('TTS 오류:', event.error, event);
            }};
            
            // 한국어 음성 찾기 및 설정
            const voices = speechSynthesis.getVoices();
            console.log('사용 가능한 음성 수:', voices.length);
            
            const koreanVoices = voices.filter(voice => 
                voice.lang && (
                    voice.lang.toLowerCase().includes('ko') || 
                    voice.name.toLowerCase().includes('korean') ||
                    voice.name.includes('한국')
                )
            );
            
            if (koreanVoices.length > 0) {{
                ttsUtterance.voice = koreanVoices[0];
                updateStatus('🎯 한국어 음성: ' + koreanVoices[0].name);
                console.log('한국어 음성 사용:', koreanVoices[0].name);
            }} else {{
                updateStatus('⚠️ 기본 음성 사용 (한국어 음성 없음)');
                console.log('한국어 음성 없음');
            }}
            
            // 음성 재생
            speechSynthesis.speak(ttsUtterance);
            
        }} catch (error) {{
            updateLED('❌ JavaScript 오류', false);
            updateStatus('오류: ' + error.message);
            console.error('TTS JavaScript 오류:', error);
        }}
    }}
    
    // 음성 정지
    function stopVoiceNow() {{
        speechSynthesis.cancel();
        isVoicePlaying = false;
        updateLED('🛑 음성 재생 정지됨', false);
        updateStatus('재생이 정지되었습니다.');
        toggleWave(false);
        setContainerEffect('');
        
        const playBtn = document.getElementById('play-btn');
        if (playBtn) {{
            playBtn.textContent = '🔊 음성 재생';
            playBtn.style.background = '#4CAF50';
        }}
        
        console.log('TTS 정지됨');
    }}
    
    // 다시 듣기
    function replayVoice() {{
        stopVoiceNow();
        setTimeout(playVoiceNow, 500);
    }}
    
    // 초기화 및 자동 재생
    function initializeTTS() {{
        const voices = speechSynthesis.getVoices();
        if (voices.length > 0) {{
            updateLED('🚀 시스템 준비 완료', false);
            updateStatus('음성 시스템 준비됨. 자동 재생 시작...');
            console.log('TTS 시스템 초기화 완료');
            
            // 2초 후 자동 재생
            setTimeout(function() {{
                if (!isVoicePlaying) {{
                    playVoiceNow();
                }}
            }}, 2000);
        }} else {{
            updateLED('⏳ 음성 엔진 로딩 중...', true);
            updateStatus('음성 엔진을 불러오는 중입니다...');
            console.log('음성 엔진 로딩 중');
        }}
    }}
    
    // 음성 목록 로드 대기
    if (speechSynthesis.getVoices().length > 0) {{
        initializeTTS();
    }} else {{
        speechSynthesis.onvoiceschanged = initializeTTS;
    }}
    
    // 5초 후에도 자동 재생 안되면 수동 안내
    setTimeout(function() {{
        if (!isVoicePlaying) {{
            updateLED('🔽 수동으로 "음성 재생" 버튼을 눌러주세요', false);
            updateStatus('자동 재생이 안 되면 수동으로 버튼을 눌러주세요.');
        }}
    }}, 5000);
    </script>
    """
    
    return tts_html

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
        st.session_state.blackboard_content = f"🎓 {teacher['name']}의 {teacher['subject']} 수업\n\n📚 교육 수준: {teacher['level']}\n\n수업을 시작할 준비가 되었습니다!\n아래에 질문을 입력해보세요."
    
    # 마이크 상태
    if 'is_recording' not in st.session_state:
        st.session_state.is_recording = False
    
    return teacher

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
            for key in ['chat_history', 'blackboard_content', 'is_recording']:
                if key in st.session_state:
                    del st.session_state[key]
            st.switch_page("app.py")
    
    with col3:
        if st.button("🗑️ 칠판 지우기"):
            st.session_state.blackboard_content = f"🎓 {teacher['name']}의 {teacher['subject']} 수업\n\n📚 교육 수준: {teacher['level']}\n\n칠판이 깨끗해졌습니다! 새로운 질문을 해보세요."
            st.rerun()
    
    # 메인 레이아웃
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 AI 칠판")
        
        # 칠판 내용 표시
        if st.session_state.blackboard_content:
            formatted_content = format_blackboard_text(st.session_state.blackboard_content)
            st.markdown(f'''
            <div class="blackboard">
                <h2>📚 AI 칠판</h2>
                <div>{formatted_content}</div>
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
        st.subheader("💬 질문하기")
        
        # 텍스트 입력
        user_text = st.text_area(
            "질문을 입력하세요:", 
            key="text_input", 
            placeholder="예: 전자기 유도에 대해 설명해주세요",
            height=100
        )
        
        if st.button("📝 질문 보내기", type="primary", use_container_width=True):
            if user_text.strip():
                process_text_input(user_text.strip())
                # 입력창 비우기
                st.session_state.text_input = ""
                st.rerun()
            else:
                st.warning("질문을 입력해주세요!")
        
        # 빠른 질문 버튼들
        st.subheader("🎯 빠른 질문")
        quick_questions = [
            "기본 개념 설명해주세요",
            "실생활 예시를 들어주세요", 
            "공식이나 법칙을 알려주세요",
            "연습 문제를 내주세요"
        ]
        
        for i, question in enumerate(quick_questions):
            if st.button(question, key=f"quick_{i}"):
                process_text_input(question)
                st.rerun()
        
        # 음성 설정
        st.subheader("🔊 음성 설정")
        with st.expander("설정 조절"):
            voice_speed = st.slider("음성 속도", 0.5, 2.0, teacher.get('voice_settings', {}).get('speed', 1.0), 0.1)
            voice_pitch = st.slider("음성 높이", 0.5, 2.0, teacher.get('voice_settings', {}).get('pitch', 1.0), 0.1)
            auto_play = st.checkbox("자동 재생", teacher.get('voice_settings', {}).get('auto_play', True))
        
        # 채팅 히스토리
        st.subheader("💬 대화 기록")
        if st.session_state.chat_history:
            chat_html = '<div class="chat-container">'
            for message in st.session_state.chat_history[-5:]:  # 최근 5개만 표시
                if message['role'] == 'user':
                    chat_html += f'<div class="user-message">👤 {message["content"]}</div>'
                else:
                    chat_html += f'<div class="ai-message">🤖 {message["content"][:100]}{"..." if len(message["content"]) > 100 else ""}</div>'
            chat_html += '</div>'
            st.markdown(chat_html, unsafe_allow_html=True)
        else:
            st.info("아직 대화가 없습니다. 위에서 질문을 입력해보세요!")
    
    # 하단 고급 기능들
    with st.expander("⚙️ 추가 기능", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("📝 칠판 메모")
            custom_text = st.text_area("추가할 내용:", key="memo_textarea")
            if st.button("📝 칠판에 메모 추가", key="add_memo_btn"):
                if custom_text:
                    st.session_state.blackboard_content += f"\n\n📝 메모: {custom_text}"
                    st.success("메모가 추가되었습니다!")
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

# 🔥 수정된 핵심 함수 - 확실한 TTS 포함
def process_text_input(user_input):
    """텍스트 입력 처리 - 확실한 TTS 포함"""
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
            with st.spinner("🤔 AI가 생각하고 있습니다..."):
                ai_response = get_claude_response(user_input, system_prompt, st.session_state.chat_history)
            
            if ai_response and "오류가 발생했습니다" not in ai_response:
                # AI 응답 추가
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': ai_response,
                    'timestamp': datetime.now()
                })
                
                # 칠판 업데이트
                update_blackboard_with_response(ai_response)
                
                # 🔊 TTS 재생 (자동 재생이 켜져있으면)
                if teacher.get('voice_settings', {}).get('auto_play', True):
                    st.success("✅ AI 응답 완료! 🔊 음성으로 들려드립니다...")
                    
                    # 전광판 효과가 있는 TTS 재생
                    voice_settings = {
                        'speed': teacher.get('voice_settings', {}).get('speed', 1.0),
                        'pitch': teacher.get('voice_settings', {}).get('pitch', 1.0)
                    }
                    
                    tts_html = play_immediate_tts(ai_response, voice_settings)
                    st.components.v1.html(tts_html, height=400)
                else:
                    st.success("✅ AI 응답 완료! (음성 재생 꺼짐)")
                
            else:
                st.error(f"❌ AI 응답 오류: {ai_response}")
                
    except Exception as e:
        st.error(f"처리 중 오류: {str(e)}")

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
    lines = response.split('\n')
    formatted = ""
    
    for line in lines:
        line = line.strip()
        if not line:
            formatted += "\n"
            continue
            
        # 제목으로 보이는 라인
        if len(line) < 50 and any(keyword in line for keyword in ['법칙', '공식', '원리', '정의', '개념']):
            formatted += f"\n## {line}\n"
        # 수식으로 보이는 라인
        elif '=' in line and len(line) < 100:
            formatted += f"\n**{line}**\n"
        # 중요한 키워드 강조
        elif any(keyword in line for keyword in ['중요', '핵심', '주의', '기억', '포인트']):
            formatted += f"\n**{line}**\n"
        else:
            formatted += f"{line}\n"
    
    return formatted

def process_topic_request(topic):
    """특정 주제 요청 처리"""
    request = f"{topic}에 대해 상세히 설명해주세요. 칠판에 중요한 내용을 정리해서 써주세요."
    process_text_input(request)

def save_lesson_content():
    """수업 내용 저장"""
    if st.session_state.blackboard_content:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        teacher_name = st.session_state.selected_teacher['name']
        
        content = f"# {teacher_name} 수업 내용\n날짜: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n{st.session_state.blackboard_content}"
        
        st.download_button(
            label="📥 수업 내용 다운로드",
            data=content,
            file_name=f"lesson_{teacher_name}_{timestamp}.md",
            mime="text/markdown"
        )
        st.success("수업 내용을 다운로드할 수 있습니다!")
    else:
        st.warning("저장할 수업 내용이 없습니다.")

if __name__ == "__main__":
    main()
