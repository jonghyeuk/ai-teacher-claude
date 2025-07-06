"""
실시간 AI 튜터 시스템 - FastAPI 백엔드 서버
Deepgram STT + GPT-4 Streaming + Google TTS
"""

import asyncio
import json
import base64
import io
from datetime import datetime
from typing import Dict, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# OpenAI 및 Google Cloud
import openai
from google.cloud import texttospeech

# 오디오 처리
import numpy as np
import soundfile as sf

# 환경 설정 (추후 secrets에서 로드)
OPENAI_API_KEY = "your-openai-api-key"  # 실제 구현 시 secrets에서 로드
GOOGLE_CREDENTIALS = {}  # 실제 구현 시 secrets에서 로드

# FastAPI 앱 초기화
app = FastAPI(title="AI Tutor Realtime System", version="1.0.0")

# CORS 설정 (Streamlit과 통신용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용, 프로덕션에서는 제한 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 클라이언트 초기화
openai.api_key = OPENAI_API_KEY
tts_client = None  # 실제 구현 시 Google TTS 클라이언트 초기화

# 연결된 클라이언트 관리
active_connections: Dict[str, WebSocket] = {}

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"클라이언트 {client_id} 연결됨")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            print(f"클라이언트 {client_id} 연결 해제됨")
    
    async def send_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            await websocket.send_json(message)
    
    async def send_audio(self, audio_data: bytes, client_id: str):
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            await websocket.send_bytes(audio_data)

manager = ConnectionManager()

class AITutorPipeline:
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

답변은 간결하면서도 이해하기 쉽게 해주세요."""

    async def process_audio_to_text(self, audio_data: bytes) -> str:
        """
        오디오 데이터를 텍스트로 변환 (Deepgram STT)
        
        ⚠️ 도움 필요: Deepgram API 정확한 사용법
        현재는 임시 구현 (실제로는 Deepgram 연동 필요)
        """
        try:
            # TODO: Deepgram API 연동 구현 필요
            # 현재는 임시 텍스트 반환
            print(f"오디오 데이터 수신: {len(audio_data)} bytes")
            return "안녕하세요, 뉴턴의 법칙에 대해 설명해주세요."  # 임시 반환
            
        except Exception as e:
            print(f"STT 오류: {e}")
            return ""
    
    async def generate_response_stream(self, user_text: str, client_id: str):
        """GPT-4 스트리밍 응답 생성 및 실시간 TTS"""
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                *self.conversation_history[-10:],  # 최근 10개 대화만 유지
                {"role": "user", "content": user_text}
            ]
            
            # GPT-4 스트리밍 호출
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=messages,
                stream=True,
                temperature=0.7,
                max_tokens=500
            )
            
            current_sentence = ""
            full_response = ""
            
            async for chunk in response:
                content = chunk.choices[0].delta.get("content", "")
                if content:
                    current_sentence += content
                    full_response += content
                    
                    # 문장 단위로 TTS 처리
                    if any(punct in content for punct in ['.', '!', '?', '다', '요', '죠']):
                        if len(current_sentence.strip()) > 10:
                            # 문장을 TTS로 변환하고 전송
                            await self.text_to_speech_and_send(current_sentence.strip(), client_id)
                            current_sentence = ""
            
            # 마지막 남은 텍스트 처리
            if current_sentence.strip():
                await self.text_to_speech_and_send(current_sentence.strip(), client_id)
            
            # 대화 히스토리에 추가
            self.conversation_history.extend([
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": full_response}
            ])
            
            return full_response
            
        except Exception as e:
            print(f"GPT-4 스트리밍 오류: {e}")
            await manager.send_message({
                "type": "error",
                "message": f"응답 생성 중 오류가 발생했습니다: {str(e)}"
            }, client_id)
    
    async def text_to_speech_and_send(self, text: str, client_id: str):
        """텍스트를 Google TTS로 변환하고 클라이언트에 전송"""
        try:
            # Google TTS 호출
            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code="ko-KR",
                name="ko-KR-Wavenet-A",
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=1.2,
                pitch=0.0
            )
            
            if tts_client:
                response = tts_client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config
                )
                
                # 오디오 데이터를 클라이언트에 전송
                await manager.send_audio(response.audio_content, client_id)
                
                # 텍스트 정보도 함께 전송 (칠판 표시용)
                await manager.send_message({
                    "type": "text_chunk",
                    "content": text
                }, client_id)
            else:
                print("TTS 클라이언트가 초기화되지 않았습니다.")
                
        except Exception as e:
            print(f"TTS 오류: {e}")

# WebSocket 엔드포인트
@app.websocket("/ws/tutor/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    
    # 기본 튜터 설정 (실제로는 클라이언트에서 받아야 함)
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
        await manager.send_message({
            "type": "connection_established",
            "message": f"AI 튜터 {teacher_config['name']}과 연결되었습니다!"
        }, client_id)
        
        while True:
            # 클라이언트로부터 데이터 수신
            data = await websocket.receive()
            
            if data["type"] == "websocket.receive":
                if "bytes" in data:
                    # 오디오 데이터 수신
                    audio_data = data["bytes"]
                    print(f"오디오 데이터 수신: {len(audio_data)} bytes")
                    
                    # STT 처리
                    user_text = await pipeline.process_audio_to_text(audio_data)
                    
                    if user_text:
                        await manager.send_message({
                            "type": "stt_result",
                            "text": user_text
                        }, client_id)
                        
                        # GPT-4 응답 생성 및 TTS 스트리밍
                        await pipeline.generate_response_stream(user_text, client_id)
                
                elif "text" in data:
                    # 텍스트 메시지 수신 (설정 변경 등)
                    message = json.loads(data["text"])
                    
                    if message["type"] == "config_update":
                        # 튜터 설정 업데이트
                        teacher_config.update(message["config"])
                        pipeline = AITutorPipeline(teacher_config)
                        
                        await manager.send_message({
                            "type": "config_updated",
                            "message": "설정이 업데이트되었습니다."
                        }, client_id)
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        print(f"WebSocket 오류: {e}")
        manager.disconnect(client_id)

# HTTP 엔드포인트 (상태 확인용)
@app.get("/")
async def root():
    return {
        "message": "AI Tutor Realtime System",
        "status": "running",
        "endpoints": {
            "websocket": "/ws/tutor/{client_id}",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_connections": len(manager.active_connections)
    }

# 서버 실행 함수
def run_server():
    """
    개발용 서버 실행 함수
    프로덕션에서는 gunicorn 등 사용 권장
    """
    uvicorn.run(
        "teacher_mode:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    run_server()
