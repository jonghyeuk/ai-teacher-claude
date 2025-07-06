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

# Claude API 응답 함수
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

def process_question(question, teacher):
    """질문 처리 및 AI 응답 생성"""
    try:
        # 채팅 히스토리 초기화
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # 채팅 히스토리에 사용자 질문 추가
        st.session_state.chat_history.append({
            'role': 'user',
            'content': question,
            'timestamp': datetime.now()
        })
        
        # AI 응답 생성
        system_prompt = generate_system_prompt(teacher)
        ai_response = get_claude_response(question, system_prompt, st.session_state.chat_history)
        
        if ai_response and "오류:" not in ai_response:
            # AI 응답을 채팅 히스토리에 추가
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now()
            })
            
            return ai_response
        else:
            return f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {ai_response}"
            
    except Exception as e:
        return f"처리 중 오류가 발생했습니다: {str(e)}"

def create_ultra_simple_interface():
    """가장 단순한 인터페이스"""
    
    html_code = """
    <div style="background: #f8f9fa; border-radius: 15px; padding: 20px; margin: 20px 0;">
        
        <!-- 헤더 -->
        <div style="text-align: center; margin-bottom: 20px;">
            <h3 style="color: #333; margin: 0;">🎓 AI 튜터와 대화하기</h3>
            <p style="color: #666; margin: 5px 0;">텍스트로 질문하고 음성으로 답변을 들어보세요</p>
        </div>
        
        <!-- 텍스트 입력 -->
        <div style="margin-bottom: 20px;">
            <textarea id="question-input" 
                      placeholder="질문을 입력하세요. 예: 뉴턴의 법칙에 대해 설명해주세요" 
                      style="width: 100%; 
                             height: 80px; 
                             padding: 15px; 
                             border: 2px solid #e0e0e0; 
                             border-radius: 10px; 
                             font-size: 16px; 
                             resize: vertical;
                             font-family: 'Malgun Gothic', sans-serif;"></textarea>
        </div>
        
        <!-- 버튼 -->
        <div style="text-align: center; margin-bottom: 20px;">
            <button onclick="askQuestion()" 
                    style="background: #28a745; 
                           color: white; 
                           border: none; 
                           padding: 15px 30px; 
                           border-radius: 25px; 
                           font-size: 16px; 
                           font-weight: bold; 
                           cursor: pointer; 
                           margin: 5px;">
                📝 질문하기
            </button>
            
            <button onclick="clearAll()" 
                    style="background: #6c757d; 
                           color: white; 
                           border: none; 
                           padding: 15px 30px; 
                           border-radius: 25px; 
                           font-size: 16px; 
                           font-weight: bold; 
                           cursor: pointer; 
                           margin: 5px;">
                🗑️ 지우기
            </button>
        </div>
        
        <!-- 상태 -->
        <div id="status" style="text-align: center; 
                                 margin: 15px 0; 
                                 padding: 10px; 
                                 background: #e7f3ff; 
                                 border-radius: 8px; 
                                 color: #0066cc;">
            💡 위에 질문을 입력하고 "질문하기" 버튼을 눌러주세요
        </div>
        
        <!-- 답변 영역 -->
        <div style="background: linear-gradient(135deg, #1a3d3a 0%, #2d5652 100%); 
                    border: 4px solid #8B4513; 
                    border-radius: 15px; 
                    padding: 25px; 
                    min-height: 300px; 
                    max-height: 400px; 
                    overflow-y: auto;">
            
            <div style="text-align: center; 
                        color: #FFD700; 
                        font-size: 20px; 
                        font-weight: bold; 
                        margin-bottom: 20px; 
                        border-bottom: 2px solid #FFD700; 
                        padding-bottom: 10px;">
                📋 AI 튜터 답변
            </div>
            
            <div id="answer-area" 
                 style="color: white; 
                        font-size: 16px; 
                        line-height: 1.6; 
                        font-family: 'Malgun Gothic', sans-serif;">
                
                <div style="text-align: center; color: #ccc; margin-top: 50px;">
                    질문을 입력하면 AI 튜터가 친근하게 답변해드려요! 😊<br><br>
                    
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
    </div>

    <script>
    function askQuestion() {
        const input = document.getElementById('question-input');
        const question = input.value.trim();
        
        if (!question) {
            updateStatus('❌ 질문을 입력해주세요!', 'error');
            return;
        }
        
        // 입력창 비우기
        input.value = '';
        
        // 상태 업데이트
        updateStatus('🤔 AI 튜터가 답변을 준비하고 있어요...', 'loading');
        
        // Streamlit으로 질문 전송 (실제 구현 필요)
        // 지금은 페이지 새로고침으로 Streamlit 처리
        const form = document.createElement('form');
        form.method = 'POST';
        form.style.display = 'none';
        
        const hiddenField = document.createElement('input');
        hiddenField.type = 'hidden';
        hiddenField.name = 'user_question';
        hiddenField.value = question;
        
        form.appendChild(hiddenField);
        document.body.appendChild(form);
        
        // Streamlit에서 처리하도록 세션 스토리지 사용
        sessionStorage.setItem('pending_question', question);
        window.location.reload();
    }
    
    function updateStatus(message, type) {
        const statusEl = document.getElementById('status');
        if (!statusEl) return;
        
        let bgColor = '#e7f3ff';
        let textColor = '#0066cc';
        
        if (type === 'error') {
            bgColor = '#f8d7da';
            textColor = '#721c24';
        } else if (type === 'loading') {
            bgColor = '#fff3cd';
            textColor = '#856404';
        } else if (type === 'success') {
            bgColor = '#d4edda';
            textColor = '#155724';
        }
        
        statusEl.style.background = bgColor;
        statusEl.style.color = textColor;
        statusEl.innerHTML = message;
    }
    
    function updateAnswer(content) {
        const answerArea = document.getElementById('answer-area');
        if (!answerArea) return;
        
        // 간단한 포맷팅
        let formatted = content
            .replace(/\\*\\*([^*]+)\\*\\*/g, '<strong style="color: #FFD700;">$1</strong>')
            .replace(/## ([^\\n]+)/g, '<h3 style="color: #FFD700; text-decoration: underline; margin: 15px 0;">$1</h3>')
            .replace(/\\[중요\\]([^\\n]+)/g, '<div style="color: #FF6B6B; font-weight: bold; margin: 10px 0; padding: 8px; background: rgba(255,107,107,0.2); border-radius: 5px;">🔴 $1</div>')
            .replace(/\\[예시\\]([^\\n]+)/g, '<div style="color: #4DABF7; font-weight: bold; margin: 10px 0; padding: 8px; background: rgba(77,171,247,0.2); border-radius: 5px;">🔵 $1</div>')
            .replace(/\\n/g, '<br>');
        
        answerArea.innerHTML = formatted;
        answerArea.scrollTop = answerArea.scrollHeight;
    }
    
    function clearAll() {
        const input = document.getElementById('question-input');
        const answerArea = document.getElementById('answer-area');
        
        if (input) input.value = '';
        if (answerArea) {
            answerArea.innerHTML = '<div style="text-align: center; color: #ccc; margin-top: 50px;">답변 영역이 지워졌습니다.<br>새로운 질문을 해주세요! 😊</div>';
        }
        
        updateStatus('🗑️ 모든 내용을 지웠어요!', 'success');
        
        // 세션 스토리지도 정리
        sessionStorage.removeItem('pending_question');
    }
    
    // Enter 키 지원
    document.addEventListener('DOMContentLoaded', function() {
        const input = document.getElementById('question-input');
        if (input) {
            input.addEventListener('keydown', function(event) {
                if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    askQuestion();
                }
            });
        }
    });
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
        <p>💬 자유롭게 질문하고 대화하세요!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 세션 스토리지에서 질문 확인
    pending_question = st.query_params.get('question', '')
    
    # 메인 레이아웃
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # 질문 입력
        user_question = st.text_area(
            "💬 질문을 입력하세요:",
            placeholder="예: 뉴턴의 법칙에 대해 설명해주세요",
            height=100,
            key="user_input",
            value=pending_question
        )
        
        col_a, col_b, col_c = st.columns([1, 1, 2])
        
        with col_a:
            if st.button("📝 질문하기", key="ask_btn", use_container_width=True):
                if user_question.strip():
                    with st.spinner("🤔 AI가 답변 준비 중..."):
                        response = process_question(user_question, teacher)
                    st.session_state.current_response = response
                    st.rerun()
                else:
                    st.warning("질문을 입력해주세요!")
        
        with col_b:
            if st.button("🗑️ 지우기", key="clear_btn", use_container_width=True):
                if 'current_response' in st.session_state:
                    del st.session_state.current_response
                if 'chat_history' in st.session_state:
                    del st.session_state.chat_history
                st.rerun()
        
        # 답변 표시
        if 'current_response' in st.session_state:
            st.markdown("### 🎓 AI 튜터 답변:")
            
            # 답변을 포맷팅해서 표시
            formatted_response = st.session_state.current_response
            formatted_response = re.sub(r'\*\*([^*]+)\*\*', r'**\1**', formatted_response)
            formatted_response = re.sub(r'\[중요\]([^\n]+)', r'🔴 **중요:** \1', formatted_response)
            formatted_response = re.sub(r'\[예시\]([^\n]+)', r'🔵 **예시:** \1', formatted_response)
            
            st.markdown(formatted_response)
            
            # 음성으로 읽기
            if st.button("🔊 음성으로 듣기", key="tts_btn"):
                # 간단한 음성 요약
                summary = "답변을 확인해주세요. 추가 질문이 있으시면 언제든 말씀해주세요!"
                
                st.markdown(f"""
                <script>
                const utterance = new SpeechSynthesisUtterance('{summary}');
                utterance.lang = 'ko-KR';
                utterance.rate = 1.0;
                speechSynthesis.speak(utterance);
                </script>
                """, unsafe_allow_html=True)
                
                st.success("🔊 음성 재생 중...")
        
        # 대화 기록
        if 'chat_history' in st.session_state and st.session_state.chat_history:
            with st.expander("📋 대화 기록 보기"):
                for i, msg in enumerate(st.session_state.chat_history):
                    if msg['role'] == 'user':
                        st.markdown(f"**👤 학생:** {msg['content']}")
                    else:
                        st.markdown(f"**🤖 AI 튜터:** {msg['content'][:100]}...")
                    st.markdown("---")
    
    with col2:
        # 컨트롤 패널
        st.subheader("🎛️ 컨트롤")
        
        if st.button("🏠 메인으로", key="home_btn", use_container_width=True):
            st.switch_page("app.py")
        
        st.markdown("---")
        st.subheader("📊 현재 상태")
        
        # API 키 확인
        claude_key = st.secrets.get('ANTHROPIC_API_KEY', '')
        if claude_key:
            st.success("✅ Claude API 연결됨")
        else:
            st.error("❌ Claude API 키 필요")
            st.info("💡 Streamlit secrets에 ANTHROPIC_API_KEY 설정하세요")
        
        st.info("💬 텍스트 입력 준비됨")
        
        st.markdown("---")
        st.subheader("👨‍🏫 튜터 정보")
        st.write(f"**이름:** {teacher['name']}")
        st.write(f"**전문분야:** {teacher['subject']}")
        st.write(f"**교육수준:** {teacher['level']}")
        
        personality = teacher.get('personality', {})
        st.write(f"**친근함:** {personality.get('friendliness', 70)}/100")
        
        st.markdown("---")
        st.subheader("💡 사용법")
        st.markdown("""
        **🎯 현재 기능:**
        1. 텍스트로 질문 입력
        2. AI가 실제로 답변 생성
        3. 대화 맥락 유지
        4. 음성으로 간단히 듣기
        
        **📝 질문 예시:**
        - "뉴턴의 법칙 설명해줘"
        - "이차방정식 풀이법"
        - "영어 문법 질문"
        
        **🚀 다음 업데이트:**
        - 실제 음성 인식
        - 실시간 스트리밍  
        - 고급 TTS
        """)

if __name__ == "__main__":
    main()
