import streamlit as st
import json
import time
from datetime import datetime
import re
import html

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
    """시스템 프롬프트 생성 - 칠판 적극 활용 버전"""
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

{natural_speech_instruction}

🎯 **칠판 사용 지침 (매우 중요!)** 
칠판에는 반드시 다음 형식으로만 써주세요:

1. **제목**: ## 주제명
2. **정의**: **개념 = 설명**  
3. **공식**: F = ma (등식 형태)
4. **중요사항**: <RED>중요한 내용</RED>
5. **보충설명**: <BLUE>추가 정보</BLUE>
6. **강조**: <U>밑줄 강조</U>

⚠️ 주의사항:
- 반드시 위의 태그 형태만 사용하세요: <RED></RED>, <BLUE></BLUE>, <U></U>
- 복잡한 HTML이나 CSS는 사용하지 마세요
- 색상은 흰색(기본), 빨간색, 파란색, 밑줄만 사용하세요

예시:
## 뉴턴의 법칙
**정의**: 물체의 운동을 설명하는 법칙
F = ma
<RED>중요: 힘과 질량의 관계</RED>
<BLUE>예: 자동차의 가속</BLUE>
<U>결론: 모든 운동의 기초</U>

학생이 이해하기 쉽게 단계별로 차근차근 설명해주세요."""

def format_blackboard_text(text):
    """칠판 텍스트 포맷팅 - 안전한 색상 처리"""
    # 제목 포맷팅
    text = re.sub(r'##\s*([^#\n]+)', r'<h2 class="title">\1</h2>', text)
    
    # 색상 태그 변환 (안전하게)
    text = re.sub(r'<RED>([^<]+)</RED>', r'<span class="red">\1</span>', text)
    text = re.sub(r'<BLUE>([^<]+)</BLUE>', r'<span class="blue">\1</span>', text)
    text = re.sub(r'<U>([^<]+)</U>', r'<span class="underline">\1</span>', text)
    
    # 강조 텍스트
    text = re.sub(r'\*\*([^*]+)\*\*', r'<span class="bold">\1</span>', text)
    
    # 공식 감지
    if re.search(r'[A-Za-z]\s*=\s*[A-Za-z0-9]', text):
        text = re.sub(r'([A-Za-z]\s*=\s*[^<\n]+)', r'<div class="formula">\1</div>', text)
    
    return text

# 🎬 완전한 칠판 타이핑 + TTS 시스템 - 안전 버전
def create_typing_blackboard_system(text, voice_settings=None):
    """칠판 타이핑 + 음성 재생 통합 시스템 - 완전 안전 버전"""
    if voice_settings is None:
        voice_settings = {'speed': 1.0, 'pitch': 1.0}
    
    # 텍스트 안전 처리 (매우 엄격하게)
    clean_text = text.replace('\n', ' ').replace('"', "'").replace("'", "`")
    clean_text = re.sub(r'<[^>]+>', '', clean_text)  # 모든 HTML 태그 제거
    clean_text = re.sub(r'[<>{}]', '', clean_text)  # < > { } 문자 제거
    clean_text = clean_text.replace('**', '').replace('*', '')
    clean_text = re.sub(r'[^\w\s가-힣.,!?=\-+*/():ㄱ-ㅎ]', '', clean_text)  # 안전한 문자만 유지
    clean_text = clean_text[:500]  # 500자 제한
    
    # 표시용 텍스트도 안전하게 처리
    display_text = text.replace("'", "`").replace('"', "`").replace('\\', " ")
    display_text = re.sub(r'[<>{}]', '', display_text)  # < > { } 완전 제거
    display_text = display_text.replace('\n', ' ')  # 줄바꿈을 공백으로
    display_text = re.sub(r'[^\w\s가-힣.,!?=\-+*/():*#>REDBLAU]', '', display_text)  # 매우 제한적
    display_text = display_text[:800]  # 표시용은 800자까지
    
    speed = voice_settings.get('speed', 1.0)
    pitch = voice_settings.get('pitch', 1.0)
    
    # 안전한 변수 전달을 위한 처리
    safe_display_text = html.escape(display_text).replace("'", "`").replace('"', "`")
    safe_voice_text = html.escape(clean_text).replace("'", "`").replace('"', "`")
    
    html_system = f"""
    <div id="typing-tts-system" style="width: 100%; background: #1a1a1a; border-radius: 15px; padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
        
        <!-- 🔊 TTS 컨트롤 패널 -->
        <div id="tts-panel" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; text-align: center;">
            
            <!-- LED 디스플레이 -->
            <div id="led-display" style="background: #000; color: #00ff00; padding: 15px; border-radius: 8px; font-family: 'Courier New', monospace; font-size: 16px; margin-bottom: 15px; border: 2px solid #333;">
                <div id="led-text">🎤 AI 선생님 준비 중...</div>
            </div>
            
            <!-- 이퀄라이저 (음성 파형) -->
            <div id="equalizer" style="display: none; margin: 15px 0; height: 60px; display: flex; justify-content: center; align-items: end;">
                <div class="eq-bar" style="width: 6px; height: 10px; background: #00ff00; margin: 0 2px; border-radius: 3px; animation: eq-bounce 0.6s ease-in-out infinite;"></div>
                <div class="eq-bar" style="width: 6px; height: 25px; background: #00ff00; margin: 0 2px; border-radius: 3px; animation: eq-bounce 0.6s ease-in-out infinite 0.1s;"></div>
                <div class="eq-bar" style="width: 6px; height: 35px; background: #00ff00; margin: 0 2px; border-radius: 3px; animation: eq-bounce 0.6s ease-in-out infinite 0.2s;"></div>
                <div class="eq-bar" style="width: 6px; height: 20px; background: #00ff00; margin: 0 2px; border-radius: 3px; animation: eq-bounce 0.6s ease-in-out infinite 0.3s;"></div>
                <div class="eq-bar" style="width: 6px; height: 40px; background: #00ff00; margin: 0 2px; border-radius: 3px; animation: eq-bounce 0.6s ease-in-out infinite 0.4s;"></div>
                <div class="eq-bar" style="width: 6px; height: 15px; background: #00ff00; margin: 0 2px; border-radius: 3px; animation: eq-bounce 0.6s ease-in-out infinite 0.5s;"></div>
                <div class="eq-bar" style="width: 6px; height: 30px; background: #00ff00; margin: 0 2px; border-radius: 3px; animation: eq-bounce 0.6s ease-in-out infinite 0.6s;"></div>
                <div class="eq-bar" style="width: 6px; height: 45px; background: #00ff00; margin: 0 2px; border-radius: 3px; animation: eq-bounce 0.6s ease-in-out infinite 0.7s;"></div>
            </div>
            
            <!-- 컨트롤 버튼 -->
            <div style="margin: 15px 0;">
                <button onclick="startTeaching()" id="start-btn" style="padding: 12px 25px; background: #4CAF50; color: white; border: none; border-radius: 20px; font-weight: bold; cursor: pointer; margin: 5px; font-size: 14px;">
                    🎬 수업 시작
                </button>
                <button onclick="stopTeaching()" id="stop-btn" style="padding: 12px 25px; background: #f44336; color: white; border: none; border-radius: 20px; font-weight: bold; cursor: pointer; margin: 5px; font-size: 14px;">
                    🛑 정지
                </button>
                <button onclick="replayTeaching()" id="replay-btn" style="padding: 12px 25px; background: #ff9800; color: white; border: none; border-radius: 20px; font-weight: bold; cursor: pointer; margin: 5px; font-size: 14px;">
                    🔄 다시보기
                </button>
            </div>
            
            <div id="voice-status" style="font-size: 12px; opacity: 0.9;">시스템 준비 중...</div>
        </div>
        
        <!-- 📝 칠판 영역 (개선된 폰트) -->
        <div id="blackboard-container" style="background: linear-gradient(135deg, #1a3d3a 0%, #2d5652 50%, #1a3d3a 100%); border: 8px solid #8B4513; border-radius: 15px; padding: 30px; min-height: 600px; max-height: 600px; overflow-y: auto; position: relative;">
            
            <!-- 칠판 제목 -->
            <div style="text-align: center; color: #FFD700; font-size: 24px; font-weight: bold; margin-bottom: 30px; border-bottom: 2px solid #FFD700; padding-bottom: 10px; font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;">
                📚 AI 튜터 칠판
            </div>
            
            <!-- 타이핑되는 내용 -->
            <div id="blackboard-content" style="color: white; font-size: 18px; line-height: 1.8; font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif; font-weight: 400; letter-spacing: 0.5px;">
                <div style="text-align: center; color: #ccc; margin-top: 100px; font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;">
                    수업을 시작하려면 "🎬 수업 시작" 버튼을 눌러주세요
                </div>
            </div>
            
            <!-- 타이핑 커서 -->
            <span id="typing-cursor" style="color: #FFD700; font-size: 20px; animation: cursor-blink 1s infinite; display: none;">|</span>
        </div>
    </div>

    <style>
    @keyframes eq-bounce {{
        0%, 100% {{ height: 10px; }}
        50% {{ height: 40px; }}
    }}
    
    @keyframes cursor-blink {{
        0%, 50% {{ opacity: 1; }}
        51%, 100% {{ opacity: 0; }}
    }}
    
    @keyframes led-scroll {{
        0% {{ transform: translateX(100%); }}
        100% {{ transform: translateX(-100%); }}
    }}
    
    .title {{
        color: #FFD700 !important;
        text-decoration: underline;
        font-size: 22px;
        font-weight: bold;
        margin: 20px 0;
        display: block;
    }}
    
    .red {{
        color: #FF6B6B !important;
        font-weight: bold;
    }}
    
    .blue {{
        color: #4DABF7 !important;
        font-weight: bold;
    }}
    
    .underline {{
        text-decoration: underline;
        font-weight: bold;
    }}
    
    .bold {{
        font-weight: bold;
        color: #FFD700;
    }}
    
    .formula {{
        background: rgba(65, 105, 225, 0.3);
        color: white;
        padding: 10px;
        border-radius: 8px;
        border-left: 4px solid #FFD700;
        margin: 15px 0;
        font-family: 'Courier New', monospace;
        font-size: 20px;
        text-align: center;
    }}
    
    #blackboard-container::-webkit-scrollbar {{
        width: 12px;
    }}
    
    #blackboard-container::-webkit-scrollbar-track {{
        background: rgba(139, 69, 19, 0.3);
        border-radius: 6px;
    }}
    
    #blackboard-container::-webkit-scrollbar-thumb {{
        background: rgba(255, 215, 0, 0.6);
        border-radius: 6px;
    }}
    </style>
    
    <script>
    // 전역 변수 (완전 안전 처리)
    let isTeaching = false;
    let typingInterval = null;
    let ttsUtterance = null;
    let currentText = `{safe_display_text}`;
    let voiceSpeed = {speed};
    let voicePitch = {pitch};
    let speechText = `{safe_voice_text}`;
    
    // LED 업데이트
    function updateLED(message) {{
        const led = document.getElementById('led-text');
        if (led) led.textContent = message;
    }}
    
    // 상태 업데이트
    function updateStatus(message) {{
        const status = document.getElementById('voice-status');
        if (status) status.textContent = message;
    }}
    
    // 이퀄라이저 표시/숨김
    function toggleEqualizer(show) {{
        const eq = document.getElementById('equalizer');
        if (eq) eq.style.display = show ? 'flex' : 'none';
    }}
    
    // 칠판 자동 스크롤
    function scrollToBottom() {{
        const container = document.getElementById('blackboard-container');
        if (container) {{
            container.scrollTop = container.scrollHeight;
        }}
    }}
    
    // 타이핑 효과
    function startTyping() {{
        const content = document.getElementById('blackboard-content');
        const cursor = document.getElementById('typing-cursor');
        
        if (!content || !cursor) return;
        
        content.innerHTML = '';
        cursor.style.display = 'inline';
        
        let index = 0;
        const formattedText = formatBlackboardText(currentText);
        
        updateLED('✍️ 칠판에 쓰는 중...');
        updateStatus('타이핑 중...');
        
        typingInterval = setInterval(() => {{
            if (index < formattedText.length) {{
                content.innerHTML = formattedText.substring(0, index + 1);
                index++;
                
                // 주기적으로 스크롤
                if (index % 20 === 0) {{
                    scrollToBottom();
                }}
            }} else {{
                clearInterval(typingInterval);
                cursor.style.display = 'none';
                updateLED('✅ 칠판 작성 완료');
                updateStatus('타이핑 완료! 음성 재생 중...');
                scrollToBottom();
                
                // 타이핑 완료 후 음성 시작
                setTimeout(startVoice, 500);
            }}
        }}, 50); // 50ms 간격으로 타이핑
    }}
    
    // 칠판 텍스트 포맷팅 (안전한 버전)
    function formatBlackboardText(text) {{
        // 제목 포맷팅
        text = text.replace(/##\\s*([^#\\n]+)/g, '<h2 class="title">$1</h2>');
        
        // 색상 태그 (안전하게)
        text = text.replace(/RED>([^R]+)RED>/g, '<span class="red">$1</span>');
        text = text.replace(/BLUE>([^B]+)BLUE>/g, '<span class="blue">$1</span>');
        text = text.replace(/U>([^U]+)U>/g, '<span class="underline">$1</span>');
        
        // 강조
        text = text.replace(/\\*\\*([^*]+)\\*\\*/g, '<span class="bold">$1</span>');
        
        // 공식
        text = text.replace(/([A-Za-z]\\s*=\\s*[^<\\n]+)/g, '<div class="formula">$1</div>');
        
        // 줄바꿈
        text = text.replace(/\\n/g, '<br>');
        
        return text;
    }}
    
    // 음성 재생
    function startVoice() {{
        try {{
            // 기존 음성 정지
            speechSynthesis.cancel();
            
            updateLED('🎤 AI 선생님이 설명하는 중...');
            updateStatus('음성 재생 중...');
            toggleEqualizer(true);
            
            // 새 음성 생성
            ttsUtterance = new SpeechSynthesisUtterance(speechText);
            ttsUtterance.lang = 'ko-KR';
            ttsUtterance.rate = voiceSpeed;
            ttsUtterance.pitch = voicePitch;
            ttsUtterance.volume = 1.0;
            
            // 한국어 음성 찾기
            const voices = speechSynthesis.getVoices();
            const koreanVoice = voices.find(voice => 
                voice.lang && voice.lang.toLowerCase().includes('ko')
            );
            if (koreanVoice) {{
                ttsUtterance.voice = koreanVoice;
            }}
            
            // 이벤트 핸들러
            ttsUtterance.onstart = function() {{
                console.log('음성 재생 시작');
                updateStatus('🔊 음성 재생 중... (속도: ' + Math.round(voiceSpeed * 100) + '%)');
            }};
            
            ttsUtterance.onend = function() {{
                updateLED('✅ 수업 완료!');
                updateStatus('수업이 끝났습니다. 다시 보시려면 "다시보기"를 눌러주세요.');
                toggleEqualizer(false);
                isTeaching = false;
                console.log('음성 재생 완료');
            }};
            
            ttsUtterance.onerror = function(event) {{
                updateLED('❌ 음성 오류');
                updateStatus('음성 재생 중 오류가 발생했습니다: ' + event.error);
                toggleEqualizer(false);
                isTeaching = false;
                console.error('TTS 오류:', event.error);
            }};
            
            // 음성 재생
            speechSynthesis.speak(ttsUtterance);
            
        }} catch (error) {{
            updateLED('❌ 시스템 오류');
            updateStatus('오류: ' + error.message);
            toggleEqualizer(false);
            console.error('음성 시스템 오류:', error);
        }}
    }}
    
    // 수업 시작
    function startTeaching() {{
        if (isTeaching) return;
        
        isTeaching = true;
        updateLED('🚀 수업을 시작합니다!');
        updateStatus('수업 준비 중...');
        
        // 버튼 상태 변경
        const startBtn = document.getElementById('start-btn');
        if (startBtn) {{
            startBtn.textContent = '⏳ 진행 중...';
            startBtn.style.background = '#FFC107';
        }}
        
        // 타이핑 시작
        setTimeout(startTyping, 1000);
    }}
    
    // 수업 정지
    function stopTeaching() {{
        isTeaching = false;
        
        // 타이핑 정지
        if (typingInterval) {{
            clearInterval(typingInterval);
            typingInterval = null;
        }}
        
        // 음성 정지
        speechSynthesis.cancel();
        
        // UI 업데이트
        updateLED('🛑 수업이 중단되었습니다');
        updateStatus('정지됨');
        toggleEqualizer(false);
        
        // 커서 숨김
        const cursor = document.getElementById('typing-cursor');
        if (cursor) cursor.style.display = 'none';
        
        // 버튼 복원
        const startBtn = document.getElementById('start-btn');
        if (startBtn) {{
            startBtn.textContent = '🎬 수업 시작';
            startBtn.style.background = '#4CAF50';
        }}
        
        console.log('수업 중단됨');
    }}
    
    // 다시보기
    function replayTeaching() {{
        stopTeaching();
        setTimeout(startTeaching, 1000);
    }}
    
    // 초기화
    function initializeSystem() {{
        updateLED('🚀 시스템 준비 완료');
        updateStatus('준비됨 - "수업 시작" 버튼을 눌러주세요');
        console.log('AI 튜터 시스템 초기화 완료');
        
        // 음성 엔진 대기
        if (speechSynthesis.getVoices().length === 0) {{
            speechSynthesis.onvoiceschanged = function() {{
                console.log('음성 엔진 로드 완료');
                updateStatus('음성 엔진 준비됨 - 수업을 시작할 수 있습니다');
            }};
        }}
    }}
    
    // 시스템 시작
    setTimeout(initializeSystem, 1000);
    </script>
    """
    
    return html_system

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
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
    }
    
    .main-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 20px;
    }
    
    .control-panel {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin: 20px 0;
    }
    
    .quick-btn {
        width: 100%;
        padding: 12px;
        margin: 5px 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .quick-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
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
    
    # 현재 설명 내용
    if 'current_explanation' not in st.session_state:
        st.session_state.current_explanation = ""
    
    return teacher

def main():
    teacher = initialize_teacher()
    if not teacher:
        return
    
    # 헤더
    st.markdown(f"""
    <div class="teacher-header">
        <h1>👨‍🏫 {teacher['name']} AI 튜터</h1>
        <p>📚 {teacher['subject']} | 🎯 {teacher['level']} 수준</p>
        <p>💬 실시간 타이핑 + 음성 설명</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 메인 레이아웃
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # 칠판 + TTS 시스템 표시
        if st.session_state.current_explanation:
            voice_settings = {
                'speed': teacher.get('voice_settings', {}).get('speed', 1.0),
                'pitch': teacher.get('voice_settings', {}).get('pitch', 1.0)
            }
            
            typing_system = create_typing_blackboard_system(
                st.session_state.current_explanation, 
                voice_settings
            )
            st.components.v1.html(typing_system, height=800)
        else:
            # 빈 칠판
            empty_system = create_typing_blackboard_system("아직 수업 내용이 없습니다. 오른쪽에서 질문을 선택하거나 입력해주세요.", {'speed': 1.0, 'pitch': 1.0})
            st.components.v1.html(empty_system, height=800)
    
    with col2:
        # 컨트롤 패널
        st.markdown('<div class="control-panel">', unsafe_allow_html=True)
        
        # 메인 버튼들
        if st.button("🏠 메인으로", key="home_btn"):
            # 세션 클리어
            for key in ['chat_history', 'current_explanation']:
                if key in st.session_state:
                    del st.session_state[key]
            st.switch_page("app.py")
        
        if st.button("🗑️ 칠판 지우기", key="clear_btn"):
            st.session_state.current_explanation = ""
            st.rerun()
        
        st.markdown("---")
        
        # 빠른 질문 버튼들
        st.subheader("🎯 빠른 질문")
        
        quick_questions = [
            "기본 개념을 설명해주세요",
            "실생활 예시를 들어주세요", 
            "관련 공식을 알려주세요",
            "연습 문제를 내주세요",
            "중요한 포인트를 정리해주세요"
        ]
        
        for i, question in enumerate(quick_questions):
            if st.button(question, key=f"quick_{i}", help=f"'{question}' 질문하기"):
                process_question(question)
                st.rerun()
        
        st.markdown("---")
        
        # 직접 입력
        st.subheader("💬 직접 질문")
        user_input = st.text_area(
            "질문을 입력하세요:",
            placeholder="예: 뉴턴의 운동법칙에 대해 설명해주세요",
            height=100,
            key="user_question"
        )
        
        if st.button("📝 질문하기", key="ask_btn"):
            if user_input.strip():
                process_question(user_input)
                st.rerun()
            else:
                st.warning("질문을 입력해주세요!")
        
        st.markdown("---")
        
        # 음성 설정
        st.subheader("🔊 음성 설정")
        with st.expander("설정 조절"):
            voice_speed = st.slider("음성 속도", 0.5, 2.0, 1.0, 0.1, key="speed_slider")
            voice_pitch = st.slider("음성 높이", 0.5, 2.0, 1.0, 0.1, key="pitch_slider")
            
            # 설정 저장
            if 'voice_settings' not in teacher:
                teacher['voice_settings'] = {}
            teacher['voice_settings']['speed'] = voice_speed
            teacher['voice_settings']['pitch'] = voice_pitch
        
        # 테스트 버튼 (완전 안전한 데이터)
        if st.button("🧪 시스템 테스트", key="test_btn"):
            # 100% 안전한 테스트 내용 (안전한 태그 사용)
            test_explanation = """## 뉴턴의 운동법칙

**정의**: 물체의 운동을 설명하는 기본 법칙들

**제1법칙**: 관성의 법칙
물체는 외부 힘이 없으면 현재 상태를 유지합니다.

<RED>중요: 정지한 물체는 계속 정지하고, 움직이는 물체는 계속 움직입니다.</RED>

**제2법칙**: 가속도의 법칙
F = ma

<BLUE>예시: 무거운 물체일수록 더 큰 힘이 필요합니다.</BLUE>

**제3법칙**: 작용-반작용의 법칙

<U>결론: 이 세 법칙이 모든 운동의 기초가 됩니다.</U>"""
            
            st.session_state.current_explanation = test_explanation
            st.success("🎉 100% 안전한 테스트 수업이 준비되었습니다!")
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

def process_question(question):
    """질문 처리 및 AI 응답 생성"""
    try:
        teacher = st.session_state.selected_teacher
        
        # 채팅 히스토리에 추가
        st.session_state.chat_history.append({
            'role': 'user',
            'content': question,
            'timestamp': datetime.now()
        })
        
        # AI 응답 생성
        system_prompt = generate_system_prompt(teacher)
        
        with st.spinner("🤔 AI가 답변을 준비하고 있습니다..."):
            ai_response = get_claude_response(question, system_prompt, st.session_state.chat_history)
        
        if ai_response and "오류가 발생했습니다" not in ai_response:
            # AI 응답 저장
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now()
            })
            
            # 칠판 설명 내용으로 변환 (안전하게)
            formatted_response = format_for_blackboard(ai_response)
            st.session_state.current_explanation = formatted_response
            
            st.success("✅ AI 답변이 준비되었습니다! 칠판의 '수업 시작' 버튼을 눌러주세요!")
            
        else:
            st.error(f"❌ AI 응답 오류: {ai_response}")
            
    except Exception as e:
        st.error(f"처리 중 오류: {str(e)}")
        st.exception(e)

