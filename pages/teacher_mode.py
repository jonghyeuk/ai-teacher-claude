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

# Claude API 응답 함수
def get_claude_response(user_message, system_prompt, chat_history):
    """Claude API 응답 생성"""
    try:
        from anthropic import Anthropic
        
        api_key = st.secrets.get('ANTHROPIC_API_KEY')
        if not api_key:
            return "Claude API 키가 설정되지 않았습니다. Streamlit secrets에 ANTHROPIC_API_KEY를 설정해주세요."
        
        client = Anthropic(api_key=api_key)
        
        messages = []
        for msg in chat_history[-10:]:  # 최근 10개만 유지
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
        return f"응답 생성 중 오류가 발생했습니다: {str(e)}"

def generate_system_prompt(teacher_config):
    """시스템 프롬프트 생성"""
    personality = teacher_config.get('personality', {})
    
    return f"""당신은 {teacher_config['name']}이라는 AI 튜터입니다.
{teacher_config['subject']} 분야의 전문가이며, {teacher_config['level']} 수준의 학생들을 가르칩니다.

성격 특성:
- 친근함: {personality.get('friendliness', 70)}/100
- 유머: {personality.get('humor_level', 30)}/100  
- 격려: {personality.get('encouragement', 80)}/100

교육 방식:
- 학생의 수준에 맞춰 이해하기 쉽게 설명
- 중요한 내용은 **강조**로 표시
- 구체적인 예시를 들어 설명
- 단계별로 차근차근 가르침
- 학생의 이해도를 중간중간 확인

대화 스타일:
- 친근하고 격려하는 말투 사용
- "음~", "그런데", "그리고" 같은 자연스러운 추임새
- 학생이 이해했는지 확인하는 질문
- 칭찬과 격려를 아끼지 않음

답변 형식:
- 제목이 필요하면 ## 제목 형태로
- 중요한 내용은 **굵게** 표시
- 예시는 구체적이고 이해하기 쉽게
- 복잡한 내용은 단계별로 나누어 설명

학생과 자연스럽고 연속적인 대화를 이어가세요."""

def initialize_teacher():
    """AI 튜터 초기화"""
    if 'selected_teacher' not in st.session_state:
        st.error("AI 튜터가 선택되지 않았습니다. 메인 페이지로 돌아가세요.")
        if st.button("🏠 메인 페이지로"):
            st.switch_page("app.py")
        return None
    
    return st.session_state.selected_teacher

def format_response(text):
    """응답 텍스트 포맷팅"""
    # 제목 포맷팅
    text = re.sub(r'^## (.+)$', r'### 📚 \1', text, flags=re.MULTILINE)
    
    # 중요사항 강조
    text = re.sub(r'\[중요\]([^\n]+)', r'🔴 **중요:** \1', text)
    text = re.sub(r'\[예시\]([^\n]+)', r'🔵 **예시:** \1', text)
    
    return text

