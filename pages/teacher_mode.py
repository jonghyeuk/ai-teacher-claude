import streamlit as st
import json
import time
from datetime import datetime
import re

# --- [1] CSS 스타일 완전 적용 (반드시 누락 없이 삽입) ---
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
    font-family: 'NotoSansKR', 'Georgia', serif;
    font-size: 18px;
    line-height: 1.8;
    height: 400px;
    border: 8px solid #8B4513;
    box-shadow: 
        inset 0 0 30px rgba(0,0,0,0.3),
        0 10px 20px rgba(0,0,0,0.2);
    overflow-y: auto;
    white-space: pre-wrap;
    position: relative;
    scroll-behavior: smooth;
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
</style>
""", unsafe_allow_html=True)

st.set_page_config(
    page_title="AI 튜터 모드",
    page_icon="👨‍🏫",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- [2] Claude API 함수 ---
def get_claude_response(user_message, system_prompt, chat_history):
    try:
        from anthropic import Anthropic
        api_key = st.secrets.get('ANTHROPIC_API_KEY')
        if not api_key:
            return "API 키가 설정되지 않았습니다. Streamlit secrets에 ANTHROPIC_API_KEY를 설정해주세요."
        client = Anthropic(api_key=api_key)
        messages = []
        for msg in chat_history[-5:]:
            if msg['role'] in ['user', 'assistant']:
                messages.append({"role": msg['role'], "content": msg['content']})
        messages.append({"role": "user", "content": user_message})
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

# --- [3] 시스템 프롬프트 ---
def generate_system_prompt(teacher_config):
    personality = teacher_config.get('personality', {})
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

🔥 **매우 중요: 칠판 적극 활용 지침** 🔥
당신은 반드시 칠판을 적극적으로 사용해야 합니다! 다음 규칙을 엄격히 따르세요:

1. **핵심 개념/정의**: **핵심개념** 형태로 반드시 강조
2. **수식/공식**: $E=mc^2$, $F=ma$ 처럼 반드시 수식 표기 
3. **중요 단어**: [RED]매우중요[/RED], [BLUE]기억하세요[/BLUE], [GREEN]핵심포인트[/GREEN]
4. **단계별 설명**: 1단계, 2단계, 3단계로 구조화
5. **예시/결과**: → 결과: 이렇게 됩니다 (화살표 사용)

반드시 포함해야 할 칠판 요소:
- 제목: ## 오늘의 주제
- 정의: **중요개념 = 설명**
- 공식: $공식$ 
- 강조: [RED]주의사항[/RED]
- 예시: → 예: 구체적 사례
- 정리: [BLUE]**정리: 핵심 내용**[/BLUE]

말로만 설명하지 말고, 학생이 칠판을 보면서 이해할 수 있도록 시각적으로 정리해주세요!

학생들에게 도움이 되는 교육적이고 참여도 높은 답변을 해주세요."""

# --- [4] 칠판 텍스트 포맷 ---
def format_blackboard_text(text):
    text = re.sub(r'\$\$([^$]+)\$\$', r'<div class="formula" style="font-size: 24px; margin: 20px 0;">\1</div>', text)
    text = re.sub(r'\$([^$]+)\$', r'<div class="formula">\1</div>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<span class="important">\1</span>', text)
    text = re.sub(r'\[RED\]([^[]+)\[/RED\]', r'<span class="highlight-red">\1</span>', text)
    text = re.sub(r'\[BLUE\]([^[]+)\[/BLUE\]', r'<span class="highlight-blue">\1</span>', text)
    text = re.sub(r'\[GREEN\]([^[]+)\[/GREEN\]', r'<span class="highlight-green">\1</span>', text)
    text = re.sub(r'\[CIRCLE\]([^[]+)\[/CIRCLE\]', r'<span class="circle">\1</span>', text)
    text = re.sub(r'##\s*([^#\n]+)', r'<h2 style="color: #FFD700; text-align: center; margin: 20px 0; border-bottom: 2px solid #FFD700; padding-bottom: 10px;">\1</h2>', text)
    text = re.sub(r'🔹\s*([^\n]+)', r'<div style="background: rgba(255,215,0,0.2); padding: 10px; border-left: 4px solid #FFD700; margin: 10px 0;">\1</div>', text)
    text = re.sub(r'💡\s*([^\n]+)', r'<div style="background: rgba(255,107,107,0.2); padding: 10px; border-left: 4px solid #FF6B6B; margin: 10px 0;">💡 \1</div>', text)
    text = re.sub(r'📋\s*([^\n]+)', r'<div style="background: rgba(81,207,102,0.2); padding: 10px; border-left: 4px solid #51CF66; margin: 10px 0;">📋 \1</div>', text)
    return text

