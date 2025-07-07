"""
실시간 AI 튜터 시스템 - FastAPI 백엔드 서버
2단계: 성능과 비용의 균형 구성
- STT: Google Cloud Speech-to-Text Streaming 
- LLM: GPT-3.5 Turbo Streaming (비용 최적화)
- TTS: Google Cloud TTS Standard (비용 최적화)
- 배포: Google Cloud Run (Scale to Zero)
"""

import asyncio
import json
import base64
import io
import os
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# OpenAI 및 Google Cloud (신버전)
from openai import AsyncOpenAI
from google.cloud import texttospeech

# 오디오 처리
import numpy as np
import soundfile as sf

# 환경 설정 (Cloud Run 환경변수에서 로드)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# FastAPI 앱 초기화
app = FastAPI(
    title="AI Tutor Realtime System", 
    version="2.0.0",
    description="실시간 음성 대화 AI 튜터 (성능과 비용 균형 구성)"
)

# CORS 설정 (Streamlit Cloud와 통신용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://*.streamlit.app",  # Streamlit Cloud 도메인
        "https://streamlit.app",
        "http://localhost:*",  # 로컬 개발용
        "*"  # 개발용 (프로덕션에서는 제거)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 클라이언트 초기화
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Google TTS 클라이언트 초기화
try:
    tts_client = texttospeech.TextToSpeechClient()
    print("✅ Google TTS 클라이언트 초기화 완료")
except Exception as e:
    print(f"⚠️ Google TTS 클라이언트 초기화 실패: {e}")
    tts_client = None

class ConnectionManager:
    """WebSocket 연결 관리자"""
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"✅ 클라이언트 {client_id} 연결됨 (총 {len(self.active_connections)}개)")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            print(f"❌ 클라이언트 {client_id} 연결 해제됨 (총 {len(self.active_connections)}개)")
    
    async def send_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                await websocket.send_json(message)
            except Exception as e:
                print(f"⚠️ 메시지 전송 실패 ({client_id}): {e}")
                self.disconnect(client_id)
    
    async def send_audio(self, audio_data: bytes, client_id: str):
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                await websocket.send_bytes(audio_data)
            except Exception as e:
                print(f"⚠️ 오디오 전송 실패 ({client_id}): {e}")
                self.disconnect(client_id)

manager = ConnectionManager()

