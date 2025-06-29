# AI 튜터 팩토리 Dockerfile

# Python 3.9 슬림 이미지 사용 (가벼우면서도 필요한 기능 포함)
FROM python:3.9-slim

# 메타데이터 설정
LABEL maintainer="AI Education Team <dev@ai-tutor-factory.com>"
LABEL description="AI 튜터 팩토리 - 맞춤형 AI 선생님 생성 플랫폼"
LABEL version="1.0.0"

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_ENV=production

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 종속성 먼저 복사 및 설치 (캐시 최적화)
COPY requirements.txt .

# pip 업그레이드 및 패키지 설치
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 필요한 디렉토리 생성
RUN mkdir -p data logs uploads temp

# 권한 설정
RUN chmod +x run.py

# 포트 노출
EXPOSE 8501

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# 앱 실행 (non-root 사용자로)
RUN useradd -m -u 1000 streamlit && chown -R streamlit:streamlit /app
USER streamlit

# Streamlit 앱 실행
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]

# ==============================================================================
# 빌드 및 실행 명령어 예시:
# 
# 이미지 빌드:
# docker build -t ai-tutor-factory .
#
# 컨테이너 실행 (기본):
# docker run -p 8501:8501 ai-tutor-factory
#
# 환경 변수와 함께 실행:
# docker run -p 8501:8501 \
#   -e ANTHROPIC_API_KEY=your_api_key \
#   -e GOOGLE_CLOUD_CREDENTIALS='{"type": "service_account", ...}' \
#   ai-tutor-factory
#
# 볼륨 마운트와 함께 실행 (데이터 영속성):
# docker run -p 8501:8501 \
#   -v $(pwd)/data:/app/data \
#   -e ANTHROPIC_API_KEY=your_api_key \
#   ai-tutor-factory
#
# 백그라운드 실행:
# docker run -d -p 8501:8501 \
#   -e ANTHROPIC_API_KEY=your_api_key \
#   --name ai-tutor \
#   ai-tutor-factory
# ==============================================================================