# --- [5] 칠판+타이핑+음성+EQ 콤보 컴포넌트 ---
def blackboard_tts_typing_combo(text, speed=1.0, pitch=1.0):
    clean_text = re.sub(r'\[.*?\]', '', text).replace('\n', ' ').replace('"', '').replace("'", '')[:400]
    safe_text = clean_text.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
    html = f"""
    <div id="combo-board" style="padding:20px;background:linear-gradient(135deg,#1a3d3a 0%,#2d5652 60%,#1a3d3a 100%);border-radius:16px;">
      <div style="font-size:22px;font-family:'NotoSansKR',monospace;min-height:68px;" id="typing-ani"></div>
      <div id="eq-bar" style="height:34px;display:flex;align-items:end;margin:12px 0 18px 0;"></div>
      <button id="tts-btn" onclick="startTTSAndTyping()" style="padding:14px 38px;background:#4CAF50;color:white;border:none;border-radius:23px;font-weight:bold;font-size:17px;box-shadow:0 2px 10px rgba(76,175,80,0.16);">🔊 음성+칠판 재생</button>
      <div id="tts-status" style="margin-top:10px;font-size:13px;opacity:0.9;color:#FFD700;"></div>
    </div>
    <script>
    let comboTxt = "{safe_text}";
    let curIdx = 0;
    let typeIntv = null;
    function fakeEQAnim(on) {{
        const eq = document.getElementById("eq-bar");
        if(!eq) return;
        if(on) {{
            eq.innerHTML = '';
            for(let i=0;i<16;i++) {{
                let bar = document.createElement('div');
                bar.style.width='8px';
                bar.style.margin='0 2px';
                bar.style.background='#FFD700';
                bar.style.height='20px';
                bar.style.borderRadius='4px';
                bar.setAttribute('id','bar'+i);
                eq.appendChild(bar);
            }}
            window.eqLoop = setInterval(()=>{
                for(let i=0;i<16;i++) {{
                    let bar = document.getElementById('bar'+i);
                    if(bar) {{
                        bar.style.height = (10+Math.random()*32)+'px';
                        bar.style.opacity = 0.7+Math.random()*0.3;
                    }}
                }}
            }}, 95);
        }} else {{
            if(window.eqLoop) clearInterval(window.eqLoop);
            eq.innerHTML = '';
        }}
    }}
    function startTTSAndTyping() {{
        document.getElementById("tts-btn").disabled = true;
        document.getElementById("tts-status").innerText = '⏳ 음성/애니 재생 중...';
        // 타이핑 애니
        const el = document.getElementById("typing-ani");
        el.innerHTML = '';
        curIdx = 0;
        if(typeIntv) clearInterval(typeIntv);
        typeIntv = setInterval(()=>{
            if(curIdx < comboTxt.length) {{
                el.innerHTML += comboTxt[curIdx++];
            }} else {{
                clearInterval(typeIntv);
            }}
        }}, 32);
        // EQ
        fakeEQAnim(true);
        // TTS
        const u = new window.SpeechSynthesisUtterance(comboTxt);
        u.lang = "ko-KR";
        u.rate = {speed};
        u.pitch = {pitch};
        u.onend = function() {{
            fakeEQAnim(false);
            document.getElementById("tts-btn").disabled = false;
            document.getElementById("tts-status").innerText = '✅ 재생 완료. 다시 듣기 가능!';
        }}
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(u);
    }}
    </script>
    """
    return html

# --- [6] 세션 초기화 ---
def initialize_teacher():
    if 'selected_teacher' not in st.session_state:
        st.error("AI 튜터가 선택되지 않았습니다. 메인 페이지로 돌아가세요.")
        if st.button("🏠 메인 페이지로"):
            st.switch_page("app.py")
        return None
    teacher = st.session_state.selected_teacher
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'blackboard_content' not in st.session_state:
        st.session_state.blackboard_content = f"🎓 {teacher['name']}의 {teacher['subject']} 수업\n\n📚 교육 수준: {teacher['level']}\n\n수업을 시작할 준비가 되었습니다!\n마이크 버튼을 눌러 질문하거나 수업을 요청해보세요."
    if 'is_recording' not in st.session_state:
        st.session_state.is_recording = False
    return teacher

