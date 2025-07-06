import streamlit as st
import json
import time
from datetime import datetime
import re

# 페이지 설정
st.set_page_config(
    page_title="🎤 AI 튜터",
    page_icon="🎙️",
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
    }
</style>
""", unsafe_allow_html=True)

# Claude API 응답 함수 (기존 코드 재사용)
def get_claude_response(user_message, system_prompt, chat_history):
    """Claude API 응답 생성"""
    try:
        from anthropic import Anthropic
        
        api_key = st.secrets.get('ANTHROPIC_API_KEY')
        if not api_key:
            return "Claude API 키가 설정되지 않았습니다."
        
        client = Anthropic(api_key=api_key)
        
        messages = []
        for msg in chat_history[-5:]:
            if msg['role'] in ['user', 'assistant']:
                messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })
        
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=800,
            temperature=0.7,
            system=system_prompt,
            messages=messages
        )
        
        return response.content[0].text
        
    except Exception as e:
        return f"오류: {str(e)}"

def generate_system_prompt(teacher_config):
    """시스템 프롬프트 생성"""
    personality = teacher_config.get('personality', {})
    
    return f"""당신은 {teacher_config['name']}이라는 AI 튜터입니다.
{teacher_config['subject']} 분야 전문가이며, {teacher_config['level']} 수준 학생들을 가르칩니다.

성격 특성:
- 친근함: {personality.get('friendliness', 70)}/100
- 유머: {personality.get('humor_level', 30)}/100  
- 격려: {personality.get('encouragement', 80)}/100

답변 방식:
- 이해하기 쉽게 단계별 설명
- 중요한 내용은 **강조**로 표시
- 예시를 들어 설명
- 학생의 이해도 확인

칠판 정리:
- 제목: ## 제목
- 중요사항: [중요] 내용
- 예시: [예시] 내용
- 공식: 명확하게 표시

