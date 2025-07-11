#!/usr/bin/env python3
"""
AI 튜터 FastAPI 백엔드 애플리케이션

완전한 실시간 AI 튜터 시스템 백엔드입니다.
- 음성 입력 (STT) + 텍스트 입력 지원
- 실시간 WebSocket 통신
- GPT-3.5 Turbo 스트리밍 응답
- Google TTS 음성 출력
- 음성 중첩 문제 해결
- 튜터 개성화 시스템
"""

import asyncio
import base64
import json
import os
import tempfile
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import logging

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import AsyncOpenAI
from google.cloud import texttospeech
from google.cloud import speech
import httpx

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 초기화
app = FastAPI(
    title="AI Tutor Realtime System",
    description="실시간 AI 튜터 시스템 - 음성 및 텍스트 입력 지원",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://*.streamlit.app",
        "https://*.streamlit.io", 
        "http://localhost:8501",
        "http://localhost:3000",
        "http://localhost:8080",
        "*"  # 개발 환경용
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 환경변수 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
    raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")

# 클라이언트 초기화
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

try:
    tts_client = texttospeech.TextToSpeechClient()
    logger.info("Google TTS 클라이언트 초기화 성공")
except Exception as e:
    logger.error(f"Google TTS 클라이언트 초기화 실패: {e}")
    tts_client = None

try:
    speech_client = speech.SpeechClient()
    logger.info("Google STT 클라이언트 초기화 성공")
except Exception as e:
    logger.error(f"Google STT 클라이언트 초기화 실패: {e}")
    speech_client = None

# 전역 변수
active_connections: Dict[str, WebSocket] = {}
tutor_configs: Dict[str, Dict[str, Any]] = {}

# 기본 엔드포인트들
@app.get("/")
async def root():
    """메인 페이지 - 시스템 정보"""
    return {
        "message": "🎓 AI Tutor Realtime System",
        "version": "2.1.0",
        "status": "running",
        "features": [
            "음성 입력 (STT)",
            "텍스트 입력", 
            "음성 출력 (TTS)",
            "실시간 스트리밍",
            "튜터 개성화",
            "다중 입력 방식"
        ],
        "config": "성능과 비용 균형 구성",
        "endpoints": {
            "websocket": "/ws/tutor/{client_id}",
            "health": "/health",
            "info": "/info",
            "docs": "/docs"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    try:
        # OpenAI API 상태 확인
        openai_status = "✅ 연결됨" if OPENAI_API_KEY else "❌ API 키 없음"
        
        # Google TTS 상태 확인
        tts_status = "❌ 비활성화"
        if tts_client:
            try:
                voices = tts_client.list_voices()
                tts_status = f"✅ 활성화 ({len(voices.voices)}개 음성)"
            except Exception as e:
                tts_status = f"⚠️ 오류: {str(e)[:50]}"
        
        # Google STT 상태 확인
        stt_status = "✅ 활성화" if speech_client else "❌ 비활성화"
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "active_connections": len(active_connections),
            "active_tutors": len(tutor_configs),
            "services": {
                "openai_gpt": openai_status,
                "google_tts": tts_status,
                "google_stt": stt_status
            },
            "system": {
                "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
                "environment": os.getenv("ENVIRONMENT", "production")
            }
        }
    except Exception as e:
        logger.error(f"Health check 오류: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy", 
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/info")
async def system_info():
    """상세 시스템 정보"""
    return {
        "system": "AI Tutor Realtime System",
        "version": "2.1.0",
        "architecture": "마이크로서비스 아키텍처",
        "deployment": "Google Cloud Run",
        "input_methods": {
            "voice": {
                "engine": "Google Cloud Speech-to-Text",
                "supported_formats": ["WEBM_OPUS", "OGG_OPUS"],
                "languages": ["ko-KR", "en-US"],
                "features": ["자동 구두점", "신뢰도 점수", "다중 설정 시도"]
            },
            "text": {
                "method": "WebSocket 실시간 전송",
                "encoding": "UTF-8",
                "max_length": "10000자"
            }
        },
        "output_methods": {
            "text": {
                "streaming": True,
                "real_time": True,
                "format": "타이핑 효과"
            },
            "voice": {
                "engine": "Google Cloud Text-to-Speech",
                "voice": "ko-KR-Standard-A",
                "format": "MP3",
                "features": ["단일 오디오 출력", "중첩 방지"]
            }
        },
        "ai_model": {
            "provider": "OpenAI",
            "model": "GPT-3.5 Turbo",
            "streaming": True,
            "max_tokens": 300,
            "temperature": 0.7
        },
        "communication": {
            "protocol": "WebSocket",
            "real_time": True,
            "auto_reconnect": True,
            "timeout": "60초"
        },
        "tutor_system": {
            "personalization": True,
            "personality_traits": [
                "친근함", "유머 수준", "격려 수준", 
                "설명 상세도", "상호작용 빈도"
            ],
            "subjects": "무제한",
            "education_levels": ["중학교", "고등학교", "대학교", "대학원"]
        }
    }

@app.get("/stats")
async def get_statistics():
    """실시간 통계"""
    return {
        "connections": {
            "active": len(active_connections),
            "total_connected": len(active_connections)
        },
        "tutors": {
            "active": len(tutor_configs),
            "configurations": list(tutor_configs.keys())
        },
        "timestamp": datetime.now().isoformat()
    }

# WebSocket 엔드포인트
@app.websocket("/ws/tutor/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """메인 WebSocket 엔드포인트"""
    await websocket.accept()
    active_connections[client_id] = websocket
    logger.info(f"✅ 클라이언트 {client_id} 연결됨")
    
    try:
        # 연결 확인 메시지 전송
        await websocket.send_json({
            "type": "connection_established",
            "message": "🎓 AI 튜터와 연결되었습니다! (음성 + 텍스트 지원)",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat(),
            "features": ["voice_input", "text_input", "voice_output", "real_time_streaming"]
        })
        
        # 메인 메시지 루프
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive(), timeout=60.0)
                
                if data["type"] == "websocket.disconnect":
                    logger.info(f"❌ 클라이언트 {client_id} 정상 연결 종료")
                    break
                
                # JSON 메시지 처리
                if data["type"] == "websocket.receive" and "text" in data:
                    try:
                        message = json.loads(data["text"])
                        await handle_text_message(websocket, message, client_id)
                    except json.JSONDecodeError as e:
                        logger.error(f"⚠️ JSON 파싱 오류: {data['text'][:100]} | {e}")
                        await websocket.send_json({
                            "type": "error",
                            "message": "메시지 형식이 올바르지 않습니다."
                        })
                
                # 바이너리 메시지 (오디오) 처리
                elif data["type"] == "websocket.receive" and "bytes" in data:
                    audio_data = data["bytes"]
                    await handle_audio_message(websocket, audio_data, client_id)
                    
            except asyncio.TimeoutError:
                # 연결 상태 확인 (핑)
                try:
                    await websocket.send_json({
                        "type": "ping",
                        "timestamp": datetime.now().isoformat()
                    })
                except:
                    logger.warning(f"클라이언트 {client_id} 핑 실패 - 연결 종료")
                    break
                
    except WebSocketDisconnect:
        logger.info(f"❌ 클라이언트 {client_id} 연결 끊김 (정상)")
    except Exception as e:
        logger.error(f"⚠️ WebSocket 에러 {client_id}: {str(e)}")
    finally:
        # 연결 정리
        if client_id in active_connections:
            del active_connections[client_id]
        if client_id in tutor_configs:
            del tutor_configs[client_id]
        logger.info(f"🔄 클라이언트 {client_id} 정리 완료")

async def handle_text_message(websocket: WebSocket, message: dict, client_id: str):
    """텍스트 메시지 처리 (설정 업데이트 + 사용자 텍스트 입력)"""
    try:
        message_type = message.get("type")
        logger.info(f"📨 텍스트 메시지 수신: {message_type} from {client_id}")
        
        if message_type == "config_update":
            # 튜터 설정 업데이트
            config = message.get("config", {})
            
            # 기본 voice_settings 추가
            if "voice_settings" not in config:
                config["voice_settings"] = {
                    "auto_play": True,
                    "speed": 1.0,
                    "pitch": 1.0
                }
            
            tutor_configs[client_id] = config
            logger.info(f"📋 튜터 설정 업데이트: {config.get('name', 'Unknown')} ({config.get('subject', 'Unknown')})")
            
            await websocket.send_json({
                "type": "config_updated",
                "message": "튜터 설정이 업데이트되었습니다.",
                "config_summary": {
                    "name": config.get("name"),
                    "subject": config.get("subject"),
                    "level": config.get("level")
                }
            })
            
        elif message_type == "user_text":
            # 사용자 텍스트 입력 처리
            user_text = message.get("text", "").strip()
            
            if not user_text:
                await websocket.send_json({
                    "type": "error",
                    "message": "텍스트가 비어있습니다."
                })
                return
            
            if len(user_text) > 10000:
                await websocket.send_json({
                    "type": "error",
                    "message": "텍스트가 너무 깁니다. 10,000자 이하로 입력해주세요."
                })
                return
            
            logger.info(f"💬 사용자 텍스트 입력: '{user_text[:50]}...' from {client_id}")
            
            # AI 응답 생성
            await generate_ai_response(websocket, user_text, client_id)
            
        elif message_type == "ping":
            # 핑 응답
            await websocket.send_json({
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            })
            
        else:
            logger.warning(f"⚠️ 알 수 없는 메시지 타입: {message_type}")
            await websocket.send_json({
                "type": "error",
                "message": f"지원하지 않는 메시지 타입: {message_type}"
            })
            
    except Exception as e:
        logger.error(f"⚠️ 텍스트 메시지 처리 오류 {client_id}: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": f"메시지 처리 중 오류가 발생했습니다: {str(e)}"
        })

async def handle_audio_message(websocket: WebSocket, audio_data: bytes, client_id: str):
    """오디오 메시지 처리 (STT → AI 응답)"""
    try:
        logger.info(f"🎤 오디오 수신: {len(audio_data)} bytes from {client_id}")
        
        # 오디오 크기 검증
        if len(audio_data) < 1000:
            await websocket.send_json({
                "type": "error", 
                "message": "녹음이 너무 짧습니다. 조금 더 길게 말씀해주세요."
            })
            return
        
        if len(audio_data) > 10 * 1024 * 1024:  # 10MB
            await websocket.send_json({
                "type": "error", 
                "message": "녹음이 너무 깁니다. 짧게 나누어서 말씀해주세요."
            })
            return
        
        # STT 처리
        transcript = await process_speech_to_text(audio_data)
        logger.info(f"🔤 STT 결과: '{transcript}' from {client_id}")
        
        if not transcript or transcript.strip() == "":
            await websocket.send_json({
                "type": "error", 
                "message": "음성을 인식할 수 없었습니다. 명확하게 말씀해주시고 다시 시도해주세요."
            })
            return
        
        # STT 결과 전송
        await websocket.send_json({
            "type": "stt_result",
            "text": transcript,
            "timestamp": datetime.now().isoformat()
        })
        
        # AI 응답 생성
        await generate_ai_response(websocket, transcript, client_id)
        
    except Exception as e:
        logger.error(f"⚠️ 오디오 처리 오류 {client_id}: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": f"오디오 처리 중 오류가 발생했습니다: {str(e)}"
        })

async def process_speech_to_text(audio_data: bytes) -> str:
    """Google Speech-to-Text 처리 (다중 설정 시도)"""
    if not speech_client:
        logger.error("STT 클라이언트가 초기화되지 않았습니다.")
        return ""
    
    try:
        logger.info(f"🎤 STT 처리 시작: {len(audio_data)} bytes")
        
        # 다양한 STT 설정 (우선순위별)
        configs_to_try = [
            {
                "encoding": speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                "sample_rate_hertz": 48000,
                "description": "WEBM_OPUS 48kHz"
            },
            {
                "encoding": speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                "sample_rate_hertz": 16000,
                "description": "WEBM_OPUS 16kHz"
            },
            {
                "encoding": speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
                "sample_rate_hertz": 48000,
                "description": "OGG_OPUS 48kHz"
            },
            {
                "encoding": speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,
                "sample_rate_hertz": 48000,
                "description": "AUTO_DETECT"
            }
        ]
        
        for i, config_params in enumerate(configs_to_try):
            try:
                logger.info(f"🔄 STT 시도 {i+1}/4: {config_params['description']}")
                
                config = speech.RecognitionConfig(
                    encoding=config_params["encoding"],
                    sample_rate_hertz=config_params["sample_rate_hertz"],
                    language_code="ko-KR",
                    enable_automatic_punctuation=True,
                    model="latest_short",
                    enable_word_confidence=True,
                    use_enhanced=True,
                    alternative_language_codes=["en-US"]
                )
                
                audio = speech.RecognitionAudio(content=audio_data)
                
                # STT 요청 (타임아웃 10초)
                response = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, 
                        lambda: speech_client.recognize(config=config, audio=audio)
                    ),
                    timeout=10.0
                )
                
                if response.results and len(response.results) > 0:
                    transcript = response.results[0].alternatives[0].transcript
                    confidence = response.results[0].alternatives[0].confidence
                    
                    logger.info(f"✅ STT 성공: '{transcript}' (신뢰도: {confidence:.2f})")
                    
                    # 신뢰도가 너무 낮으면 다음 설정 시도
                    if confidence < 0.3:
                        logger.warning(f"⚠️ 신뢰도 낮음 ({confidence:.2f}), 다음 설정 시도")
                        continue
                    
                    return transcript.strip()
                else:
                    logger.warning(f"⚠️ STT 결과 없음: {config_params['description']}")
                    
            except asyncio.TimeoutError:
                logger.warning(f"⏰ STT 타임아웃: {config_params['description']}")
                continue
            except Exception as e:
                logger.error(f"⚠️ STT 설정 {i+1} 실패: {str(e)}")
                continue
        
        logger.error("❌ 모든 STT 설정 실패")
        return ""
        
    except Exception as e:
        logger.error(f"⚠️ STT 전체 처리 오류: {str(e)}")
        return ""

async def generate_ai_response(websocket: WebSocket, user_input: str, client_id: str):
    """AI 응답 생성 (GPT-3.5 스트리밍 + TTS)"""
    try:
        tutor_config = tutor_configs.get(client_id, {})
        tutor_prompt = create_tutor_prompt(tutor_config, user_input)
        
        logger.info(f"🤖 AI 응답 생성 시작: '{user_input[:30]}...' for {tutor_config.get('name', 'Unknown')}")
        
        # GPT 스트리밍 요청
        stream = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": tutor_prompt},
                {"role": "user", "content": user_input}
            ],
            max_tokens=300,
            temperature=0.7,
            stream=True
        )
        
        response_text = ""
        
        # 스트리밍 응답 처리
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                response_text += content
                
                # 실시간 텍스트 표시 (TTS 없이)
                await websocket.send_json({
                    "type": "text_chunk",
                    "content": content,
                    "timestamp": datetime.now().isoformat()
                })
        
        # 전체 응답 완료 후 TTS 처리
        if response_text.strip():
            logger.info(f"💬 응답 완료 ({len(response_text)}자), TTS 처리 시작")
            await process_and_send_tts(websocket, response_text.strip())
        
        logger.info(f"✅ AI 응답 처리 완료: {client_id}")
        
    except Exception as e:
        logger.error(f"⚠️ AI 응답 생성 오류 {client_id}: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": f"AI 응답 생성 중 오류가 발생했습니다: {str(e)}"
        })

def create_tutor_prompt(tutor_config: dict, user_input: str) -> str:
    """튜터 설정 기반 개인화 프롬프트 생성"""
    # 기본 정보
    name = tutor_config.get("name", "AI 튜터")
    subject = tutor_config.get("subject", "일반")
    level = tutor_config.get("level", "중학교")
    
    # 성격 설정
    personality = tutor_config.get("personality", {})
    friendliness = personality.get("friendliness", 70)
    humor_level = personality.get("humor_level", 30)
    encouragement = personality.get("encouragement", 80)
    explanation_detail = personality.get("explanation_detail", 70)
    
    # 성격 기반 지시사항 생성
    personality_instructions = []
    
    if friendliness >= 80:
        personality_instructions.append("매우 친근하고 다정한 말투로 대화하세요.")
    elif friendliness >= 60:
        personality_instructions.append("친근하고 편안한 말투로 대화하세요.")
    else:
        personality_instructions.append("정중하고 차분한 말투로 대화하세요.")
    
    if humor_level >= 70:
        personality_instructions.append("적절한 유머와 재미있는 비유를 사용하세요.")
    elif humor_level >= 40:
        personality_instructions.append("가끔 유머를 섞어서 대화하세요.")
    
    if encouragement >= 80:
        personality_instructions.append("학생을 적극적으로 격려하고 칭찬하세요.")
    elif encouragement >= 60:
        personality_instructions.append("학생을 격려하는 말을 해주세요.")
    
    if explanation_detail >= 80:
        personality_instructions.append("매우 상세하고 구체적으로 설명하세요.")
    elif explanation_detail >= 60:
        personality_instructions.append("적절한 수준으로 자세히 설명하세요.")
    else:
        personality_instructions.append("간단명료하게 설명하세요.")
    
    # 최종 프롬프트 구성
    prompt = f"""당신은 {name}이라는 {subject} 전문 선생님입니다.
{level} 수준의 학생들을 가르치는 경험이 풍부한 교육자입니다.

성격 특성:
- 친근함: {friendliness}%
- 유머 수준: {humor_level}%
- 격려 수준: {encouragement}%
- 설명 상세도: {explanation_detail}%

교육 지침:
{chr(10).join(f"- {instruction}" for instruction in personality_instructions)}

기본 규칙:
- 항상 한국어로 답변하세요.
- 학생의 수준({level})에 맞춰 설명하세요.
- {subject} 분야에 대한 전문 지식을 활용하세요.
- 질문이 {subject}와 관련 없다면 {subject}와 연관지어 설명해보세요.
- 답변은 300자 이내로 간결하게 해주세요.
- 자연스럽고 대화하는 듯한 말투를 사용하세요.
- 학생의 이해도를 확인하고 추가 질문을 유도하세요.

현재 학생의 질문이나 요청에 대해 위 특성을 모두 반영하여 교육적이고 도움이 되는 답변을 해주세요."""
    
    return prompt

async def process_and_send_tts(websocket: WebSocket, text: str):
    """TTS 처리 및 전송 (단일 오디오 출력)"""
    if not tts_client:
        logger.warning("TTS 클라이언트가 비활성화되어 텍스트만 전송합니다.")
        await websocket.send_json({
            "type": "text_chunk",
            "content": text
        })
        return
    
    try:
        logger.info(f"🔊 TTS 처리 시작: {text[:30]}... ({len(text)}자)")
        
        # TTS 설정
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="ko-KR",
            name="ko-KR-Standard-A",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0.0
        )
        
        # TTS 요청
        response = tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Base64 인코딩
        audio_base64 = base64.b64encode(response.audio_content).decode('utf-8')
        
        # 단일 오디오 청크로 전송 (중첩 방지)
        await websocket.send_json({
            "type": "audio_chunk",
            "content": text,
            "audio": audio_base64,
            "audio_size": len(response.audio_content),
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"✅ TTS 전송 완료: {len(response.audio_content)} bytes")
        
    except Exception as e:
        logger.error(f"⚠️ TTS 처리 오류: {str(e)}")
        # TTS 실패 시 텍스트만 전송
        await websocket.send_json({
            "type": "text_chunk",
            "content": text,
            "error": "TTS 처리 실패"
        })

# 예외 처리 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "서버에서 오류가 발생했습니다."
        }
    )

# 서버 실행 (Cloud Run용)
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    log_level = os.getenv("LOG_LEVEL", "info")
    
    logger.info(f"🚀 AI 튜터 서버 시작")
    logger.info(f"📡 포트: {port}")
    logger.info(f"🎤 음성 입력: {'✅ 활성화' if speech_client else '❌ 비활성화'}")
    logger.info(f"🔊 음성 출력: {'✅ 활성화' if tts_client else '❌ 비활성화'}")
    logger.info(f"💬 텍스트 입력: ✅ 활성화")
    logger.info(f"🤖 AI 모델: GPT-3.5 Turbo")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level=log_level,
        access_log=True
    )
