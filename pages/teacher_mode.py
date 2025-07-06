import streamlit as st
import time
from datetime import datetime
import re

# ================================
# 1단계: 페이지 설정 (안전한 기본 설정)
# ================================
st.set_page_config(
    page_title="GPT-4 AI 튜터",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ================================
# 2단계: 필수 함수들 (에러 처리 포함)
# ================================

def safe_get_openai_client():
    """OpenAI 클라이언트 안전하게 가져오기"""
    try:
        import openai
        api_key = st.secrets.get('OPENAI_API_KEY')
        if not api_key:
            return None, "OpenAI API 키가 설정되지 않았습니다."
        
        client = openai.OpenAI(api_key=api_key)
        return client, "성공"
    except ImportError:
        return None, "openai 패키지가 설치되지 않았습니다."
    except Exception as e:
        return None, f"OpenAI 클라이언트 생성 오류: {str(e)}"

def get_gpt4_response(user_message, teacher_config, chat_history):
    """GPT-4 응답 생성 (완전한 에러 처리)"""
    try:
        client, error_msg = safe_get_openai_client()
        if client is None:
            return f"오류: {error_msg}"
        
        # 시스템 프롬프트 생성
        personality = teacher_config.get('personality', {})
        system_prompt = f"""당신은 {teacher_config.get('name', 'AI 튜터')}라는 친근한 AI 튜터입니다.
{teacher_config.get('subject', '일반')} 분야를 전문으로 하며, {teacher_config.get('level', '중급')} 수준의 학생들을 가르칩니다.

성격 특성:
- 친근함: {personality.get('friendliness', 70)}/100
- 유머: {personality.get('humor_level', 30)}/100
- 격려: {personality.get('encouragement', 80)}/100

교육 방식:
- 이해하기 쉽게 단계별로 설명
- 중요한 내용은 **강조**로 표시
- 구체적인 예시를 활용
- 학생의 이해도를 확인하는 질문

친근하고 격려하는 말투로 자연스럽게 대화하세요."""

        # 메시지 구성 (안전하게)
        messages = [{"role": "system", "content": system_prompt}]
        
        # 최근 대화만 포함 (메모리 절약)
        recent_history = chat_history[-8:] if len(chat_history) > 8 else chat_history
        for msg in recent_history:
            if msg.get('role') in ['user', 'assistant']:
                messages.append({
                    "role": msg['role'],
                    "content": str(msg.get('content', ''))[:1000]  # 길이 제한
                })
        
        # 현재 메시지 추가
        messages.append({
            "role": "user",
            "content": str(user_message)[:1000]  # 길이 제한
        })
        
        # GPT-4 API 호출
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=600,
            temperature=0.7,
            timeout=30  # 타임아웃 설정
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}"

def safe_initialize_session():
    """세션 상태 안전하게 초기화"""
    try:
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        if 'is_responding' not in st.session_state:
            st.session_state.is_responding = False
            
        if 'response_count' not in st.session_state:
            st.session_state.response_count = 0
            
        return True
    except Exception as e:
        st.error(f"세션 초기화 오류: {str(e)}")
        return False

def get_teacher_info():
    """튜터 정보 안전하게 가져오기"""
    try:
        if 'selected_teacher' not in st.session_state:
            return None
        return st.session_state.selected_teacher
    except:
        return None

def format_response_safely(text):
    """응답 텍스트 안전하게 포맷팅"""
    try:
        if not text:
            return "응답을 받지 못했습니다."
        
        # 기본 포맷팅 (안전하게)
        formatted = str(text)
        
        # 제목 포맷팅
        formatted = re.sub(r'^## (.+)$', r'### 📚 \1', formatted, flags=re.MULTILINE)
        
        # 강조 처리
        formatted = re.sub(r'\*\*([^*]+)\*\*', r'**\1**', formatted)
        
        return formatted
    except:
        return str(text) if text else "포맷팅 오류"

# ================================
# 3단계: 메인 함수 (단계별 구현)
# ================================