def main():
    teacher = initialize_teacher()
    if not teacher:
        return
    
    # 세션 상태 초기화
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # 헤더
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; 
                padding: 20px; 
                border-radius: 15px; 
                text-align: center; 
                margin-bottom: 20px;">
        <h1>🎙️ {teacher['name']} AI 튜터</h1>
        <p>📚 {teacher['subject']} | 🎯 {teacher['level']} 수준</p>
        <p>💬 자연스러운 대화로 학습하세요!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # API 키 확인
    claude_key = st.secrets.get('ANTHROPIC_API_KEY', '')
    
    if not claude_key:
        st.error("⚠️ Claude API 키가 설정되지 않았습니다.")
        st.info("💡 Streamlit secrets에 ANTHROPIC_API_KEY를 설정해주세요.")
        st.code("ANTHROPIC_API_KEY = 'sk-ant-...'", language="toml")
        return
    
    # 메인 레이아웃
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # 질문 입력 영역
        st.subheader("💬 AI 튜터와 대화하기")
        
        # 질문 입력
        user_question = st.text_area(
            "질문을 입력하세요:",
            placeholder="예: 뉴턴의 법칙에 대해 설명해주세요",
            height=100,
            key="user_input"
        )
        
        # 버튼들
        col_a, col_b, col_c = st.columns([2, 1, 1])
        
        with col_a:
            ask_button = st.button("📝 질문하기", type="primary", use_container_width=True)
        
        with col_b:
            clear_chat = st.button("🗑️ 대화 지우기", use_container_width=True)
        
        with col_c:
            if st.button("🏠 메인으로", use_container_width=True):
                st.switch_page("app.py")
        
        # 질문 처리
        if ask_button and user_question.strip():
            with st.spinner("🤔 AI 튜터가 답변을 준비하고 있어요..."):
                # 시스템 프롬프트 생성
                system_prompt = generate_system_prompt(teacher)
                
                # Claude API 호출
                ai_response = get_claude_response(user_question, system_prompt, st.session_state.chat_history)
                
                # 대화 히스토리에 추가
                st.session_state.chat_history.append({
                    'role': 'user',
                    'content': user_question,
                    'timestamp': datetime.now()
                })
                
                st.session_state.chat_history.append({
                    'role': 'assistant', 
                    'content': ai_response,
                    'timestamp': datetime.now()
                })
            
            # 입력창 비우기
            st.session_state.user_input = ""
            st.rerun()
        
        elif ask_button:
            st.warning("질문을 입력해주세요!")
        
        # 대화 지우기
        if clear_chat:
            st.session_state.chat_history = []
            st.success("대화 기록을 모두 지웠습니다!")
            st.rerun()
        
        # 대화 기록 표시
        if st.session_state.chat_history:
            st.subheader("💭 대화 기록")
            
            # 대화를 역순으로 표시 (최신이 위로)
            for i, msg in enumerate(reversed(st.session_state.chat_history)):
                timestamp = msg['timestamp'].strftime("%H:%M:%S")
                
                if msg['role'] == 'user':
                    with st.container():
                        st.markdown(f"""
                        <div style="background: #e3f2fd; 
                                    padding: 15px; 
                                    border-radius: 10px; 
                                    margin: 10px 0; 
                                    border-left: 4px solid #2196f3;">
                            <strong>👤 학생 [{timestamp}]:</strong><br>
                            {msg['content']}
                        </div>
                        """, unsafe_allow_html=True)
                
                else:  # assistant
                    with st.container():
                        st.markdown(f"""
                        <div style="background: #f3e5f5; 
                                    padding: 15px; 
                                    border-radius: 10px; 
                                    margin: 10px 0; 
                                    border-left: 4px solid #9c27b0;">
                            <strong>🤖 {teacher['name']} AI 튜터 [{timestamp}]:</strong>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 응답 내용 포맷팅해서 표시
                        formatted_response = format_response(msg['content'])
                        st.markdown(formatted_response)
                        
                        # 음성으로 듣기 버튼
                        if st.button(f"🔊 음성으로 듣기", key=f"tts_{i}"):
                            # 간단한 TTS 요약
                            summary = "답변을 확인해주세요. 추가 질문이 있으시면 언제든 말씀해주세요!"
                            
                            st.markdown(f"""
                            <script>
                            try {{
                                const utterance = new SpeechSynthesisUtterance('{summary}');
                                utterance.lang = 'ko-KR';
                                utterance.rate = 1.0;
                                
                                // 한국어 음성 찾기
                                const voices = speechSynthesis.getVoices();
                                const koreanVoice = voices.find(voice => 
                                    voice.lang && voice.lang.toLowerCase().includes('ko')
                                );
                                if (koreanVoice) {{
                                    utterance.voice = koreanVoice;
                                }}
                                
                                speechSynthesis.speak(utterance);
                            }} catch (error) {{
                                console.error('TTS Error:', error);
                            }}
                            </script>
                            """, unsafe_allow_html=True)
                            
                            st.success("🔊 음성 재생 중...")
        
        else:
            # 시작 안내
            st.info("""
            👋 안녕하세요! AI 튜터와의 첫 대화를 시작해보세요.
            
            **💡 질문 예시:**
            - "안녕하세요! 자기소개 해주세요"
            - "뉴턴의 법칙에 대해 설명해주세요"
            - "이차방정식 풀이 방법을 알려주세요"
            - "영어 과거시제 사용법이 궁금해요"
            
            자연스럽게 대화하듯이 질문해주세요! 😊
            """)
    
    with col2:
        # 사이드바 정보
        st.subheader("🎛️ 컨트롤")
        
        # 현재 상태
        st.subheader("📊 현재 상태")
        st.success("✅ Claude API 연결됨")
        st.info(f"💬 대화 수: {len(st.session_state.chat_history)//2}회")
        
        # 튜터 정보
        st.subheader("👨‍🏫 AI 튜터 정보")
        st.write(f"**이름:** {teacher['name']}")
        st.write(f"**전문분야:** {teacher['subject']}")
        st.write(f"**교육수준:** {teacher['level']}")
        
        personality = teacher.get('personality', {})
        st.write(f"**친근함:** {personality.get('friendliness', 70)}/100")
        st.write(f"**유머수준:** {personality.get('humor_level', 30)}/100")
        st.write(f"**격려수준:** {personality.get('encouragement', 80)}/100")
        
        # 사용법
        st.subheader("💡 사용법")
        st.markdown("""
        **🎯 현재 기능:**
        - ✅ **진짜 AI 대화** (Claude 연동)
        - ✅ **대화 맥락 유지** (이전 대화 기억)
        - ✅ **자연스러운 대화** (연속 질답)
        - ✅ **음성으로 듣기** (간단한 TTS)
        
        **📝 대화 팁:**
        - 자연스럽게 대화하듯이 질문
        - 이전 답변에 대한 추가 질문 가능
        - "더 쉽게 설명해주세요" 같은 요청 가능
        
        **🚀 업데이트 예정:**
        - 실시간 음성 인식
        - 고급 음성 합성
        - 실시간 스트리밍
        """)
        
        # 빠른 질문 버튼들
        st.subheader("⚡ 빠른 질문")
        
        quick_questions = [
            "안녕하세요! 자기소개 해주세요",
            "오늘 뭘 배워볼까요?",
            "어려운 개념을 쉽게 설명하는 비법이 있나요?",
            "학습에 도움되는 팁을 알려주세요"
        ]
        
        for i, question in enumerate(quick_questions):
            if st.button(question, key=f"quick_{i}", use_container_width=True):
                st.session_state.user_input = question
                st.rerun()

if __name__ == "__main__":
    main()