친근하고 격려하는 말투로 대화하세요."""

def create_simple_interface(teacher_config):
    """단순하고 실용적인 인터페이스"""
    
    teacher_name = teacher_config.get('name', 'AI 튜터')
    
    html_code = f"""
    <div style="background: #f8f9fa; border-radius: 15px; padding: 20px; margin: 20px 0;">
        
        <!-- 간단한 헤더 -->
        <div style="text-align: center; margin-bottom: 20px;">
            <h3 style="color: #333; margin: 0;">🎓 {teacher_name} AI 튜터</h3>
            <p style="color: #666; margin: 5px 0;">텍스트 또는 음성으로 질문하세요</p>
        </div>
        
        <!-- 텍스트 입력 영역 -->
        <div style="margin-bottom: 20px;">
            <textarea id="text-input" 
                      placeholder="여기에 질문을 입력하세요. 예: 뉴턴의 법칙에 대해 설명해주세요" 
                      style="width: 100%; 
                             height: 80px; 
                             padding: 15px; 
                             border: 2px solid #e0e0e0; 
                             border-radius: 10px; 
                             font-size: 16px; 
                             resize: vertical;
                             font-family: 'Malgun Gothic', sans-serif;"></textarea>
        </div>
        
        <!-- 버튼들 -->
        <div style="text-align: center; margin-bottom: 20px;">
            <button onclick="sendTextMessage()" 
                    style="background: #28a745; 
                           color: white; 
                           border: none; 
                           padding: 12px 30px; 
                           border-radius: 25px; 
                           font-size: 16px; 
                           font-weight: bold; 
                           cursor: pointer; 
                           margin: 5px;">
                📝 텍스트로 질문하기
            </button>
            
            <button id="voice-btn" onclick="toggleVoice()" 
                    style="background: #dc3545; 
                           color: white; 
                           border: none; 
                           padding: 12px 30px; 
                           border-radius: 25px; 
                           font-size: 16px; 
                           font-weight: bold; 
                           cursor: pointer; 
                           margin: 5px;">
                🎤 음성으로 질문하기
            </button>
            
            <button onclick="clearBoard()" 
                    style="background: #6c757d; 
                           color: white; 
                           border: none; 
                           padding: 12px 30px; 
                           border-radius: 25px; 
                           font-size: 16px; 
                           font-weight: bold; 
                           cursor: pointer; 
                           margin: 5px;">
                🗑️ 지우기
            </button>
        </div>
        
        <!-- 상태 표시 -->
        <div id="status" style="text-align: center; 
                                 margin: 15px 0; 
                                 padding: 10px; 
                                 background: #e7f3ff; 
                                 border-radius: 8px; 
                                 color: #0066cc;">
            💡 질문을 입력하거나 음성 버튼을 눌러주세요
        </div>
        
        <!-- 칠판 -->
        <div style="background: linear-gradient(135deg, #1a3d3a 0%, #2d5652 100%); 
                    border: 4px solid #8B4513; 
                    border-radius: 15px; 
                    padding: 25px; 
                    min-height: 400px; 
                    max-height: 500px; 
                    overflow-y: auto;">
            
            <div style="text-align: center; 
                        color: #FFD700; 
                        font-size: 20px; 
                        font-weight: bold; 
                        margin-bottom: 20px; 
                        border-bottom: 2px solid #FFD700; 
                        padding-bottom: 10px;">
                📋 AI 튜터 칠판
            </div>
            
            <div id="blackboard" 
                 style="color: white; 
                        font-size: 16px; 
                        line-height: 1.6; 
                        font-family: 'Malgun Gothic', sans-serif;">
                
                <div style="text-align: center; color: #ccc; margin-top: 50px;">
                    위의 텍스트 입력창에 질문을 입력하거나<br>
                    🎤 버튼을 눌러 음성으로 질문해보세요!<br><br>
                    
                    <div style="background: rgba(255,255,255,0.1); 
                                padding: 15px; 
                                border-radius: 10px; 
                                margin: 20px 0;">
                        <strong>💡 질문 예시:</strong><br>
                        • "뉴턴의 법칙에 대해 설명해주세요"<br>
                        • "이차방정식 풀이 방법을 알려주세요"<br>
                        • "영어 과거시제 사용법이 궁금해요"
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 대화 기록 -->
        <div id="chat-history" style="background: #fff; 
                                      border: 1px solid #ddd; 
                                      border-radius: 10px; 
                                      padding: 15px; 
                                      margin-top: 20px; 
                                      max-height: 200px; 
                                      overflow-y: auto;
                                      display: none;">
            <h4 style="margin-top: 0; color: #333;">📋 대화 기록</h4>
            <div id="chat-content" style="font-size: 14px; color: #555;"></div>
        </div>
    </div>

    <script>
    let isRecording = false;
    let mediaRecorder = null;
    let audioStream = null;
    let currentSpeech = null;
    
    // 상태 업데이트
    function updateStatus(message, type = 'info') {{
        const statusEl = document.getElementById('status');
        if (!statusEl) return;
        
        let bgColor = '#e7f3ff';
        let textColor = '#0066cc';
        
        if (type === 'success') {{
            bgColor = '#d4edda';
            textColor = '#155724';
        }} else if (type === 'error') {{
            bgColor = '#f8d7da';
            textColor = '#721c24';
        }} else if (type === 'warning') {{
            bgColor = '#fff3cd';
            textColor = '#856404';
        }}
        
        statusEl.style.background = bgColor;
        statusEl.style.color = textColor;
        statusEl.innerHTML = message;
    }}
    
    // 칠판 업데이트 (스크롤 수정)
    function updateBlackboard(content) {{
        const board = document.getElementById('blackboard');
        if (!board) return;
        
        // 간단한 포맷팅
        let formatted = content
            .replace(/\\*\\*([^*]+)\\*\\*/g, '<strong style="color: #FFD700;">$1</strong>')
            .replace(/## ([^\\n]+)/g, '<h3 style="color: #FFD700; text-decoration: underline; margin: 15px 0;">$1</h3>')
            .replace(/\\[중요\\]([^\\n]+)/g, '<div style="color: #FF6B6B; font-weight: bold; margin: 10px 0; padding: 8px; background: rgba(255,107,107,0.2); border-radius: 5px;">🔴 $1</div>')
            .replace(/\\[예시\\]([^\\n]+)/g, '<div style="color: #4DABF7; font-weight: bold; margin: 10px 0; padding: 8px; background: rgba(77,171,247,0.2); border-radius: 5px;">🔵 $1</div>')
            .replace(/\\n/g, '<br>');
        
        board.innerHTML = formatted;
        
        // 스크롤을 맨 아래로 (수정됨)
        board.scrollTop = board.scrollHeight;
    }}
    
    // 채팅 기록 추가
    function addToChatHistory(speaker, message) {{
        const chatContent = document.getElementById('chat-content');
        const chatHistory = document.getElementById('chat-history');
        
        if (!chatContent || !chatHistory) return;
        
        const time = new Date().toLocaleTimeString();
        const chatItem = document.createElement('div');
        chatItem.style.cssText = 'margin: 8px 0; padding: 8px; background: #f8f9fa; border-radius: 5px; border-left: 3px solid #007bff;';
        chatItem.innerHTML = `<strong>[${time}] ${speaker}:</strong> ${message}`;
        
        chatContent.appendChild(chatItem);
        chatHistory.style.display = 'block';
        chatContent.scrollTop = chatContent.scrollHeight;
    }}
    
    // 텍스트 메시지 전송
    async function sendTextMessage() {{
        const textInput = document.getElementById('text-input');
        if (!textInput) return;
        
        const message = textInput.value.trim();
        if (!message) {{
            updateStatus('❌ 질문을 입력해주세요!', 'error');
            return;
        }}
        
        // 입력창 비우기
        textInput.value = '';
        
        // 처리 중 표시
        updateStatus('🤔 AI가 답변을 준비하고 있어요...', 'warning');
        
        // 채팅 기록에 추가
        addToChatHistory('👤 학생', message);
        
        try {{
            // 실제 API 호출을 위해 Streamlit으로 데이터 전송
            // 여기서는 시뮬레이션
            await simulateAIResponse(message);
            
        }} catch (error) {{
            updateStatus('❌ 오류가 발생했습니다: ' + error.message, 'error');
        }}
    }}
    
    // AI 응답 시뮬레이션
    async function simulateAIResponse(userMessage) {{
        updateStatus('✍️ AI가 칠판에 답변을 작성하고 있어요...', 'warning');
        
        // 사용자 질문에 따른 간단한 응답 생성
        let response = '';
        
        if (userMessage.includes('뉴턴') || userMessage.includes('물리')) {{
            response = `## 뉴턴의 운동 법칙

**뉴턴의 3법칙**은 물리학의 기본 원리입니다.

**제1법칙 (관성의 법칙)**
물체는 외부 힘이 작용하지 않으면 현재 상태를 유지합니다.

[예시] 버스가 급브레이크를 밟으면 승객이 앞으로 쏠리는 현상

**제2법칙 (가속도의 법칙)**  
F = ma (힘 = 질량 × 가속도)

[중요] 같은 힘이라도 질량이 클수록 가속도는 작아집니다.

**제3법칙 (작용-반작용의 법칙)**
모든 작용에는 크기가 같고 방향이 반대인 반작용이 존재합니다.

[예시] 걸을 때 발로 땅을 뒤로 밀면, 땅이 우리를 앞으로 밀어줍니다.

**결론**
뉴턴의 법칙은 우리 일상의 모든 운동을 설명하는 기본 원리입니다!`;
        }} else if (userMessage.includes('이차방정식') || userMessage.includes('수학')) {{
            response = `## 이차방정식 풀이

**이차방정식**의 일반형: ax² + bx + c = 0 (a ≠ 0)

**풀이 방법들**

**1. 인수분해**
x² - 5x + 6 = 0
(x - 2)(x - 3) = 0
따라서 x = 2 또는 x = 3

**2. 완전제곱식**
x² + 6x + 9 = 0
(x + 3)² = 0
따라서 x = -3

**3. 근의 공식**
x = (-b ± √(b² - 4ac)) / 2a

[중요] 판별식 D = b² - 4ac
- D > 0: 서로 다른 두 실근
- D = 0: 중근 (같은 실근 2개)  
- D < 0: 허근

[예시] x² - 4x + 3 = 0에서
D = 16 - 12 = 4 > 0 → 서로 다른 두 실근`;
        }} else {{
            response = `## ${userMessage}에 대한 답변

안녕하세요! **${userMessage}**에 대해 질문해주셨네요.

이 주제는 정말 흥미로운 내용입니다.

[중요] 구체적인 답변을 위해 더 자세한 질문을 해주시면 좋겠어요.

[예시] 다음과 같이 질문해보세요:
- "뉴턴의 법칙에 대해 설명해주세요"
- "이차방정식 풀이 방법을 알려주세요"
- "영어 문법 중 과거시제 사용법이 궁금해요"

**더 구체적인 질문을 해주시면 더 정확하고 자세한 답변을 드릴 수 있어요!**`;
        }}
        
        // 타이핑 효과로 칠판 업데이트
        await typeOnBlackboard(response);
        
        // 채팅 기록에 추가
        addToChatHistory('🤖 AI 튜터', '답변을 칠판에 정리했습니다.');
        
        // 음성으로 간단한 설명 (중복 방지)
        speakText('답변을 칠판에 정리했습니다. 추가 질문이 있으시면 언제든 말씀해주세요!');
        
        updateStatus('✅ 답변 완료! 추가 질문해주세요 😊', 'success');
    }}
    
    // 타이핑 효과
    async function typeOnBlackboard(text) {{
        const board = document.getElementById('blackboard');
        if (!board) return;
        
        board.innerHTML = '';
        
        const words = text.split(' ');
        let currentText = '';
        
        for (let i = 0; i < words.length; i++) {{
            currentText += words[i] + ' ';
            
            // 포맷팅 적용
            let formatted = currentText
                .replace(/\\*\\*([^*]+)\\*\\*/g, '<strong style="color: #FFD700;">$1</strong>')
                .replace(/## ([^\\n]+)/g, '<h3 style="color: #FFD700; text-decoration: underline; margin: 15px 0;">$1</h3>')
                .replace(/\\[중요\\]([^\\n]+)/g, '<div style="color: #FF6B6B; font-weight: bold; margin: 10px 0; padding: 8px; background: rgba(255,107,107,0.2); border-radius: 5px;">🔴 $1</div>')
                .replace(/\\[예시\\]([^\\n]+)/g, '<div style="color: #4DABF7; font-weight: bold; margin: 10px 0; padding: 8px; background: rgba(77,171,247,0.2); border-radius: 5px;">🔵 $1</div>')
                .replace(/\\n/g, '<br>');
            
            board.innerHTML = formatted;
            board.scrollTop = board.scrollHeight;
            
            await new Promise(resolve => setTimeout(resolve, 80)); // 80ms 지연
        }}
    }}
    
    // 음성 재생 (중복 방지)
    function speakText(text) {{
        // 기존 음성 중지
        if (currentSpeech) {{
            speechSynthesis.cancel();
            currentSpeech = null;
        }}
        
        if (!text.trim()) return;
        
        try {{
            currentSpeech = new SpeechSynthesisUtterance(text);
            currentSpeech.lang = 'ko-KR';
            currentSpeech.rate = 1.0;
            currentSpeech.pitch = 1.0;
            
            // 한국어 음성 찾기
            const voices = speechSynthesis.getVoices();
            const koreanVoice = voices.find(voice => 
                voice.lang && voice.lang.toLowerCase().includes('ko')
            );
            if (koreanVoice) {{
                currentSpeech.voice = koreanVoice;
            }}
            
            currentSpeech.onend = function() {{
                currentSpeech = null;
            }};
            
            speechSynthesis.speak(currentSpeech);
            
        }} catch (error) {{
            console.error('TTS Error:', error);
        }}
    }}
    
    // 음성 녹음 토글
    async function toggleVoice() {{
        if (isRecording) {{
            stopRecording();
        }} else {{
            startRecording();
        }}
    }}
    
    async function startRecording() {{
        try {{
            updateStatus('🎤 마이크 권한을 요청하고 있어요...', 'warning');
            
            audioStream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
            mediaRecorder = new MediaRecorder(audioStream);
            
            const audioChunks = [];
            
            mediaRecorder.ondataavailable = function(event) {{
                audioChunks.push(event.data);
            }};
            
            mediaRecorder.onstop = async function() {{
                updateStatus('🤔 음성을 텍스트로 변환하고 있어요...', 'warning');
                
                // 음성 인식 시뮬레이션
                const sampleQuestions = [
                    "뉴턴의 법칙에 대해 설명해주세요",
                    "이차방정식 풀이 방법을 알려주세요", 
                    "영어 과거시제 사용법이 궁금해요"
                ];
                
                const randomQuestion = sampleQuestions[Math.floor(Math.random() * sampleQuestions.length)];
                
                addToChatHistory('👤 학생 (음성)', randomQuestion);
                await simulateAIResponse(randomQuestion);
            }};
            
            mediaRecorder.start();
            isRecording = true;
            
            const voiceBtn = document.getElementById('voice-btn');
            if (voiceBtn) {{
                voiceBtn.style.background = '#28a745';
                voiceBtn.innerHTML = '🔴 녹음 중... (클릭해서 중지)';
            }}
            
            updateStatus('👂 듣고 있어요! 질문해주세요!', 'success');
            
        }} catch (error) {{
            updateStatus('❌ 마이크 권한이 필요해요!', 'error');
        }}
    }}
    
    function stopRecording() {{
        if (mediaRecorder && mediaRecorder.state === 'recording') {{
            mediaRecorder.stop();
        }}
        
        if (audioStream) {{
            audioStream.getTracks().forEach(track => track.stop());
        }}
        
        isRecording = false;
        
        const voiceBtn = document.getElementById('voice-btn');
        if (voiceBtn) {{
            voiceBtn.style.background = '#dc3545';
            voiceBtn.innerHTML = '🎤 음성으로 질문하기';
        }}
    }}
    
    // 칠판 지우기
    function clearBoard() {{
        updateBlackboard('<div style="text-align: center; color: #ccc; margin-top: 80px;">칠판이 지워졌습니다.<br>새로운 질문을 해주세요! 😊</div>');
        updateStatus('🗑️ 칠판을 지웠어요!', 'success');
        
        // 음성도 중지
        if (currentSpeech) {{
            speechSynthesis.cancel();
            currentSpeech = null;
        }}
    }}
    
    // Enter 키로 전송
    document.addEventListener('DOMContentLoaded', function() {{
        const textInput = document.getElementById('text-input');
        if (textInput) {{
            textInput.addEventListener('keydown', function(event) {{
                if (event.key === 'Enter' && !event.shiftKey) {{
                    event.preventDefault();
                    sendTextMessage();
                }}
            }});
        }}
        
        updateStatus('💡 질문을 입력하거나 음성 버튼을 눌러주세요', 'info');
    }});
    </script>
    """
    
    return html_code

def initialize_teacher():
    """AI 튜터 초기화"""
    if 'selected_teacher' not in st.session_state:
        st.error("AI 튜터가 선택되지 않았습니다. 메인 페이지로 돌아가세요.")
        if st.button("🏠 메인 페이지로"):
            st.switch_page("app.py")
        return None
    
    return st.session_state.selected_teacher

def main():
    teacher = initialize_teacher()
    if not teacher:
        return
    
    # 헤더
    st.markdown(f"""
    <div class="teacher-header">
        <h1>🎙️ {teacher['name']} AI 튜터</h1>
        <p>📚 {teacher['subject']} | 🎯 {teacher['level']} 수준</p>
        <p>💬 텍스트와 음성으로 자유롭게 질문하세요!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 메인 레이아웃
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # 단순하고 실용적인 인터페이스
        simple_interface = create_simple_interface(teacher)
        st.components.v1.html(simple_interface, height=800)
    
    with col2:
        # 간단한 컨트롤 패널
        st.subheader("🎛️ 컨트롤")
        
        if st.button("🏠 메인으로", key="home_btn", use_container_width=True):
            st.switch_page("app.py")
        
        st.markdown("---")
        st.subheader("📊 현재 상태")
        st.success("✅ 시스템 준비됨")
        st.info("💬 텍스트/음성 입력 가능")
        st.warning("⚠️ 시뮬레이션 모드")
        
        st.markdown("---")
        st.subheader("👨‍🏫 튜터 정보")
        st.write(f"**이름:** {teacher['name']}")
        st.write(f"**전문분야:** {teacher['subject']}")
        st.write(f"**교육수준:** {teacher['level']}")
        
        st.markdown("---")
        st.subheader("💡 사용법")
        st.markdown("""
        **📝 텍스트 질문:**
        1. 위의 입력창에 질문 입력
        2. "텍스트로 질문하기" 버튼 클릭
        3. 또는 Enter 키 사용
        
        **🎤 음성 질문:**
        1. "음성으로 질문하기" 버튼 클릭
        2. 마이크 권한 허용
        3. 명확하게 질문하기
        4. 다시 버튼 클릭해서 중지
        
        **🔧 수정된 부분:**
        - 음성 반복 문제 해결
        - 칠판 스크롤 수정  
        - 텍스트 입력 추가
        - UI 대폭 단순화
        """)

if __name__ == "__main__":
    main()