class AITutorPipeline:
    """AI 튜터 파이프라인 (STT → LLM → TTS)"""
    
    def __init__(self, teacher_config: dict):
        self.teacher_config = teacher_config
        self.conversation_history = []
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        teacher_name = self.teacher_config.get('name', 'AI 튜터')
        subject = self.teacher_config.get('subject', '일반')
        level = self.teacher_config.get('level', '중급')
        
        return f"""당신은 {teacher_name}이라는 이름의 AI 튜터입니다.
{subject} 분야의 전문가이며, {level} 수준의 학생들을 가르칩니다.

교육 방식:
- 학생의 수준에 맞춰 설명
- 이해하기 쉬운 예시 활용  
- 질문을 격려하고 친근하게 응답
- 중요한 내용은 강조하여 설명

답변할 때는 자연스럽게 "음~", "그러니까", "잠깐만" 같은 추임새를 사용하고,
학생이 이해했는지 중간중간 확인해주세요.

답변은 간결하면서도 이해하기 쉽게 해주세요. 한 번에 너무 긴 설명보다는 
대화형으로 진행해주세요."""

    async def process_audio_to_text(self, audio_data: bytes) -> str:
        """
        오디오 데이터를 텍스트로 변환
        
        TODO: Google Cloud Speech-to-Text Streaming API 연동
        현재는 임시 구현 (실제 STT 구현 시 교체 필요)
        """
        try:
            print(f"🎤 오디오 데이터 수신: {len(audio_data)} bytes")
            
            # TODO: 실제 STT 구현
            # Google Cloud Speech-to-Text Streaming API 또는 Deepgram 연동
            
            # 임시 테스트용 텍스트들 (실제 구현 시 제거)
            test_texts = [
                "안녕하세요, 뉴턴의 법칙에 대해 설명해주세요.",
                "미적분학이 어려워요. 쉽게 설명해주실 수 있나요?",
                "물리학과 수학의 관계에 대해 궁금해요.",
                "과제 도움이 필요해요."
            ]
            
            import random
            return random.choice(test_texts)
            
        except Exception as e:
            print(f"❌ STT 오류: {e}")
            return ""
    
    async def generate_response_stream(self, user_text: str, client_id: str):
        """GPT-3.5 Turbo 스트리밍 응답 생성 및 실시간 TTS"""
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                *self.conversation_history[-10:],  # 최근 10개 대화만 유지
                {"role": "user", "content": user_text}
            ]
            
            print(f"🤖 GPT-3.5 Turbo 스트리밍 시작: {user_text[:50]}...")
            
            # GPT-3.5 Turbo 스트리밍 호출 (비용 최적화)
            response = await openai_client.chat.completions.create(
                model="gpt-3.5-turbo",  # 비용 절약
                messages=messages,
                stream=True,
                temperature=0.7,
                max_tokens=300  # 응답 길이 제한으로 비용 절약
            )
            
            current_sentence = ""
            full_response = ""
            
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    current_sentence += content
                    full_response += content
                    
                    # 문장 단위로 TTS 처리 (자연스러운 실시간 음성)
                    if any(punct in content for punct in ['.', '!', '?', '다', '요', '죠', '니다']):
                        sentence = current_sentence.strip()
                        if len(sentence) > 5:  # 너무 짧은 문장 제외
                            await self.text_to_speech_and_send(sentence, client_id)
                            current_sentence = ""
            
            # 마지막 남은 텍스트 처리
            if current_sentence.strip():
                await self.text_to_speech_and_send(current_sentence.strip(), client_id)
            
            # 대화 히스토리에 추가
            self.conversation_history.extend([
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": full_response}
            ])
            
            print(f"✅ 응답 완료: {len(full_response)} 글자")
            return full_response
            
        except Exception as e:
            print(f"❌ GPT 스트리밍 오류: {e}")
            await manager.send_message({
                "type": "error",
                "message": f"응답 생성 중 오류가 발생했습니다: {str(e)}"
            }, client_id)
    
    async def text_to_speech_and_send(self, text: str, client_id: str):
        """텍스트를 Google TTS Standard로 변환하고 클라이언트에 전송"""
        try:
            if not tts_client:
                print("⚠️ TTS 클라이언트가 초기화되지 않았습니다.")
                # TTS 없이 텍스트만 전송
                await manager.send_message({
                    "type": "text_chunk",
                    "content": text,
                    "audio": False
                }, client_id)
                return
            
            # Google TTS 설정 (Standard 모델로 비용 절약)
            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code="ko-KR",
                name="ko-KR-Standard-A",  # WaveNet 대신 Standard (비용 1/4)
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=1.1,  # 자연스러운 속도
                pitch=0.0
            )
            
            print(f"🎵 TTS 생성 중: {text[:30]}...")
            
            response = tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Base64로 인코딩하여 JSON으로 전송
            audio_base64 = base64.b64encode(response.audio_content).decode('utf-8')
            
            await manager.send_message({
                "type": "audio_chunk",
                "content": text,
                "audio": audio_base64,
                "format": "mp3"
            }, client_id)
            
            print(f"✅ TTS 전송 완료: {len(response.audio_content)} bytes")
                
        except Exception as e:
            print(f"❌ TTS 오류: {e}")
            # TTS 실패 시 텍스트만 전송
            await manager.send_message({
                "type": "text_chunk",
                "content": text,
                "audio": False,
                "error": "TTS 생성 실패"
            }, client_id)

