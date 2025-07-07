# Python 3.11 slim 이미지 사용
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt 복사 및 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 포트 8000 노출 (Cloud Run 기본 포트)
EXPOSE 8000

# 환경변수 설정 (Cloud Run용)
ENV PORT=8000

# FastAPI 서버 실행 (uvicorn 직접 사용)
CMD ["uvicorn", "pages.teacher_mode:app", "--host", "0.0.0.0", "--port", "8000"]