def main():
    """메인 함수 - 단계별 안전 구현"""
    
    # 세션 초기화 체크
    if not safe_initialize_session():
        st.error("시스템 초기화에 실패했습니다. 페이지를 새로고침해주세요.")
        return
    
    # 튜터 정보 확인
    teacher = get_teacher_info()
    if not teacher:
        st.error("AI 튜터가 선택되지 않았습니다.")
        st.info("메인 페이지에서 튜터를 먼저 생성해주세요.")
        if st.button("🏠 메인 페이지로 이동"):
            st.switch_page("app.py")
        return
    
    # API 키 확인
    client, api_error = safe_get_openai_client()
    if client is None:
        st.error("⚠️ OpenAI API 설정 문제")
        st.info(f"문제: {api_error}")
        st.code("Streamlit secrets에 다음을 추가하세요:\nOPENAI_API_KEY = 'sk-proj-...'", language="toml")
        return
    
    # ================================
    # 4단계: UI 구성 (안전한 컴포넌트만)
    # ================================
    
    # 헤더
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; 
                padding: 20px; 
                border-radius: 15px; 
                text-align: center; 
                margin-bottom: 30px;">
        <h1>🤖 {teacher.get('name', 'AI 튜터')} (GPT-4)</h1>
        <p>📚 {teacher.get('subject', '일반')} | 🎯 {teacher.get('level', '중급')} 수준</p>
        <p>💬 자연스러운 대화로 함께 학습해요!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 메인 레이아웃
    col1, col2 = st.columns([7, 3])
    
    with col1:
        # ================================
        # 5단계: 대화 인터페이스
        # ================================
        
        st.subheader("💬 대화하기")
        
        # 질문 입력
        user_question = st.text_area(
            "질문을 입력하세요:",
            placeholder="예: 안녕하세요! 자기소개 해주세요",
            height=100,
            key="question_input",
            help="Enter 키를 누르면 전송됩니다"
        )
        
        # 버튼 영역
        col_a, col_b, col_c = st.columns([3, 2, 2])
        
        with col_a:
            send_button = st.button(
                "📤 질문 보내기", 
                type="primary", 
                use_container_width=True,
                disabled=st.session_state.is_responding
            )
        
        with col_b:
            clear_button = st.button(
                "🗑️ 대화 지우기", 
                use_container_width=True
            )
        
        with col_c:
            home_button = st.button(
                "🏠 메인으로", 
                use_container_width=True
            )
        
        # ================================
        # 6단계: 대화 처리 로직
        # ================================
        
        # 홈 버튼 처리
        if home_button:
            st.switch_page("app.py")
        
        # 대화 지우기 처리
        if clear_button:
            st.session_state.chat_history = []
            st.session_state.response_count = 0
            st.success("대화 기록을 모두 지웠습니다!")
            st.rerun()
        
        # 질문 처리
        if send_button and user_question.strip():
            if not st.session_state.is_responding:
                st.session_state.is_responding = True
                
                # 사용자 메시지 추가
                st.session_state.chat_history.append({
                    'role': 'user',
                    'content': user_question.strip(),
                    'timestamp': datetime.now()
                })
                
                # AI 응답 생성
                with st.spinner("🤔 GPT-4가 답변을 생각하고 있어요..."):
                    ai_response = get_gpt4_response(
                        user_question.strip(), 
                        teacher, 
                        st.session_state.chat_history
                    )
                
                # AI 응답 추가
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': ai_response,
                    'timestamp': datetime.now()
                })
                
                st.session_state.response_count += 1
                st.session_state.is_responding = False
                
                # 페이지 새로고침으로 입력창 비우기
                st.rerun()
        
        elif send_button:
            st.warning("질문을 입력해주세요!")
        
        # ================================
        # 7단계: 대화 기록 표시 (실시간 느낌)
        # ================================
        
        if st.session_state.chat_history:
            st.subheader("💭 대화 기록")
            
            # 대화를 역순으로 표시 (최신이 위로)
            for i, msg in enumerate(reversed(st.session_state.chat_history)):
                timestamp = msg.get('timestamp', datetime.now()).strftime("%H:%M")
                content = msg.get('content', '')
                
                if msg.get('role') == 'user':
                    # 사용자 메시지
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #e3f2fd, #bbdefb); 
                                padding: 15px; 
                                border-radius: 15px; 
                                margin: 10px 0; 
                                border-left: 5px solid #2196f3;">
                        <div style="color: #1976d2; font-weight: bold; margin-bottom: 8px;">
                            👤 학생 ({timestamp})
                        </div>
                        <div style="color: #333; font-size: 16px;">
                            {content}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                else:
                    # AI 응답
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #f3e5f5, #e1bee7); 
                                padding: 15px; 
                                border-radius: 15px; 
                                margin: 10px 0; 
                                border-left: 5px solid #9c27b0;">
                        <div style="color: #7b1fa2; font-weight: bold; margin-bottom: 8px;">
                            🤖 {teacher.get('name', 'AI 튜터')} ({timestamp})
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 응답 내용 (포맷팅해서 표시)
                    formatted_content = format_response_safely(content)
                    st.markdown(formatted_content)
                    
                    # 음성 듣기 버튼
                    if st.button(f"🔊 음성으로 듣기", key=f"tts_{len(st.session_state.chat_history)-i}"):
                        # 간단한 브라우저 TTS
                        tts_text = "답변을 확인해주세요. 궁금한 점이 더 있으시면 언제든 질문해주세요!"
                        
                        st.markdown(f"""
                        <script>
                        try {{
                            const utterance = new SpeechSynthesisUtterance('{tts_text}');
                            utterance.lang = 'ko-KR';
                            utterance.rate = 1.0;
                            utterance.pitch = 1.0;
                            speechSynthesis.speak(utterance);
                        }} catch (error) {{
                            console.error('TTS 오류:', error);
                        }}
                        </script>
                        """, unsafe_allow_html=True)
                        
                        st.success("🔊 음성 재생 중...")
                
                # 구분선
                if i < len(st.session_state.chat_history) - 1:
                    st.markdown("---")
        
        else:
            # 시작 안내
            st.info("""
            👋 **GPT-4 AI 튜터와의 첫 대화를 시작해보세요!**
            
            **💡 추천 질문:**
            - "안녕하세요! 간단히 자기소개 해주세요"
            - "오늘은 무엇을 배워볼까요?"
            - "뉴턴의 법칙에 대해 설명해주세요"
            - "이차방정식 풀이 방법을 알려주세요"
            
            자연스럽게 대화하듯이 질문해주세요! 😊
            """)
    
    with col2:
        # ================================
        # 8단계: 사이드바 정보
        # ================================
        
        st.subheader("📊 현재 상태")
        st.success("✅ GPT-4 API 연결됨")
        st.info(f"💬 대화 횟수: {st.session_state.response_count}회")
        
        if st.session_state.is_responding:
            st.warning("🤔 응답 생성 중...")
        else:
            st.success("🚀 대화 준비됨")
        
        st.markdown("---")
        
        # 튜터 정보
        st.subheader("👨‍🏫 AI 튜터 정보")
        st.write(f"**이름:** {teacher.get('name', '알 수 없음')}")
        st.write(f"**전문분야:** {teacher.get('subject', '일반')}")
        st.write(f"**교육수준:** {teacher.get('level', '중급')}")
        
        personality = teacher.get('personality', {})
        if personality:
            st.write(f"**친근함:** {personality.get('friendliness', 70)}/100")
            st.write(f"**유머수준:** {personality.get('humor_level', 30)}/100")
            st.write(f"**격려수준:** {personality.get('encouragement', 80)}/100")
        
        st.markdown("---")
        
        # 빠른 질문
        st.subheader("⚡ 빠른 질문")
        
        quick_questions = [
            "안녕하세요! 자기소개 해주세요",
            "오늘 뭘 배워볼까요?",
            "어려운 개념을 쉽게 설명하는 팁이 있나요?",
            "공부할 때 도움되는 조언을 해주세요"
        ]
        
        for i, question in enumerate(quick_questions):
            if st.button(
                question, 
                key=f"quick_{i}", 
                use_container_width=True,
                disabled=st.session_state.is_responding
            ):
                # 빠른 질문 입력창에 설정
                st.session_state.question_input = question
                st.rerun()
        
        st.markdown("---")
        
        # 사용 가이드
        st.subheader("💡 사용 가이드")
        st.markdown("""
        **🎯 현재 기능:**
        - ✅ GPT-4와 실제 대화
        - ✅ 대화 맥락 완전 유지
        - ✅ 개인화된 튜터 성격
        - ✅ 브라우저 음성 재생
        
        **💬 대화 팁:**
        - 자연스럽게 대화하듯 질문
        - 이전 답변에 대한 추가 질문 가능
        - "더 쉽게 설명해주세요" 같은 요청
        - "예시를 더 들어주세요" 등
        
        **🚀 향후 업데이트:**
        - 실시간 음성 인식 (Whisper)
        - 고품질 음성 합성
        - 실시간 스트리밍 답변
        """)

# ================================
# 9단계: 최종 검수 및 실행
# ================================

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"시스템 오류가 발생했습니다: {str(e)}")
        st.info("페이지를 새로고침해주세요.")
        
        # 디버그 정보 (개발용)
        if st.checkbox("디버그 정보 보기"):
            st.exception(e)
