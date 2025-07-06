import streamlit as st
import json
import time
from datetime import datetime
import re
import html

# 페이지 설정
st.set_page_config(
    page_title="🎤 실시간 AI 튜터",
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
        background: linear-gradient(45deg, #ff6b6b, #ee5a52);
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
        margin: 5px;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
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

def create_realtime_ai_tutor_system(teacher_config, openai_api_key):
    """OpenAI Realtime API 기반 실시간 AI 튜터 시스템"""
    
    # 안전한 설정값 추출
    teacher_name = html.escape(teacher_config.get('name', 'AI 튜터'))
    subject = html.escape(teacher_config.get('subject', '일반'))
    level = html.escape(teacher_config.get('level', '중급'))
    
    personality = teacher_config.get('personality', {})
    friendliness = personality.get('friendliness', 70)
    humor_level = personality.get('humor_level', 30)
    encouragement = personality.get('encouragement', 80)
    
    # 시스템 프롬프트 생성
    system_prompt = f"""당신은 {teacher_name}이라는 이름의 AI 튜터입니다.
{subject} 분야의 전문가이며, {level} 수준의 학생들을 가르칩니다.

성격 특성:
- 친근함: {friendliness}/100 (높을수록 더 친근하게)
- 유머: {humor_level}/100 (높을수록 더 유머러스하게)
- 격려: {encouragement}/100 (높을수록 더 격려하며)

교육 방식:
- 학생의 수준에 맞춰 설명
- 이해하기 쉬운 예시 활용
- 질문을 격려하고 친근하게 응답
- 칠판에 중요한 내용 정리하며 설명

대화할 때는 자연스럽게 "음~", "그러니까", "잠깐만" 같은 추임새를 사용하고,
학생이 이해했는지 중간중간 확인해주세요."""

    html_code = f"""
    <div style="background: #0a0a0a; border-radius: 20px; padding: 25px; box-shadow: 0 15px 35px rgba(0,0,0,0.7);">
        
        <!-- 🎤 실시간 AI 튜터 헤더 -->
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; 
                    padding: 25px; 
                    border-radius: 15px; 
                    text-align: center; 
                    margin-bottom: 25px;">
            
            <h2 style="margin: 0 0 10px 0;">🎙️ 실시간 AI 튜터</h2>
            <p style="margin: 5px 0; opacity: 0.9;">{teacher_name} | {subject} | {level}</p>
            
            <!-- 실시간 배지 -->
            <div style="margin: 15px 0;">
                <span style="background: linear-gradient(45deg, #ff6b6b, #ee5a52); 
                             color: white; 
                             padding: 8px 20px; 
                             border-radius: 25px; 
                             font-size: 14px; 
                             font-weight: bold; 
                             animation: pulse 2s infinite;">
                    🔴 LIVE - 실시간 음성 대화
                </span>
            </div>
            
            <!-- 연결 상태 -->
            <div id="connection-status" style="margin-top: 15px; font-size: 14px;">
                <span id="status-text">🔌 연결 준비 중...</span>
            </div>
        </div>
        
        <!-- 🎛️ 실시간 컨트롤 패널 -->
        <div style="background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%); 
                    color: white; 
                    padding: 25px; 
                    border-radius: 15px; 
                    margin-bottom: 25px;">
            
            <!-- 마이크 버튼 (대형) -->
            <div style="text-align: center; margin-bottom: 20px;">
                <button id="mic-button" 
                        onclick="toggleVoiceChat()" 
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
                    음성 채팅 시작하기
                </div>
            </div>
            
            <!-- 음성 시각화 -->
            <div id="voice-visualizer" style="display: none; margin: 20px 0; height: 80px; display: flex; justify-content: center; align-items: end;">
                <div class="voice-bar" style="width: 8px; height: 15px; background: #2ecc71; margin: 0 3px; border-radius: 4px; animation: voice-bounce 0.8s ease-in-out infinite;"></div>
                <div class="voice-bar" style="width: 8px; height: 30px; background: #2ecc71; margin: 0 3px; border-radius: 4px; animation: voice-bounce 0.8s ease-in-out infinite 0.1s;"></div>
                <div class="voice-bar" style="width: 8px; height: 45px; background: #2ecc71; margin: 0 3px; border-radius: 4px; animation: voice-bounce 0.8s ease-in-out infinite 0.2s;"></div>
                <div class="voice-bar" style="width: 8px; height: 25px; background: #2ecc71; margin: 0 3px; border-radius: 4px; animation: voice-bounce 0.8s ease-in-out infinite 0.3s;"></div>
                <div class="voice-bar" style="width: 8px; height: 50px; background: #2ecc71; margin: 0 3px; border-radius: 4px; animation: voice-bounce 0.8s ease-in-out infinite 0.4s;"></div>
                <div class="voice-bar" style="width: 8px; height: 20px; background: #2ecc71; margin: 0 3px; border-radius: 4px; animation: voice-bounce 0.8s ease-in-out infinite 0.5s;"></div>
                <div class="voice-bar" style="width: 8px; height: 35px; background: #2ecc71; margin: 0 3px; border-radius: 4px; animation: voice-bounce 0.8s ease-in-out infinite 0.6s;"></div>
                <div class="voice-bar" style="width: 8px; height: 55px; background: #2ecc71; margin: 0 3px; border-radius: 4px; animation: voice-bounce 0.8s ease-in-out infinite 0.7s;"></div>
            </div>
            
            <!-- 대화 상태 -->
            <div id="conversation-info" style="text-align: center; margin: 15px 0;">
                <div id="listening-indicator" style="display: none; color: #2ecc71; font-weight: bold;">
                    👂 듣고 있어요... 질문해주세요!
                </div>
                <div id="thinking-indicator" style="display: none; color: #f39c12; font-weight: bold;">
                    🤔 답변을 생각하고 있어요...
                </div>
                <div id="speaking-indicator" style="display: none; color: #3498db; font-weight: bold;">
                    🗣️ AI 선생님이 설명하고 있어요
                </div>
            </div>
            
            <!-- 컨트롤 버튼들 -->
            <div style="text-align: center; margin: 20px 0;">
                <button onclick="stopConversation()" 
                        style="padding: 12px 25px; 
                               background: #e74c3c; 
                               color: white; 
                               border: none; 
                               border-radius: 25px; 
                               font-weight: bold; 
                               cursor: pointer; 
                               margin: 5px;">
                    🛑 대화 중단
                </button>
                <button onclick="clearBlackboard()" 
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
                <button onclick="downloadTranscript()" 
                        style="padding: 12px 25px; 
                               background: #27ae60; 
                               color: white; 
                               border: none; 
                               border-radius: 25px; 
                               font-weight: bold; 
                               cursor: pointer; 
                               margin: 5px;">
                    💾 대화록 저장
                </button>
            </div>
        </div>
        
        <!-- 📝 실시간 칠판 -->
        <div style="background: linear-gradient(135deg, #1a3d3a 0%, #2d5652 50%, #1a3d3a 100%); 
                    border: 8px solid #8B4513; 
                    border-radius: 15px; 
                    padding: 30px; 
                    min-height: 500px; 
                    max-height: 500px; 
                    overflow-y: auto;">
            
            <!-- 칠판 제목 -->
            <div style="text-align: center; 
                        color: #FFD700; 
                        font-size: 24px; 
                        font-weight: bold; 
                        margin-bottom: 30px; 
                        border-bottom: 2px solid #FFD700; 
                        padding-bottom: 10px;">
                🎓 AI 튜터 실시간 칠판
            </div>
            
            <!-- 실시간 타이핑 내용 -->
            <div id="blackboard-content" 
                 style="color: white; 
                        font-size: 18px; 
                        line-height: 1.8; 
                        font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; 
                        min-height: 300px;">
                
                <div style="text-align: center; 
                            color: #ccc; 
                            margin-top: 80px; 
                            font-size: 16px;">
                    🎤 마이크 버튼을 눌러 음성 대화를 시작하세요<br><br>
                    💡 "뉴턴의 법칙에 대해 설명해주세요" 같은 질문을 해보세요!
                </div>
            </div>
            
            <!-- 실시간 타이핑 커서 -->
            <span id="typing-cursor" 
                  style="color: #FFD700; 
                         font-size: 20px; 
                         animation: cursor-blink 1s infinite; 
                         display: none;">|</span>
        </div>
        
        <!-- 📋 대화 기록 -->
        <div id="conversation-log" 
             style="background: rgba(255,255,255,0.1); 
                    border-radius: 10px; 
                    padding: 20px; 
                    margin-top: 20px; 
                    max-height: 200px; 
                    overflow-y: auto;
                    display: none;">
            <h4 style="color: white; margin-top: 0;">📋 대화 기록</h4>
            <div id="log-content" style="color: #ccc; font-size: 14px;"></div>
        </div>
    </div>

    <style>
    @keyframes voice-bounce {{
        0%, 100% {{ height: 15px; }}
        50% {{ height: 60px; }}
    }}
    
    @keyframes cursor-blink {{
        0%, 50% {{ opacity: 1; }}
        51%, 100% {{ opacity: 0; }}
    }}
    
    @keyframes pulse {{
        0% {{ opacity: 1; transform: scale(1); }}
        50% {{ opacity: 0.8; transform: scale(1.05); }}
        100% {{ opacity: 1; transform: scale(1); }}
    }}
    
    #mic-button:hover {{
        transform: scale(1.1);
        box-shadow: 0 12px 30px rgba(231, 76, 60, 0.6);
    }}
    
    #mic-button.recording {{
        background: linear-gradient(135deg, #2ecc71, #27ae60) !important;
        animation: pulse 1.5s infinite;
    }}
    
    .voice-bar {{
        transition: height 0.1s ease-in-out;
    }}
    </style>

    <script>
    // 전역 변수
    let realtimeWS = null;
    let isConnected = false;
    let isRecording = false;
    let mediaRecorder = null;
    let audioStream = null;
    let conversationHistory = [];
    let systemPrompt = `{system_prompt}`;
    let openaiApiKey = '{openai_api_key}';
    
    // 상태 업데이트 함수들
    function updateStatus(message, color = '#2ecc71') {{
        const statusEl = document.getElementById('status-text');
        if (statusEl) {{
            statusEl.textContent = message;
            statusEl.style.color = color;
        }}
    }}
    
    function updateMicStatus(message, isActive = false) {{
        const statusEl = document.getElementById('mic-status');
        const micBtn = document.getElementById('mic-button');
        if (statusEl) statusEl.textContent = message;
        if (micBtn) {{
            if (isActive) {{
                micBtn.classList.add('recording');
            }} else {{
                micBtn.classList.remove('recording');
            }}
        }}
    }}
    
    function showIndicator(type) {{
        // 모든 인디케이터 숨김
        ['listening-indicator', 'thinking-indicator', 'speaking-indicator'].forEach(id => {{
            const el = document.getElementById(id);
            if (el) el.style.display = 'none';
        }});
        
        // 특정 인디케이터 표시
        const el = document.getElementById(type + '-indicator');
        if (el) el.style.display = 'block';
    }}
    
    function toggleVoiceVisualizer(show) {{
        const visualizer = document.getElementById('voice-visualizer');
        if (visualizer) {{
            visualizer.style.display = show ? 'flex' : 'none';
        }}
    }}
    
    // 실시간 칠판 업데이트
    function updateBlackboard(content, append = false) {{
        const blackboardEl = document.getElementById('blackboard-content');
        if (!blackboardEl) return;
        
        if (append) {{
            blackboardEl.innerHTML += content;
        }} else {{
            blackboardEl.innerHTML = content;
        }}
        
        // 자동 스크롤
        blackboardEl.scrollTop = blackboardEl.scrollHeight;
    }}
    
    function typeOnBlackboard(text) {{
        const blackboardEl = document.getElementById('blackboard-content');
        const cursor = document.getElementById('typing-cursor');
        
        if (!blackboardEl || !cursor) return;
        
        blackboardEl.innerHTML = '';
        cursor.style.display = 'inline';
        
        let index = 0;
        const typingInterval = setInterval(() => {{
            if (index < text.length) {{
                blackboardEl.innerHTML = formatBlackboardText(text.substring(0, index + 1));
                index++;
                blackboardEl.scrollTop = blackboardEl.scrollHeight;
            }} else {{
                clearInterval(typingInterval);
                cursor.style.display = 'none';
            }}
        }}, 30);
    }}
    
    function formatBlackboardText(text) {{
        // 제목 포맷팅
        text = text.replace(/##\\s*([^#\\n]+)/g, '<h2 style="color: #FFD700; text-decoration: underline; margin: 20px 0;">$1</h2>');
        
        // 강조 표시
        text = text.replace(/\\*\\*([^*]+)\\*\\*/g, '<strong style="color: #FFD700;">$1</strong>');
        
        // 중요사항 (빨간색)
        text = text.replace(/\\[중요\\]([^\\n]+)/g, '<div style="color: #FF6B6B; font-weight: bold; margin: 10px 0;">🔴 $1</div>');
        
        // 참고사항 (파란색)
        text = text.replace(/\\[참고\\]([^\\n]+)/g, '<div style="color: #4DABF7; font-weight: bold; margin: 10px 0;">🔵 $1</div>');
        
        // 핵심사항 (노란색)
        text = text.replace(/\\[핵심\\]([^\\n]+)/g, '<div style="color: #FFD700; font-weight: bold; text-decoration: underline; margin: 10px 0;">⭐ $1</div>');
        
        // 공식 포맷팅
        text = text.replace(/([A-Za-z]\\s*=\\s*[A-Za-z0-9\\s\\+\\-\\*\\/\\(\\)]+)/g, 
                           '<div style="background: rgba(65, 105, 225, 0.3); color: white; padding: 15px; border-radius: 8px; border-left: 4px solid #FFD700; margin: 15px 0; font-family: \\'Courier New\\', monospace; font-size: 20px; text-align: center;">$1</div>');
        
        // 줄바꿈 처리
        text = text.replace(/\\n/g, '<br>');
        
        return text;
    }}
    
    // OpenAI Realtime API 연결
    async function connectToRealtimeAPI() {{
        try {{
            updateStatus('🔌 OpenAI Realtime API 연결 중...', '#f39c12');
            
            // WebSocket 연결
            realtimeWS = new WebSocket('wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01', 
                                      ['realtime', 'Bearer ' + openaiApiKey]);
            
            realtimeWS.onopen = function() {{
                updateStatus('✅ 실시간 AI 연결 완료!', '#2ecc71');
                isConnected = true;
                
                // 세션 구성
                const sessionConfig = {{
                    type: 'session.update',
                    session: {{
                        modalities: ['text', 'audio'],
                        instructions: systemPrompt,
                        voice: 'alloy',
                        input_audio_format: 'pcm16',
                        output_audio_format: 'pcm16',
                        input_audio_transcription: {{
                            model: 'whisper-1'
                        }}
                    }}
                }};
                
                realtimeWS.send(JSON.stringify(sessionConfig));
            }};
            
            realtimeWS.onmessage = function(event) {{
                const data = JSON.parse(event.data);
                handleRealtimeMessage(data);
            }};
            
            realtimeWS.onerror = function(error) {{
                updateStatus('❌ 연결 오류: ' + error.message, '#e74c3c');
                console.error('Realtime API Error:', error);
            }};
            
            realtimeWS.onclose = function() {{
                updateStatus('🔌 연결이 끊어졌습니다', '#e74c3c');
                isConnected = false;
            }};
            
        }} catch (error) {{
            updateStatus('❌ 연결 실패: ' + error.message, '#e74c3c');
            console.error('Connection Error:', error);
        }}
    }}
    
    // Realtime 메시지 처리
    function handleRealtimeMessage(data) {{
        switch (data.type) {{
            case 'conversation.item.input_audio_transcription.completed':
                // 사용자 음성 텍스트 변환 완료
                const userText = data.transcript;
                addToConversationLog('👤 학생: ' + userText);
                showIndicator('thinking');
                break;
                
            case 'response.audio_transcript.delta':
                // AI 응답 텍스트 스트리밍
                if (data.delta) {{
                    updateBlackboard(data.delta, true);
                }}
                break;
                
            case 'response.audio_transcript.done':
                // AI 응답 완료
                showIndicator('speaking');
                addToConversationLog('🤖 ' + '{teacher_name}: ' + data.transcript);
                break;
                
            case 'response.audio.delta':
                // AI 음성 스트리밍 (실제 음성 재생)
                if (data.delta) {{
                    playAudioDelta(data.delta);
                }}
                break;
                
            case 'response.done':
                // 응답 완료
                showIndicator('listening');
                break;
                
            case 'error':
                updateStatus('❌ API 오류: ' + data.error.message, '#e74c3c');
                break;
        }}
    }}
    
    // 음성 대화 토글
    async function toggleVoiceChat() {{
        if (!isConnected) {{
            await connectToRealtimeAPI();
            return;
        }}
        
        if (isRecording) {{
            stopRecording();
        }} else {{
            startRecording();
        }}
    }}
    
    // 녹음 시작
    async function startRecording() {{
        try {{
            audioStream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
            
            mediaRecorder = new MediaRecorder(audioStream);
            
            mediaRecorder.ondataavailable = function(event) {{
                if (event.data.size > 0 && realtimeWS && realtimeWS.readyState === WebSocket.OPEN) {{
                    // 오디오 데이터를 실시간으로 전송
                    const reader = new FileReader();
                    reader.onload = function() {{
                        const audioData = {{
                            type: 'input_audio_buffer.append',
                            audio: btoa(String.fromCharCode(...new Uint8Array(reader.result)))
                        }};
                        realtimeWS.send(JSON.stringify(audioData));
                    }};
                    reader.readAsArrayBuffer(event.data);
                }}
            }};
            
            mediaRecorder.start(100); // 100ms 간격으로 데이터 전송
            isRecording = true;
            
            updateMicStatus('🔴 녹음 중... 질문해주세요!', true);
            showIndicator('listening');
            toggleVoiceVisualizer(true);
            
        }} catch (error) {{
            updateStatus('❌ 마이크 권한이 필요합니다', '#e74c3c');
            console.error('Recording Error:', error);
        }}
    }}
    
    // 녹음 중지
    function stopRecording() {{
        if (mediaRecorder && mediaRecorder.state === 'recording') {{
            mediaRecorder.stop();
        }}
        
        if (audioStream) {{
            audioStream.getTracks().forEach(track => track.stop());
        }}
        
        if (realtimeWS && realtimeWS.readyState === WebSocket.OPEN) {{
            // 입력 완료 신호
            realtimeWS.send(JSON.stringify({{ type: 'input_audio_buffer.commit' }}));
            realtimeWS.send(JSON.stringify({{ type: 'response.create' }}));
        }}
        
        isRecording = false;
        updateMicStatus('🎤 음성 채팅 시작하기', false);
        toggleVoiceVisualizer(false);
        showIndicator('thinking');
    }}
    
    // 기타 기능들
    function stopConversation() {{
        if (mediaRecorder) stopRecording();
        if (realtimeWS) realtimeWS.close();
        updateStatus('🔌 대화가 종료되었습니다', '#95a5a6');
        updateMicStatus('🎤 음성 채팅 시작하기', false);
    }}
    
    function clearBlackboard() {{
        updateBlackboard('<div style="text-align: center; color: #ccc; margin-top: 80px;">칠판이 지워졌습니다.<br>새로운 질문을 해주세요!</div>');
    }}
    
    function addToConversationLog(text) {{
        const logEl = document.getElementById('log-content');
        const logContainer = document.getElementById('conversation-log');
        
        if (logEl && logContainer) {{
            const timestamp = new Date().toLocaleTimeString();
            logEl.innerHTML += `<div style="margin: 5px 0; padding: 5px; background: rgba(255,255,255,0.1); border-radius: 5px;">[${timestamp}] ${text}</div>`;
            logEl.scrollTop = logEl.scrollHeight;
            logContainer.style.display = 'block';
        }}
        
        conversationHistory.push({{ text, timestamp: new Date() }});
    }}
    
    function downloadTranscript() {{
        const transcript = conversationHistory.map(item => 
            `[${item.timestamp.toLocaleString()}] ${item.text}`
        ).join('\\n\\n');
        
        const blob = new Blob([transcript], {{ type: 'text/plain' }});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'ai_tutor_conversation_' + new Date().toISOString().slice(0,10) + '.txt';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }}
    
    // 페이지 로드 시 초기화
    window.addEventListener('load', function() {{
        updateStatus('🚀 실시간 AI 튜터 준비 완료!');
        console.log('Real-time AI Tutor System Initialized');
        
        // 자동 연결 (선택사항)
        // connectToRealtimeAPI();
    }});
    
    // 페이지 종료 시 정리
    window.addEventListener('beforeunload', function() {{
        stopConversation();
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
        <h1>🎙️ {teacher['name']} 실시간 AI 튜터</h1>
        <p>📚 {teacher['subject']} | 🎯 {teacher['level']} 수준</p>
        <div class="realtime-badge">🔴 OpenAI Realtime API 통합</div>
        <p style="margin-top: 15px; opacity: 0.9;">💬 자연스러운 음성 대화로 학습하세요!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # OpenAI API 키 확인
    openai_api_key = st.secrets.get('OPENAI_API_KEY', '')
    if not openai_api_key:
        st.error("⚠️ OpenAI API 키가 설정되지 않았습니다. Streamlit secrets에 OPENAI_API_KEY를 설정해주세요.")
        st.info("💡 설정 방법: Streamlit Cloud → Settings → Secrets → OPENAI_API_KEY = 'your-api-key'")
        return
    
    # 메인 레이아웃
    col1, col2 = st.columns([4, 1])
    
    with col1:
        # 실시간 AI 튜터 시스템
        realtime_system = create_realtime_ai_tutor_system(teacher, openai_api_key)
        st.components.v1.html(realtime_system, height=900)
    
    with col2:
        # 컨트롤 패널
        st.markdown('<div class="control-panel">', unsafe_allow_html=True)
        
        st.subheader("🎛️ 제어판")
        
        # 메인 버튼들
        if st.button("🏠 메인으로", key="home_btn", use_container_width=True):
            st.switch_page("app.py")
        
        st.markdown("---")
        
        # 튜터 정보
        st.subheader("👨‍🏫 AI 튜터 정보")
        st.write(f"**이름:** {teacher['name']}")
        st.write(f"**전문분야:** {teacher['subject']}")
        st.write(f"**교육수준:** {teacher['level']}")
        
        personality = teacher.get('personality', {})
        st.write(f"**친근함:** {personality.get('friendliness', 70)}/100")
        st.write(f"**유머수준:** {personality.get('humor_level', 30)}/100")
        st.write(f"**격려수준:** {personality.get('encouragement', 80)}/100")
        
        st.markdown("---")
        
        # 사용 팁
        st.subheader("💡 사용 팁")
        st.markdown("""
        **🎤 음성 대화 방법:**
        1. 큰 마이크 버튼 클릭
        2. 마이크 권한 허용
        3. 자연스럽게 질문하기
        4. AI의 음성 답변 듣기
        
        **📝 질문 예시:**
        - "뉴턴의 법칙 설명해줘"
        - "이차방정식 풀이 알려줘"
        - "화학반응식 설명해줘"
        - "영어 문법 질문있어"
        
        **🔄 기능:**
        - 실시간 음성 인식
        - 자연스러운 대화
        - 칠판 자동 업데이트
        - 대화록 저장
        """)
        
        st.markdown("---")
        
        # 시스템 상태
        st.subheader("📊 시스템 상태")
        st.success("🔗 OpenAI Realtime API 준비됨")
        st.info("🎙️ 마이크 권한 필요")
        st.warning("🌐 안정적인 인터넷 연결 필요")
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