def format_for_blackboard(response):
    """AI 응답을 칠판 형식으로 변환 - 매우 안전한 버전"""
    lines = response.split('\n')
    formatted = ""
    
    for line in lines:
        line = line.strip()
        if not line:
            formatted += "\n"
            continue
        
        # 기존 HTML 태그 완전 제거
        line = re.sub(r'<[^>]+>', '', line)
        
        # 제목 감지 (## 형태로만)
        if any(keyword in line for keyword in ['에 대해', '란 무엇', '이란 무엇', '개념', '원리', '법칙', '정의']) and len(line) < 60:
            clean_title = line.replace('에 대해', '').replace('란 무엇인가', '').replace('이란 무엇인가', '').strip()
            formatted += f"## {clean_title}\n\n"
            continue
        
        # 정의/개념 감지 (**텍스트** 형태로만)
        if '정의:' in line or '개념:' in line or line.endswith('란') or line.endswith('이란'):
            formatted += f"**{line}**\n\n"
            continue
        
        # 공식 감지 (단순한 등식만)
        if '=' in line and len(line) < 50:
            # 간단한 등식인지 확인
            if re.match(r'^[A-Za-z]+\s*=\s*[A-Za-z0-9\s\+\-\*\/]+$', line.strip()):
                formatted += f"{line}\n\n"
                continue
        
        # 중요사항 감지 (안전한 태그)
        if any(keyword in line for keyword in ['중요', '핵심', '주의', '반드시', '꼭', '절대']):
            # < > 문자를 안전하게 처리
            safe_line = line.replace('<', '').replace('>', '')
            formatted += f"<RED>{safe_line}</RED>\n\n"
            continue
        
        # 예시 감지 (안전한 태그)
        if line.startswith('예:') or line.startswith('예시:') or '예를 들어' in line[:20]:
            safe_line = line.replace('<', '').replace('>', '')
            formatted += f"<BLUE>{safe_line}</BLUE>\n\n"
            continue
        
        # 결론 감지 (안전한 태그)
        if any(keyword in line[:15] for keyword in ['결론', '따라서', '그러므로', '정리하면']):
            safe_line = line.replace('<', '').replace('>', '')
            formatted += f"<U>{safe_line}</U>\n\n"
            continue
        
        # 단계별 설명 (**텍스트** 형태로만)
        if re.match(r'^\d+[.)]\s*', line) or '단계' in line[:10]:
            formatted += f"**{line}**\n"
            continue
        
        # 일반 텍스트 (< > 문자 제거)
        if len(line) > 3:
            safe_line = line.replace('<', '').replace('>', '')
            formatted += f"{safe_line}\n"
    
    # 빈 줄 정리
    formatted = re.sub(r'\n{3,}', '\n\n', formatted)
    
    return formatted.strip()

if __name__ == "__main__":
    main()
