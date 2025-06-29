# 🎓 AI 튜터 팩토리

맞춤형 AI 선생님을 생성하고 실시간으로 상호작용할 수 있는 교육 플랫폼입니다.

## ✨ 주요 기능

### 🛠️ AI 튜터 생성기
- **전문 분야 선택**: 물리학, 화학, 생물학, 수학 등 다양한 과목
- **교육 수준 설정**: 중학교부터 대학원까지
- **성격 커스터마이징**: 12가지 성격 특성을 슬라이더로 조절
  - 친근함, 유머 수준, 격려 수준, 설명 상세도
  - 이론-실습 균형, 안전 강조, 자연스러운 말투 등
- **음성 설정**: 속도, 높이, 자동 재생 옵션
- **참고 자료 업로드**: PDF, DOC, TXT 파일 지원

### 🎭 AI 튜터 실행 모드
- **실시간 칠판**: AI가 설명하면서 동시에 칠판에 내용 작성
  - 색상 강조 (빨강, 파랑, 초록)
  - 수식 렌더링 (LaTeX 지원)
  - 중요 부분 원표시 및 밑줄
- **Push-to-Talk 음성 인터페이스**: 마이크 버튼을 눌러서만 음성 입력
- **실시간 음성 합성**: Google Cloud TTS 또는 브라우저 TTS
- **대화 히스토리 관리**: 최근 대화 내용 표시

### 📚 프리셋 시스템
- **기본 프리셋**: 물리 교수님, 화학 실험 조교, 친근한 수학 선생님 등
- **사용자 프리셋**: 개인 설정 저장 및 공유
- **프리셋 가져오기/내보내기**: JSON 형식으로 설정 백업

### ☁️ 클라우드 저장
- **AI 튜터 자동 저장**: 생성한 모든 AI 튜터 클라우드에 보관
- **Recent 목록**: 최근 사용한 AI 튜터 빠른 접근
- **수업 내용 저장**: 칠판 내용과 대화 내용 마크다운으로 다운로드

## 🚀 빠른 시작

### 1. 설치

```bash
# 레포지토리 클론
git clone https://github.com/your-username/ai-teacher-claude.git
cd ai-teacher-claude

# 패키지 설치
pip install -r requirements.txt
```

### 2. 환경 설정

`.env` 파일을 생성하고 API 키를 설정하세요:

```bash
cp .env.example .env
```

`.env` 파일에 다음 정보를 입력:

```env
# Claude API 키 (필수)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Google Cloud TTS (선택사항)
GOOGLE_CLOUD_CREDENTIALS={"type": "service_account", ...}
```

### 3. 실행

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501`로 접속하세요.

## 📋 사용 가이드

### AI 튜터 생성하기

1. **기본 정보 입력**
   - AI 튜터 이름 (예: "김교수님")
   - 전문 분야 선택
   - 교육 수준 선택

2. **성격 설정**
   - 각 슬라이더를 조절하여 원하는 성격 설정
   - 프리셋을 사용하여 빠른 설정 가능

3. **참고 자료 업로드** (선택사항)
   - PDF, DOC, TXT 파일 업로드
   - 파일당 최대 10MB, 총 5개까지

4. **생성 및 실행**
   - "AI 튜터 생성하기" 버튼 클릭
   - 자동으로 튜터 모드로 이동

### AI 튜터와 상호작용하기

1. **음성으로 질문하기**
   - 🎤 버튼을 누르고 있는 동안 말하기
   - 버튼을 놓으면 자동으로 음성 전송

2. **칠판 확인하기**
   - AI가 설명하면서 실시간으로 칠판에 내용 작성
   - 중요한 부분은 색상과 강조로 표시

3. **특정 주제 요청하기**
   - 고급 설정에서 "특정 주제 요청" 사용
   - 원하는 주제를 직접 입력 가능

## 🛠️ 기술 스택

- **Frontend**: Streamlit
- **AI API**: Anthropic Claude 3 Sonnet
- **음성 처리**: Google Cloud Text-to-Speech
- **문서 처리**: PyPDF2, python-docx
- **저장소**: 로컬 JSON 파일 (클라우드 확장 가능)

## ⚙️ 시스템 요구사항

- Python 3.8 이상
- Anthropic API 키 (필수)
- Google Cloud 계정 (음성 기능 사용 시)
- 웹브라우저 (Chrome, Firefox, Safari 권장)

## 🔧 고급 설정

### 프리셋 커스터마이징

기본 프리셋을 수정하거나 새로운 프리셋을 만들 수 있습니다:

```python
# utils/preset_manager.py에서 DEFAULT_PRESETS 수정
"내 커스텀 튜터": {
    "subject": "컴퓨터과학",
    "level": "대학교",
    "personality": {
        "friendliness": 80,
        "humor_level": 60,
        # ... 기타 설정
    }
}
```

### 음성 설정 최적화

Google Cloud TTS를 사용할 때 더 나은 음질을 위해:

1. Google Cloud Console에서 TTS API 활성화
2. 서비스 계정 키 생성 및 다운로드
3. JSON 키를 환경 변수에 설정

### 칠판 스타일 수정

칠판 디자인을 변경하려면 `pages/teacher_mode.py`의 CSS 스타일을 수정하세요:

```css
.blackboard {
    background: #2d3748;  /* 배경색 */
    color: #e2e8f0;       /* 텍스트 색상 */
    font-family: 'Courier New', monospace;
}
```

## 📱 모바일 지원

- 반응형 디자인으로 모바일에서도 사용 가능
- 터치 친화적인 큰 마이크 버튼
- 모바일 브라우저의 음성 인식 지원

## 🚀 배포

### Streamlit Cloud 배포

1. GitHub에 코드 푸시
2. [Streamlit Cloud](https://streamlit.io/cloud) 접속
3. 레포지토리 연결 및 배포
4. Secrets에 API 키 설정

### Docker 배포

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 🆘 문제 해결

### 자주 묻는 질문

**Q: API 키 오류가 발생해요**
A: `.env` 파일에 올바른 Anthropic API 키가 설정되어 있는지 확인하세요.

**Q: 음성이 재생되지 않아요**
A: 브라우저에서 음성 재생을 허용했는지 확인하고, Google Cloud TTS 설정을 점검하세요.

**Q: 파일 업로드가 안 돼요**
A: 지원되는 파일 형식(PDF, DOC, TXT)인지, 파일 크기가 10MB 이하인지 확인하세요.

**Q: 칠판에 한글이 깨져 보여요**
A: 브라우저 인코딩을 UTF-8로 설정하고 페이지를 새로고침하세요.

### 로그 확인

개발 모드에서 자세한 로그를 확인하려면:

```bash
export STREAMLIT_ENV=development
streamlit run app.py
```

## 📞 지원

- 이슈 리포트: [GitHub Issues](https://github.com/your-username/ai-teacher-claude/issues)
- 기능 요청: [Discussions](https://github.com/your-username/ai-teacher-claude/discussions)
- 이메일: support@ai-teacher.com

## 🙏 감사의 말

- [Anthropic](https://www.anthropic.com)의 Claude API
- [Streamlit](https://streamlit.io) 팀
- [Google Cloud](https://cloud.google.com) TTS 서비스
- 모든 기여자들과 베타 테스터들

---

**Made with ❤️ for Education**