# --- [7] 메인 ---
def main():
    teacher = initialize_teacher()
    if not teacher:
        return
    st.markdown(f"""
    <div class="teacher-header">
        <h1>👨‍🏫 {teacher['name']}</h1>
        <p>{teacher['subject']} | {teacher['level']} 수준</p>
    </div>
    """, unsafe_allow_html=True)

    # 칠판 표시
    if st.session_state.blackboard_content:
        st.markdown(f'''
        <div class="blackboard">
            <h2>📚 AI 칠판</h2>
            <div>{format_blackboard_text(st.session_state.blackboard_content)}</div>
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

    # 콤보 컴포넌트
    if 'latest_ai_response' in st.session_state and st.session_state.latest_ai_response:
        st.components.v1.html(
            blackboard_tts_typing_combo(
                st.session_state.latest_ai_response,
                speed=teacher.get('voice_settings',{}).get('speed',1.0),
                pitch=teacher.get('voice_settings',{}).get('pitch',1.0)
            ), height=340
        )

    # 텍스트 입력
    user_text = st.text_input("질문을 입력하세요:", key="text_input", placeholder="예: 전자기 유도에 대해 설명해주세요")
    if st.button("📝 텍스트 전송", key="send_text"):
        if user_text:
            process_text_input(user_text)
            st.rerun()

# --- [8] 입력 및 응답 핸들러 ---
def process_text_input(user_input):
    try:
        if user_input:
            st.session_state.chat_history.append({
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now()
            })
            teacher = st.session_state.selected_teacher
            system_prompt = generate_system_prompt(teacher)
            with st.spinner("🤔 AI가 생각하고 있습니다..."):
                ai_response = get_claude_response(user_input, system_prompt, st.session_state.chat_history)
            if ai_response and "오류가 발생했습니다" not in ai_response:
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': ai_response,
                    'timestamp': datetime.now()
                })
                update_blackboard_with_response(ai_response)
                st.session_state.latest_ai_response = ai_response
                st.success("✅ AI 응답 완료! [음성+애니메이션] 버튼으로 확인하세요!")
                st.rerun()
            else:
                st.error(f"❌ AI 응답 오류: {ai_response}")
    except Exception as e:
        st.error(f"처리 중 오류: {str(e)}")
        st.exception(e)

def update_blackboard_with_response(response):
    blackboard_text = format_response_for_blackboard(response)
    timestamp = datetime.now().strftime("%H:%M")
    separator = f"\n\n🕐 {timestamp} - 새로운 설명\n{'🔥'*25}\n"
    if st.session_state.blackboard_content:
        if "수업을 시작할 준비가 되었습니다" not in st.session_state.blackboard_content:
            st.session_state.blackboard_content += separator + blackboard_text
        else:
            st.session_state.blackboard_content = f"🎓 AI 튜터 칠판\n{'='*50}\n{blackboard_text}"
    else:
        st.session_state.blackboard_content = f"🎓 AI 튜터 칠판\n{'='*50}\n{blackboard_text}"

def format_response_for_blackboard(response):
    lines = response.split('\n')
    formatted = ""
    title_found = False
    for line in lines:
        line = line.strip()
        if not line:
            formatted += "\n"
            continue
        if not title_found and (len(line) < 60 and any(keyword in line for keyword in ['에 대해', '란', '이란', '개념', '원리', '법칙', '공식', '정의'])):
            formatted += f"\n## 📚 {line}\n{'='*40}\n"
            title_found = True
            continue
        if ('=' in line and any(char in line for char in ['²', '³', '+', '-', '*', '/', '∆', 'π', '∑', '∫'])) or \
           (re.search(r'[A-Za-z]\s*=\s*[A-Za-z0-9]', line)) or \
           ('공식' in line and '=' in line):
            formatted += f"\n[BLUE]$$ {line.strip()} $$[/BLUE]\n"
            continue
        if ('정의:' in line or '개념:' in line or '이란' in line or '란' in line) and len(line) < 100:
            formatted += f"\n**🔹 정의**\n{line}\n"
            continue
        if re.match(r'^\d+[.)]\s*', line) or line.startswith('단계') or line.startswith('Step'):
            formatted += f"\n**{line}**\n"
            continue
        if line.startswith('예:') or line.startswith('예시:') or '예를 들어' in line[:20]:
            formatted += f"\n[GREEN]📋 {line}[/GREEN]\n"
            continue
        if line.startswith('결과:') or line.startswith('따라서') or line.startswith('결론적으로'):
            formatted += f"\n[RED]**💡 {line}**[/RED]\n"
            continue
        if any(keyword in line for keyword in ['중요', '핵심', '주의', '기억', '포인트', '반드시', '꼭', '절대', '특히']):
            formatted += f"\n[RED]**⚠️ {line}**[/RED]\n"
            continue
        if ('특징' in line or '특성' in line or '장점' in line or '단점' in line) and len(line) < 80:
            formatted += f"\n**🔸 {line}**\n"
            continue
        if len(line) > 5:
            formatted += f"  • {line}\n"
    if formatted.strip():
        formatted += f"\n{'─'*50}\n"
    return formatted

# --- [9] 앱 시작 ---
if __name__ == "__main__":
    main()
