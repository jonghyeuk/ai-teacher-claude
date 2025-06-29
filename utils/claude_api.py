import os
from anthropic import Anthropic
import streamlit as st
from typing import List, Dict

def get_claude_client():
    """Claude API 클라이언트 초기화"""
    # Streamlit Secrets에서 먼저 확인 (우선순위)
    api_key = None
    
    try:
        if hasattr(st, 'secrets'):
            api_key = st.secrets.get('ANTHROPIC_API_KEY')
            if api_key:
                st.success(f"✅ Claude API 키 확인됨 (길이: {len(api_key)})")
    except Exception as e:
        st.warning(f"Secrets 읽기 실패: {str(e)}")
    
    # 로컬 환경변수 백업
    if not api_key:
        api_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not api_key:
        st.error("❌ Claude API 키가 설정되지 않았습니다. Streamlit Secrets에 ANTHROPIC_API_KEY를 설정해주세요.")
        st.info("🔧 App 설정 → Secrets 탭에서 설정하세요")
        return None
    
    try:
        return Anthropic(api_key=api_key)
    except Exception as e:
        st.error(f"❌ Claude API 클라이언트 생성 실패: {str(e)}")
        return None

def generate_system_prompt(teacher_config: Dict) -> str:
    """AI 튜터의 시스템 프롬프트 생성"""
    personality = teacher_config['personality']
    
    # 기본 역할 설정
    base_prompt = f"""당신은 {teacher_config['name']}이라는 이름의 AI 튜터입니다. 
{teacher_config['subject']} 분야의 전문가이며, {teacher_config['level']} 수준의 학생들을 가르칩니다.

당신의 성격과 특성:
- 친근함 수준: {personality['friendliness']}/100 (0: 매우 엄격 ↔ 100: 매우 친근)
- 유머 수준: {personality['humor_level']}/100 (0: 진지함 ↔ 100: 유머러스)
- 격려 수준: {personality['encouragement']}/100 (0: 객관적 ↔ 100: 매우 격려적)
- 설명 상세도: {personality['explanation_detail']}/100 (0: 간단명료 ↔ 100: 매우 상세)
- 이론-실습 균형: {personality['theory_vs_practice']}/100 (0: 이론 중심 ↔ 100: 실습 중심)
- 안전 강조: {personality['safety_emphasis']}/100 (실험/실습 시 안전 주의사항 강조)
- 자연스러운 말투: {personality['natural_speech']}/100 (끊어지는 말, 되묻기 등)
- 어휘 수준: {personality['vocabulary_level']}/100 (0: 쉬운 어휘 ↔ 100: 전문 용어)

중요한 규칙:
1. 학생과의 대화에서는 항상 교육적이고 도움이 되도록 답변하세요.
2. 칠판에 쓸 내용이 있다면 다음 형식을 사용하세요:
   - 제목: ## 제목
   - 중요한 내용: **내용** 또는 [RED]내용[/RED]
   - 수식: $수식$ 또는 [BLUE]$수식$[/BLUE]
   - 강조할 부분: [CIRCLE]내용[/CIRCLE]
   - 색상 구분: [RED], [BLUE], [GREEN] 태그 사용

3. 음성으로 읽힐 내용이므로 자연스럽고 말하기 쉬운 문장으로 구성하세요.
4. 학생의 수준에 맞는 어휘와 설명을 사용하세요.
5. 안전과 관련된 내용은 반드시 강조해서 설명하세요.
"""
    
    # 성격별 추가 지침
    if personality['friendliness'] > 70:
        base_prompt += "\n- 친근하고 따뜻한 말투로 대화하세요. 학생을 격려하고 응원해주세요."
    elif personality['friendliness'] < 30:
        base_prompt += "\n- 전문적이고 엄격한 태도를 유지하세요. 정확한 정보 전달에 집중하세요."
    
    if personality['humor_level'] > 60:
        base_prompt += "\n- 적절한 유머와 재미있는 예시를 사용해서 학습을 즐겁게 만드세요."
    
    if personality['natural_speech'] > 60:
        base_prompt += "\n- 실제 선생님처럼 자연스럽게 말하세요. 가끔 '음...', '그러니까', '잠깐만요' 같은 자연스러운 표현을 사용하세요."
    
    if personality['theory_vs_practice'] > 60:
        base_prompt += "\n- 실험이나 실습 위주로 설명하고, 직접 해볼 수 있는 활동을 제안하세요."
    else:
        base_prompt += "\n- 이론적 배경과 원리를 중심으로 체계적으로 설명하세요."
    
    return base_prompt

def get_claude_response(user_message: str, system_prompt: str, chat_history: List[Dict]) -> str:
    """Claude API를 통해 응답 생성"""
    client = get_claude_client()
    if not client:
        return "죄송합니다. AI 서비스에 연결할 수 없습니다."
    
    try:
        # 대화 히스토리 준비
        messages = []
        
        # 최근 대화만 포함 (토큰 제한 고려)
        recent_history = chat_history[-10:] if len(chat_history) > 10 else chat_history
        
        for msg in recent_history:
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
            max_tokens=2000,
            temperature=0.7,
            system=system_prompt,
            messages=messages
        )
        
        return response.content[0].text
        
    except Exception as e:
        st.error(f"Claude API 호출 중 오류: {str(e)}")
        return f"죄송합니다. 응답을 생성하는 중 오류가 발생했습니다: {str(e)}"

def generate_lesson_content(topic: str, teacher_config: Dict) -> str:
    """특정 주제에 대한 수업 내용 생성"""
    system_prompt = generate_system_prompt(teacher_config)
    
    lesson_request = f"""
    '{topic}'에 대한 수업을 진행해주세요. 다음과 같이 구성해주세요:
    
    1. 주제 소개와 학습 목표
    2. 주요 개념 설명 (칠판에 정리할 내용 포함)
    3. 실제 예시나 실험 (가능한 경우)
    4. 중요 포인트 정리
    5. 학생들에게 질문 던지기
    
    칠판에 쓸 내용은 반드시 포맷팅 태그를 사용해주세요.
    """
    
    client = get_claude_client()
    if not client:
        return "API 연결에 실패했습니다."
    
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=2000,
            temperature=0.7,
            system=system_prompt,
            messages=[{"role": "user", "content": lesson_request}]
        )
        return response.content[0].text
    except Exception as e:
        return f"수업 내용 생성 중 오류가 발생했습니다: {str(e)}"

def check_api_status() -> bool:
    """Claude API 연결 상태 확인"""
    client = get_claude_client()
    if not client:
        return False
    
    try:
        # 간단한 테스트 메시지
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=10,
            messages=[{"role": "user", "content": "안녕하세요"}]
        )
        return True
    except:
        return False