# WebSocket 엔드포인트
@app.websocket("/ws/tutor/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    
    # 기본 튜터 설정 (클라이언트에서 커스터마이징 가능)
    teacher_config = {
        "name": "김선생",
        "subject": "수학",
        "level": "고등학교",
        "personality": {
            "friendliness": 80,
            "humor_level": 40,
            "encouragement": 90
        }
    }
    
    pipeline = AITutorPipeline(teacher_config)
    
    try:
        # 연결 확인 메시지
        await manager.send_message({
            "type": "connection_established",
            "message": f"🎓 AI 튜터 {teacher_config['name']}과 연결되었습니다!",
            "config": teacher_config
        }, client_id)
        
        while True:
            try:
                # 클라이언트로부터 데이터 수신
                data = await websocket.receive()
                
                if data["type"] == "websocket.receive":
                    if "bytes" in data:
                        # 오디오 데이터 수신 (마이크 입력)
                        audio_data = data["bytes"]
                        print(f"🎤 오디오 수신: {len(audio_data)} bytes")
                        
                        # STT 처리
                        user_text = await pipeline.process_audio_to_text(audio_data)
                        
                        if user_text:
                            # STT 결과 전송
                            await manager.send_message({
                                "type": "stt_result",
                                "text": user_text
                            }, client_id)
                            
                            # GPT-3.5 응답 생성 및 TTS 스트리밍
                            await pipeline.generate_response_stream(user_text, client_id)
                    
                    elif "text" in data:
                        # 텍스트 메시지 수신 (설정 변경, 텍스트 입력 등)
                        try:
                            message = json.loads(data["text"])
                            
                            if message["type"] == "config_update":
                                # 튜터 설정 업데이트
                                teacher_config.update(message["config"])
                                pipeline = AITutorPipeline(teacher_config)
                                
                                await manager.send_message({
                                    "type": "config_updated",
                                    "message": "✅ 설정이 업데이트되었습니다.",
                                    "config": teacher_config
                                }, client_id)
                            
                            elif message["type"] == "text_input":
                                # 텍스트 직접 입력 (오디오 없이)
                                user_text = message["text"]
                                await pipeline.generate_response_stream(user_text, client_id)
                                
                        except json.JSONDecodeError:
                            await manager.send_message({
                                "type": "error",
                                "message": "잘못된 메시지 형식입니다."
                            }, client_id)
            
            except Exception as e:
                print(f"⚠️ 메시지 처리 오류: {e}")
                await manager.send_message({
                    "type": "error",
                    "message": "메시지 처리 중 오류가 발생했습니다."
                }, client_id)
    
    except WebSocketDisconnect:
        print(f"🔌 클라이언트 {client_id} 정상 연결 해제")
        manager.disconnect(client_id)
    except Exception as e:
        print(f"❌ WebSocket 오류 ({client_id}): {e}")
        manager.disconnect(client_id)

# HTTP 엔드포인트들
@app.get("/")
async def root():
    return {
        "message": "🎓 AI Tutor Realtime System",
        "version": "2.0.0",
        "status": "running",
        "config": "성능과 비용 균형 구성",
        "endpoints": {
            "websocket": "/ws/tutor/{client_id}",
            "health": "/health",
            "info": "/info"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_connections": len(manager.active_connections),
        "services": {
            "openai": "✅" if OPENAI_API_KEY != "your-openai-api-key" else "❌",
            "google_tts": "✅" if tts_client else "❌"
        }
    }

@app.get("/info")
async def system_info():
    return {
        "system": "AI Tutor Realtime System",
        "architecture": "2단계: 성능과 비용 균형",
        "components": {
            "frontend": "Streamlit Cloud",
            "backend": "FastAPI on Google Cloud Run",
            "stt": "Google Cloud Speech-to-Text (TODO)",
            "llm": "GPT-3.5 Turbo Streaming",
            "tts": "Google Cloud TTS Standard",
            "communication": "WebSocket"
        },
        "features": [
            "실시간 음성 인식",
            "스트리밍 AI 응답", 
            "실시간 음성 합성",
            "양방향 WebSocket 통신",
            "비용 최적화된 AI 모델"
        ]
    }

# 서버 실행 함수 (Cloud Run 및 로컬 개발용)
def run_server():
    """
    서버 실행 함수
    - 로컬 개발: python pages/teacher_mode.py
    - Cloud Run: uvicorn pages.teacher_mode:app --host 0.0.0.0 --port $PORT
    """
    port = int(os.getenv("PORT", 8000))  # Cloud Run 환경변수
    
    uvicorn.run(
        app,  # 직접 app 객체 전달 (경로 문제 해결)
        host="0.0.0.0",
        port=port,
        reload=False,  # 프로덕션에서는 False
        log_level="info"
    )

if __name__ == "__main__":
    print("🚀 AI Tutor System 시작...")
    print(f"📍 포트: {os.getenv('PORT', 8000)}")
    print(f"🔑 OpenAI: {'✅' if OPENAI_API_KEY != 'your-openai-api-key' else '❌'}")
    print(f"🎵 Google TTS: {'✅' if tts_client else '❌'}")
    run_server()
