import streamlit as st
import streamlit.components.v1 as components

# 페이지 설정
st.set_page_config(
    page_title="AI 튜터 실시간 음성 대화",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 AI 튜터 실시간 음성 대화 시스템")
st.markdown("### 2단계: 성능과 비용 균형 구성")

# 서버 URL 설정
WEBSOCKET_URL = "wss://ai-teacher-611312919059.asia-northeast3.run.app/ws/tutor/user1"

# 상태 표시
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("백엔드 상태", "🟢 정상", "FastAPI + Cloud Run")
with col2:
    st.metric("AI 모델", "GPT-3.5 Turbo", "비용 최적화")
with col3:
    st.metric("음성 처리", "Google TTS", "Standard 모델")

st.divider()

# 대화 영역
st.subheader("🎙️ 음성 대화")

# WebSocket HTML Component
websocket_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 30px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }}
        .status {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .status-dot {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }}
        .connected {{ background: #4CAF50; }}
        .disconnected {{ background: #f44336; }}
        .connecting {{ background: #ff9800; animation: pulse 1s infinite; }}
        
        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
            100% {{ opacity: 1; }}
        }}
        
        .controls {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .btn {{
            padding: 15px 30px;
            border: none;
            border-radius: 50px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .btn-record {{
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            color: white;
        }}
        
        .btn-record:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(238, 90, 36, 0.3);
        }}
        
        .btn-record:active {{
            background: linear-gradient(45deg, #ee5a24, #ff6b6b);
        }}
        
        .btn-stop {{
            background: linear-gradient(45deg, #6c757d, #495057);
            color: white;
        }}
        
        .btn-stop:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(108, 117, 125, 0.3);
        }}
        
        .chat-area {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 20px;
            min-height: 400px;
            max-height: 500px;
            overflow-y: auto;
            margin-bottom: 20px;
        }}
        
        .message {{
            margin-bottom: 15px;
            padding: 12px 18px;
            border-radius: 18px;
            max-width: 70%;
            animation: slideIn 0.3s ease;
        }}
        
        .user-message {{
            background: linear-gradient(45deg, #4CAF50, #45a049);
            margin-left: auto;
            text-align: right;
        }}
        
        .ai-message {{
            background: rgba(255, 255, 255, 0.1);
            margin-right: auto;
        }}
        
        @keyframes slideIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .typing {{
            display: none;
            background: rgba(255, 255, 255, 0.1);
            padding: 12px 18px;
            border-radius: 18px;
            max-width: 200px;
            margin-bottom: 15px;
        }}
        
        .typing-dots {{
            display: flex;
            gap: 4px;
        }}
        
        .typing-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.7);
            animation: typing 1.4s infinite;
        }}
        
        .typing-dot:nth-child(2) {{ animation-delay: 0.2s; }}
        .typing-dot:nth-child(3) {{ animation-delay: 0.4s; }}
        
        @keyframes typing {{
            0%, 60%, 100% {{ transform: translateY(0); }}
            30% {{ transform: translateY(-10px); }}
        }}
        
        .info {{
            text-align: center;
            font-size: 14px;
            opacity: 0.8;
            margin-top: 15px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="status">
            <span class="status-dot disconnected" id="statusDot"></span>
            <span id="statusText">연결 중...</span>
        </div>
        
        <div class="controls">
            <button class="btn btn-record" id="recordBtn" onclick="startRecording()">
                🎤 음성 녹음 시작
            </button>
            <button class="btn btn-stop" id="stopBtn" onclick="stopRecording()" disabled>
                ⏹️ 녹음 중지
            </button>
        </div>
        
        <div class="chat-area" id="chatArea">
            <div class="message ai-message">
                안녕하세요! 🎓 AI 튜터입니다. 궁금한 것이 있으면 언제든 물어보세요!
            </div>
        </div>
        
        <div class="typing" id="typingIndicator">
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
        
        <div class="info">
            💡 마이크 버튼을 눌러 질문하세요. AI 튜터가 실시간으로 답변해드립니다.
        </div>
    </div>

    <script>
        let websocket = null;
        let mediaRecorder = null;
        let audioChunks = [];
        let isRecording = false;
        
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');
        const recordBtn = document.getElementById('recordBtn');
        const stopBtn = document.getElementById('stopBtn');
        const chatArea = document.getElementById('chatArea');
        const typingIndicator = document.getElementById('typingIndicator');
        
        // WebSocket 연결
        function connectWebSocket() {{
            const wsUrl = '{WEBSOCKET_URL}';
            console.log('연결 시도:', wsUrl);
            
            statusDot.className = 'status-dot connecting';
            statusText.textContent = '연결 중...';
            
            websocket = new WebSocket(wsUrl);
            
            websocket.onopen = function(event) {{
                console.log('WebSocket 연결 성공');
                statusDot.className = 'status-dot connected';
                statusText.textContent = '연결됨';
                recordBtn.disabled = false;
            }};
            
            websocket.onmessage = function(event) {{
                console.log('메시지 수신:', event.data);
                
                try {{
                    const message = JSON.parse(event.data);
                    handleServerMessage(message);
                }} catch (e) {{
                    console.log('텍스트 메시지:', event.data);
                }}
            }};
            
            websocket.onclose = function(event) {{
                console.log('WebSocket 연결 종료');
                statusDot.className = 'status-dot disconnected';
                statusText.textContent = '연결 끊김';
                recordBtn.disabled = true;
                
                // 5초 후 재연결 시도
                setTimeout(connectWebSocket, 5000);
            }};
            
            websocket.onerror = function(error) {{
                console.error('WebSocket 에러:', error);
                statusDot.className = 'status-dot disconnected';
                statusText.textContent = '연결 오류';
            }};
        }}
        
        // 서버 메시지 처리
        function handleServerMessage(message) {{
            console.log('서버 메시지:', message);
            
            switch(message.type) {{
                case 'connection_established':
                    addMessage('ai', message.message);
                    break;
                    
                case 'stt_result':
                    addMessage('user', message.text);
                    showTyping();
                    break;
                    
                case 'audio_chunk':
                    hideTyping();
                    addMessage('ai', message.content);
                    if (message.audio) {{
                        playAudio(message.audio);
                    }}
                    break;
                    
                case 'text_chunk':
                    hideTyping();
                    addMessage('ai', message.content);
                    break;
                    
                case 'error':
                    hideTyping();
                    addMessage('ai', '❌ ' + message.message);
                    break;
            }}
        }}
        
        // 메시지 추가
        function addMessage(sender, text) {{
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${{sender}}-message`;
            messageDiv.textContent = text;
            chatArea.appendChild(messageDiv);
            chatArea.scrollTop = chatArea.scrollHeight;
        }}
        
        // 타이핑 표시
        function showTyping() {{
            typingIndicator.style.display = 'block';
        }}
        
        function hideTyping() {{
            typingIndicator.style.display = 'none';
        }}
        
        // 오디오 재생
        function playAudio(base64Audio) {{
            try {{
                const audioBlob = base64ToBlob(base64Audio, 'audio/mp3');
                const audioUrl = URL.createObjectURL(audioBlob);
                const audio = new Audio(audioUrl);
                
                audio.play().then(() => {{
                    console.log('오디오 재생 시작');
                }}).catch(error => {{
                    console.error('오디오 재생 실패:', error);
                }});
                
                // 메모리 정리
                audio.onended = () => {{
                    URL.revokeObjectURL(audioUrl);
                }};
            }} catch (error) {{
                console.error('오디오 처리 오류:', error);
            }}
        }}
        
        // Base64를 Blob으로 변환
        function base64ToBlob(base64, mimeType) {{
            const byteCharacters = atob(base64);
            const byteNumbers = new Array(byteCharacters.length);
            for (let i = 0; i < byteCharacters.length; i++) {{
                byteNumbers[i] = byteCharacters.charCodeAt(i);
            }}
            const byteArray = new Uint8Array(byteNumbers);
            return new Blob([byteArray], {{type: mimeType}});
        }}
        
        // 녹음 시작
        async function startRecording() {{
            try {{
                const stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                
                mediaRecorder.ondataavailable = function(event) {{
                    audioChunks.push(event.data);
                }};
                
                mediaRecorder.onstop = function() {{
                    const audioBlob = new Blob(audioChunks, {{ type: 'audio/wav' }});
                    sendAudioToServer(audioBlob);
                    
                    // 스트림 정리
                    stream.getTracks().forEach(track => track.stop());
                }};
                
                mediaRecorder.start();
                isRecording = true;
                
                recordBtn.disabled = true;
                stopBtn.disabled = false;
                recordBtn.innerHTML = '🎤 녹음 중...';
                
            }} catch (error) {{
                console.error('마이크 접근 오류:', error);
                alert('마이크에 접근할 수 없습니다. 브라우저 설정을 확인해주세요.');
            }}
        }}
        
        // 녹음 중지
        function stopRecording() {{
            if (mediaRecorder && isRecording) {{
                mediaRecorder.stop();
                isRecording = false;
                
                recordBtn.disabled = false;
                stopBtn.disabled = true;
                recordBtn.innerHTML = '🎤 음성 녹음 시작';
            }}
        }}
        
        // 오디오를 서버로 전송
        function sendAudioToServer(audioBlob) {{
            if (websocket && websocket.readyState === WebSocket.OPEN) {{
                console.log('오디오 전송:', audioBlob.size, 'bytes');
                websocket.send(audioBlob);
            }} else {{
                console.error('WebSocket 연결이 없습니다');
                addMessage('ai', '❌ 서버 연결이 끊어졌습니다. 페이지를 새로고침해주세요.');
            }}
        }}
        
        // 페이지 로드 시 WebSocket 연결
        connectWebSocket();
        
        // 페이지 언로드 시 연결 정리
        window.addEventListener('beforeunload', function() {{
            if (websocket) {{
                websocket.close();
            }}
        }});
    </script>
</body>
</html>
"""

# HTML Component 렌더링
components.html(websocket_html, height=800, scrolling=False)

st.divider()

# 시스템 정보
st.subheader("🔧 시스템 정보")

col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    **아키텍처:**
    - Frontend: Streamlit Cloud
    - Backend: FastAPI (Google Cloud Run)
    - Communication: WebSocket
    """)

with col2:
    st.markdown("""
    **AI 모델:**
    - STT: Google Cloud Speech-to-Text (TODO)
    - LLM: GPT-3.5 Turbo Streaming  
    - TTS: Google Cloud TTS Standard
    """)

# 사용법 안내
st.subheader("📖 사용법")
st.markdown("""
1. **🟢 연결됨** 상태 확인
2. **🎤 음성 녹음 시작** 버튼 클릭
3. **질문하기** (예: "미적분학에 대해 설명해주세요")
4. **⏹️ 녹음 중지** 버튼 클릭
5. **AI 답변** 듣기 (텍스트 + 음성)
""")

# 설정
with st.sidebar:
    st.header("⚙️ 설정")
    
    st.subheader("🎓 튜터 설정")
    teacher_name = st.selectbox("튜터 이름", ["김선생", "이선생", "박선생"])
    subject = st.selectbox("과목", ["수학", "물리", "화학", "영어", "국어"])
    level = st.selectbox("수준", ["초등학교", "중학교", "고등학교", "대학교"])
    
    st.subheader("🔊 음성 설정")
    voice_speed = st.slider("음성 속도", 0.8, 1.5, 1.1, 0.1)
    voice_pitch = st.slider("음성 높낮이", -5.0, 5.0, 0.0, 0.5)
    
    st.subheader("📊 상태")
    st.metric("WebSocket URL", "✅ 설정됨")
    st.code(WEBSOCKET_URL, language="text")
