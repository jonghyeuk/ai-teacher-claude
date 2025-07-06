import streamlit as st
import json
import time
from datetime import datetime
import re
import html

# 페이지 설정
st.set_page_config(
    page_title="🎤 GPT-4 AI 튜터",
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
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
    }
    
    .realtime-badge {
        background: linear-gradient(45deg, #28a745, #20c997);
        color: white;
        padding: 8px 20px;
        border-radius: 25px;
        font-size: 14px;
        font-weight: bold;
        display: inline-block;
        margin: 8px;
        animation: pulse 2s infinite;
    }
    
    .cost-badge {
        background: linear-gradient(45deg, #ffc107, #fd7e14);
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
        margin: 5px;
    }
    
    @keyframes pulse {
        0% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.8; transform: scale(1.05); }
        100% { opacity: 1; transform: scale(1); }
    }
    
    .control-panel {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

def create_simple_gpt4_system(teacher_config):
    """단순화된 GPT-4 AI 튜터 시스템"""
    
    # 안전한 설정값 추출
    teacher_name = html.escape(str(teacher_config.get('name', 'AI 튜터')))
    subject = html.escape(str(teacher_config.get('subject', '일반')))
    level = html.escape(str(teacher_config.get('level', '중급')))
    
    html_code = f"""
    <div style="background: #0a0a0a; border-radius: 20px; padding: 25px; box-shadow: 0 15px 35px rgba(0,0,0,0.7);">
        
        <!-- 헤더 -->
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; 
                    padding: 25px; 
                    border-radius: 15px; 
                    text-align: center; 
                    margin-bottom: 25px;">
            
            <h2 style="margin: 0 0 10px 0;">🎙️ GPT-4 AI 튜터</h2>
            <p style="margin: 5px 0; opacity: 0.9;">{teacher_name} | {subject} | {level}</p>
            
            <div style="margin: 15px 0;">
                <span style="background: linear-gradient(45deg, #28a745, #20c997); 
                             color: white; 
                             padding: 8px 20px; 
                             border-radius: 25px; 
                             font-size: 14px; 
                             font-weight: bold; 
                             margin: 5px;">
                    🤖 GPT-4 + 🎵 브라우저 TTS
                </span>
                <br>
                <span style="background: linear-gradient(45deg, #ffc107, #fd7e14); 
                             color: white; 
                             padding: 5px 15px; 
                             border-radius: 20px; 
                             font-size: 12px; 
                             font-weight: bold; 
                             margin: 5px;">
                    💰 시간당 800원 (초저렴!)
                </span>
            </div>
            
            <div id="status-display" style="margin-top: 15px; font-size: 14px; color: #FFD700;">
                🚀 시스템 준비 완료!
            </div>
        </div>
        
        <!-- 컨트롤 패널 -->
        <div style="background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%); 
                    color: white; 
                    padding: 25px; 
                    border-radius: 15px; 
                    margin-bottom: 25px;">
            
            <!-- 마이크 버튼 -->
            <div style="text-align: center; margin-bottom: 20px;">
                <button id="mic-btn" 
                        onclick="toggleRecording()" 
                        style="width: 120px; 
                               height: 120px; 
                               border-radius: 50%; 
                               border: none; 
                               background: linear-gradient(135deg, #e74c3c, #c0392b); 
                               color: white; 
                               font-size: 48px; 
                               cursor: pointer; 
                               box-shadow: 0 8px 20px rgba(231, 76, 60, 0.4);
                               transition: all 0.3s ease;">
                    🎤
                </button>
                <div id="mic-status" style="margin-top: 15px; font-size: 16px; font-weight: bold;">
                    클릭해서 음성 질문하기
                </div>
            </div>
            
            <!-- 상태 표시 -->
            <div id="current-status" style="text-align: center; margin: 20px 0; min-height: 30px; font-size: 18px; font-weight: bold;">
                🎯 질문을 기다리고 있어요!
            </div>
            
            <!-- 간단한 컨트롤 -->
            <div style="text-align: center; margin: 20px 0;">
                <button onclick="clearBoard()" 
                        style="padding: 12px 25px; 
                               background: #95a5a6; 
                               color: white; 
                               border: none; 
                               border-radius: 25px; 
                               font-weight: bold; 
                               cursor: pointer; 
                               margin: 5px;">
                    🗑️ 칠판 지우기
                </button>
                <button onclick="stopAll()" 
                        style="padding: 12px 25px; 
                               background: #e74c3c; 
                               color: white; 
                               border: none; 
                               border-radius: 25px; 
                               font-weight: bold; 
                               cursor: pointer; 
                               margin: 5px;">
                    🛑 정지
                </button>
            </div>
            
            <!-- 통계 -->
            <div style="background: rgba(0,0,0,0.3); padding: 15px; border-radius: 10px;">
                <div style="text-align: center;">
                    💬 질문수: <span id="question-count">0</span> | 
                    💰 예상비용: <span id="cost-estimate">0원</span>
                </div>
            </div>
        </div>
        
        <!-- 칠판 -->
        <div style="background: linear-gradient(135deg, #1a3d3a 0%, #2d5652 50%, #1a3d3a 100%); 
                    border: 8px solid #8B4513; 
                    border-radius: 15px; 
                    padding: 30px; 
                    min-height: 450px; 
                    max-height: 450px; 
                    overflow-y: auto;">
            
            <div style="text-align: center; 
                        color: #FFD700; 
                        font-size: 24px; 
                        font-weight: bold; 
                        margin-bottom: 30px; 
                        border-bottom: 2px solid #FFD700; 
                        padding-bottom: 10px;">
                🎓 GPT-4 AI 칠판
            </div>
            
            <div id="blackboard" 
                 style="color: white; 
                        font-size: 18px; 
                        line-height: 1.8; 
                        font-family: 'Malgun Gothic', sans-serif; 
                        min-height: 300px;">
                
                <div style="text-align: center; color: #ccc; margin-top: 80px;">
                    🎤 마이크 버튼을 눌러 음성으로 질문해보세요!<br><br>
                    💡 예시: "뉴턴의 법칙에 대해 설명해주세요"<br><br>
                    ⚡ GPT-4가 실시간으로 답변하고 칠판에 정리해드려요!
                </div>
            </div>
        </div>
        
        <!-- 대화기록 (숨김) -->
        <div id="chat-log" 
             style="background: rgba(255,255,255,0.1); 
                    border-radius: 10px; 
                    padding: 20px; 
                    margin-top: 20px; 
                    max-height: 150px; 
                    overflow-y: auto;
                    display: none;">
            <h4 style="color: white; margin-top: 0;">📋 대화 기록</h4>
            <div id="chat-content" style="color: #ccc; font-size: 14px;"></div>
        </div>
    </div>

    <script>
    // 간단한 전역 변수들
    let isRecording = false;
    let mediaRecorder = null;
    let audioStream = null;
    let questionCount = 0;
    let totalCost = 0;
    
    // 상태 업데이트
    function updateStatus(message, color = '#FFD700') {{
        const statusEl = document.getElementById('current-status');
        if (statusEl) {{
            statusEl.innerHTML = message;
            statusEl.style.color = color;
        }}
    }}
    
    function updateMicButton(isActive = false) {{
        const micBtn = document.getElementById('mic-btn');
        const micStatus = document.getElementById('mic-status');
        
        if (micBtn && micStatus) {{
            if (isActive) {{
                micBtn.style.background = 'linear-gradient(135deg, #2ecc71, #27ae60)';
                micStatus.textContent = '🔴 녹음 중... 말씀하세요!';
            }} else {{
                micBtn.style.background = 'linear-gradient(135deg, #e74c3c, #c0392b)';
                micStatus.textContent = '클릭해서 음성 질문하기';
            }}
        }}
    }}
    
    function updateStats() {{
        document.getElementById('question-count').textContent = questionCount;
        document.getElementById('cost-estimate').textContent = Math.round(totalCost) + '원';
    }}
    
    // 칠판 업데이트
    function updateBlackboard(content) {{
        const board = document.getElementById('blackboard');
        if (board) {{
            // 간단한 포맷팅
            let formatted = content
                .replace(/\\*\\*([^*]+)\\*\\*/g, '<strong style="color: #FFD700;">$1</strong>')
                .replace(/## ([^\\n]+)/g, '<h3 style="color: #FFD700; text-decoration: underline;">$1</h3>')
                .replace(/\\n/g, '<br>');
            
            board.innerHTML = formatted;
            board.scrollTop = board.scrollHeight;
        }}
    }}
    
    function addToChatLog(speaker, message) {{
        const logContent = document.getElementById('chat-content');
        const logContainer = document.getElementById('chat-log');
        
        if (logContent && logContainer) {{
            const time = new Date().toLocaleTimeString();
            logContent.innerHTML += `<div style="margin: 5px 0; padding: 5px; background: rgba(255,255,255,0.1); border-radius: 5px;">[` + time + `] ` + speaker + `: ` + message + `</div>`;
            logContent.scrollTop = logContent.scrollHeight;
            logContainer.style.display = 'block';
        }}
    }}
    
    // 음성 녹음 토글
    async function toggleRecording() {{
        if (isRecording) {{
            stopRecording();
        }} else {{
            startRecording();
        }}
    }}
    
    async function startRecording() {{
        try {{
            updateStatus('🎤 마이크 권한을 요청하고 있어요...', '#f39c12');
            
            audioStream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
            mediaRecorder = new MediaRecorder(audioStream);
            
            const audioChunks = [];
            
            mediaRecorder.ondataavailable = function(event) {{
                audioChunks.push(event.data);
            }};
            
            mediaRecorder.onstop = async function() {{
                updateStatus('🤔 음성을 처리하고 GPT-4에게 질문하고 있어요...', '#f39c12');
                
                const audioBlob = new Blob(audioChunks, {{ type: 'audio/wav' }});
                
                try {{
                    // 여기서 실제로는 Streamlit backend로 오디오를 보내야 함
                    // 지금은 시뮬레이션
                    await simulateAIResponse();
                    
                }} catch (error) {{
                    updateStatus('❌ 처리 중 오류가 발생했어요: ' + error.message, '#e74c3c');
                }}
            }};
            
            mediaRecorder.start();
            isRecording = true;
            
            updateMicButton(true);
            updateStatus('👂 듣고 있어요! 질문해주세요!', '#2ecc71');
            
        }} catch (error) {{
            updateStatus('❌ 마이크 권한이 필요해요!', '#e74c3c');
            console.error('Recording error:', error);
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
        updateMicButton(false);
    }}
    
    // AI 응답 시뮬레이션 (실제로는 백엔드 연동 필요)
    async function simulateAIResponse() {{
        updateStatus('✍️ AI가 칠판에 답변을 작성하고 있어요...', '#9b59b6');
        
        // 시뮬레이션 응답
        const sampleResponse = `## 뉴턴의 운동 법칙

**정의**: 물체의 운동을 설명하는 세 가지 기본 법칙

**제1법칙 (관성의 법칙)**
정지한 물체는 계속 정지하고, 움직이는 물체는 계속 직선 운동한다.

**제2법칙 (가속도의 법칙)**  
F = ma (힘 = 질량 × 가속도)

**제3법칙 (작용-반작용의 법칙)**
모든 작용에는 크기가 같고 방향이 반대인 반작용이 있다.

**실생활 예시**
- 자동차 급정거 시 몸이 앞으로 쏠리는 현상 (제1법칙)
- 무거운 물건일수록 밀기 어려움 (제2법칙)  
- 걸을 때 땅을 뒤로 밀면 몸이 앞으로 나감 (제3법칙)`;
        
        // 타이핑 효과로 칠판 업데이트
        let currentText = '';
        const words = sampleResponse.split(' ');
        
        for (let i = 0; i < words.length; i++) {{
            currentText += words[i] + ' ';
            updateBlackboard(currentText);
            await new Promise(resolve => setTimeout(resolve, 100)); // 100ms 지연
        }}
        
        // 음성 읽기
        const utterance = new SpeechSynthesisUtterance('뉴턴의 운동법칙에 대해 설명드렸습니다. 추가 질문이 있으시면 언제든 말씀해주세요!');
        utterance.lang = 'ko-KR';
        utterance.rate = 1.1;
        speechSynthesis.speak(utterance);
        
        // 로그 추가
        addToChatLog('👤 학생', '뉴턴의 법칙에 대해 설명해주세요');
        addToChatLog('🤖 AI 튜터', '뉴턴의 운동법칙에 대해 설명드렸습니다.');
        
        // 통계 업데이트
        questionCount++;
        totalCost += 50;
        updateStats();
        
        updateStatus('✅ 설명이 완료되었어요! 추가 질문해주세요!', '#2ecc71');
    }}
    
    // 기타 기능들
    function clearBoard() {{
        updateBlackboard('<div style="text-align: center; color: #ccc; margin-top: 80px;">칠판이 지워졌습니다.<br>새로운 질문을 해주세요!</div>');
        updateStatus('🗑️ 칠판을 지웠어요!', '#95a5a6');
    }}
    
    function stopAll() {{
        if (mediaRecorder) stopRecording();
        speechSynthesis.cancel();
        updateStatus('🛑 모든 작업을 중단했어요!', '#e74c3c');
    }}
    
    // 초기화
    window.addEventListener('load', function() {{
        updateStatus('🚀 GPT-4 AI 튜터 준비 완료!', '#2ecc71');
        updateStats();
        console.log('Simple GPT-4 AI Tutor initialized');
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
        <h1>🎙️ {teacher['name']} GPT-4 AI 튜터</h1>
        <p>📚 {teacher['subject']} | 🎯 {teacher['level']} 수준</p>
        <div class="realtime-badge">🤖 GPT-4 + 🎵 브라우저 TTS</div>
        <div class="cost-badge">💰 시간당 800원 (초저렴!)</div>
        <p style="margin-top: 15px; opacity: 0.9;">⚡ 음성으로 질문하고 AI가 칠판에 정리해드려요!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # API 키 확인
    openai_api_key = st.secrets.get('OPENAI_API_KEY', '')
    
    if not openai_api_key:
        st.error("⚠️ OpenAI API 키가 설정되지 않았습니다.")
        st.info("💡 설정: Streamlit secrets → OPENAI_API_KEY = 'sk-...'")
        return
    
    # 메인 레이아웃
    col1, col2 = st.columns([4, 1])
    
    with col1:
        # 단순화된 GPT-4 시스템
        simple_system = create_simple_gpt4_system(teacher)
        st.components.v1.html(simple_system, height=850)
    
    with col2:
        # 컨트롤 패널
        st.markdown('<div class="control-panel">', unsafe_allow_html=True)
        
        st.subheader("🎛️ 제어판")
        
        # 메인 버튼
        if st.button("🏠 메인으로", key="home_btn", use_container_width=True):
            st.switch_page("app.py")
        
        st.markdown("---")
        
        # 현재 상태
        st.subheader("📊 현재 상태")
        st.success("✅ 시스템 준비 완료")
        st.info("🎤 마이크 권한 필요")
        st.warning("⚠️ 현재 시뮬레이션 모드")
        
        # 기술 정보
        st.markdown("---")
        st.subheader("🚀 기술 스택")
        st.markdown("""
        **🎤 음성 인식:** OpenAI Whisper
        **🤖 AI 대화:** GPT-4
        **🔊 음성 합성:** 브라우저 TTS
        **💻 인터페이스:** JavaScript
        """)
        
        # 비용 정보
        st.subheader("💰 예상 비용")
        st.markdown("""
        **2시간 대화 기준:**
        - Whisper: 312원
        - GPT-4: 1,209원
        - TTS: 0원 (무료)
        - **총합: 1,521원**
        
        **시간당 760원! 😊**
        """)
        
        # 튜터 정보
        st.markdown("---")
        st.subheader("👨‍🏫 AI 튜터")
        st.write(f"**이름:** {teacher['name']}")
        st.write(f"**전문분야:** {teacher['subject']}")
        st.write(f"**교육수준:** {teacher['level']}")
        
        # 사용법
        st.markdown("---")
        st.subheader("💡 사용법")
        st.markdown("""
        1. **🎤 마이크 버튼 클릭**
        2. **브라우저 권한 허용**
        3. **음성으로 질문하기**
        4. **AI 답변 확인**
        
        **📝 질문 예시:**
        - "뉴턴의 법칙 설명해줘"
        - "피타고라스 정리 알려줘"
        - "영어 문법 질문있어"
        """)
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
