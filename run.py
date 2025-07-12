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
- 1초 이내 응답 시작
- 즉시 음성 중단 기능
- 실시간 피드백 루프
- 스마트 의도 분석
"""

import asyncio
import base64
import json
import os
import tempfile
import uuid
import time
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
    description="실시간 AI 튜터 시스템 - 1초 응답 + 즉시 중단 + 실시간 피드백",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정 (기존 유지)
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

# 환경변수 설정 (기존 유지)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
    raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")

# 클라이언트 초기화 (기존 유지)
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

# 전역 변수 (기존 + 새로 추가)
active_connections: Dict[str, WebSocket] = {}
tutor_configs: Dict[str, Dict[str, Any]] = {}
response_in_progress: set = set()  # 응답 상태 관리
conversation_history: Dict[str, list] = {}  # 대화 기억 관리 (NEW)

# 기본 엔드포인트들 (기존 유지 + 정보 추가)
@app.get("/")
async def root():
    """메인 페이지 - 시스템 정보"""
    return {
        "message": "🎓 AI Tutor Realtime System",
        "version": "3.0.0",
        "status": "running",
        "features": [
            "음성 입력 (STT)",
            "텍스트 입력", 
            "음성 출력 (TTS)",
            "실시간 스트리밍",
            "튜터 개성화",
            "다중 입력 방식",
            "1초 이내 응답",        # NEW
            "즉시 음성 중단",        # NEW
            "실시간 피드백 루프",     # NEW
            "스마트 의도 분석",      # NEW
            "대화 기억 관리"        # NEW
        ],
        "performance": {
            "target_response_time": "< 1초",
            "audio_quality": "최우선",
            "interrupt_latency": "즉시"
        },
        "config": "1초 응답 + 고품질 음성 + 즉시 중단",
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
    """서비스 상태 확인 (기존 + 새로운 메트릭 추가)"""
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
            "active_responses": len(response_in_progress),
            "conversation_sessions": len(conversation_history),  # NEW
            "services": {
                "openai_gpt": openai_status,
                "google_tts": tts_status,
                "google_stt": stt_status
            },
            "performance": {  # NEW
                "target_response_time": "1000ms",
                "audio_buffer_allowed": "200-300ms",
                "interrupt_support": "enabled"
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
    """상세 시스템 정보 (기존 + 새로운 기능 정보 추가)"""
    return {
        "system": "AI Tutor Realtime System",
        "version": "3.0.0",
        "architecture": "고성능 실시간 마이크로서비스",
        "deployment": "Google Cloud Run",
        "input_methods": {
            "voice": {
                "engine": "Google Cloud Speech-to-Text",
                "supported_formats": ["WEBM_OPUS", "OGG_OPUS"],
                "languages": ["ko-KR", "en-US"],
                "features": ["자동 구두점", "신뢰도 점수", "다중 설정 시도", "실시간 중단 감지"]  # NEW
            },
            "text": {
                "method": "WebSocket 실시간 전송",
                "encoding": "UTF-8",
                "max_length": "10000자",
                "features": ["실시간 피드백", "의도 분석", "즉시 중단"]  # NEW
            }
        },
        "output_methods": {
            "text": {
                "streaming": True,
                "real_time": True,
                "format": "1초 이내 시작 + 자연스러운 단어 단위 스트리밍"  # NEW
            },
            "voice": {
                "engine": "Google Cloud Text-to-Speech",
                "voice": "ko-KR-Standard-A",
                "format": "MP3",
                "features": ["고품질 우선", "200-300ms 버퍼링", "즉시 중단", "문장별 스트리밍"]  # NEW
            }
        },
        "ai_model": {
            "provider": "OpenAI",
            "model": "GPT-3.5 Turbo",
            "streaming": True,
            "max_tokens": "의도별 적응형 (50-400)",  # NEW
            "temperature": 0.7,
            "response_strategies": ["very_short", "short", "medium", "long", "interactive"]  # NEW
        },
        "communication": {
            "protocol": "WebSocket",
            "real_time": True,
            "auto_reconnect": True,
            "timeout": "60초",
            "interrupt_support": True,  # NEW
            "feedback_loop": True       # NEW
        },
        "tutor_system": {
            "personalization": True,
            "personality_traits": [
                "친근함", "유머 수준", "격려 수준", 
                "설명 상세도", "상호작용 빈도"
            ],
            "subjects": "무제한",
            "education_levels": ["중학교", "고등학교", "대학교", "대학원"],
            "conversation_memory": "5-10턴 + 세션 요약",  # NEW
            "intent_analysis": "실시간 의도 파악 및 응답 최적화"  # NEW
        }
    }

@app.get("/stats")
async def get_statistics():
    """실시간 통계 (기존 + 새로운 메트릭 추가)"""
    return {
        "connections": {
            "active": len(active_connections),
            "total_connected": len(active_connections)
        },
        "tutors": {
            "active": len(tutor_configs),
            "configurations": list(tutor_configs.keys())
        },
        "responses": {
            "in_progress": len(response_in_progress),
            "active_clients": list(response_in_progress)
        },
        "conversations": {  # NEW
            "active_sessions": len(conversation_history),
            "total_messages": sum(len(msgs) for msgs in conversation_history.values())
        },
        "timestamp": datetime.now().isoformat()
    }

# WebSocket 엔드포인트 (기존 로직 유지)
@app.websocket("/ws/tutor/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """메인 WebSocket 엔드포인트 (기존 로직 보존)"""
    await websocket.accept()
    active_connections[client_id] = websocket
    
    # NEW: 대화 세션 초기화
    if client_id not in conversation_history:
        conversation_history[client_id] = []
    
    logger.info(f"✅ 클라이언트 {client_id} 연결됨")
    
    try:
        # 연결 확인 메시지 전송 (기존 + 새 기능 정보 추가)
        await websocket.send_json({
            "type": "connection_established",
            "message": "🎓 AI 튜터와 연결되었습니다! (1초 응답 + 즉시 중단 + 실시간 피드백)",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat(),
            "features": [
                "voice_input", "text_input", "voice_output", 
                "real_time_streaming", "state_management",
                "instant_interrupt", "feedback_loop", "intent_analysis"  # NEW
            ],
            "performance": {  # NEW
                "response_target": "1초 이내",
                "audio_quality": "최우선",
                "interrupt_latency": "즉시"
            }
        })
        
        # 메인 메시지 루프 (기존 로직 유지)
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
                # 연결 상태 확인 (핑) - 기존 로직
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
        # 연결 정리 (기존 + 새로운 정리 항목 추가)
        if client_id in active_connections:
            del active_connections[client_id]
        if client_id in tutor_configs:
            del tutor_configs[client_id]
        response_in_progress.discard(client_id)
        # NEW: 대화 기록은 유지 (재연결 시 복원 가능)
        logger.info(f"🔄 클라이언트 {client_id} 정리 완료")

async def handle_text_message(websocket: WebSocket, message: dict, client_id: str):
    """텍스트 메시지 처리 (기존 로직 보존 + 새 기능 추가)"""
    try:
        message_type = message.get("type")
        logger.info(f"📨 텍스트 메시지 수신: {message_type} from {client_id}")
        
        if message_type == "config_update":
            # 튜터 설정 업데이트 (기존 로직 완전 보존)
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
            user_text = message.get("text", "").strip()
            is_interrupt = message.get("interrupt", False)  # NEW
            
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
            
            # NEW: 현재 응답 중이고 중단 플래그가 있으면 피드백/중단 처리
            if is_interrupt and client_id in response_in_progress:
                await handle_response_interrupt(websocket, user_text, client_id)
                return
            
            # NEW: 일반 응답이지만 현재 진행 중이면 중단 후 새 응답
            if client_id in response_in_progress:
                await interrupt_current_response(websocket, client_id)
            
            logger.info(f"💬 사용자 텍스트 입력: '{user_text[:50]}...' from {client_id}")
            
            # NEW: 대화 기록에 추가
            add_to_conversation_history(client_id, "user", user_text)
            
            # NEW: 최적화된 AI 응답 생성 (1초 목표)
            await generate_ai_response_optimized(websocket, user_text, client_id)
            
        elif message_type == "feedback_request":
            # NEW: 실시간 피드백 처리
            await handle_realtime_feedback(websocket, message, client_id)
            
        elif message_type == "interrupt_response":
            # NEW: 응답 중단 요청
            await interrupt_current_response(websocket, client_id)
            
        elif message_type == "ping":
            # 핑 응답 (기존 로직)
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
    """오디오 메시지 처리 (기존 로직 보존 + 중단 체크 추가)"""
    try:
        # NEW: 응답 진행 중 체크
        if client_id in response_in_progress:
            await interrupt_current_response(websocket, client_id)
        
        logger.info(f"🎤 오디오 수신: {len(audio_data)} bytes from {client_id}")
        
        # 오디오 크기 검증 (기존 로직)
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
        
        # STT 처리 (기존 로직 완전 보존)
        transcript = await process_speech_to_text(audio_data)
        logger.info(f"🔤 STT 결과: '{transcript}' from {client_id}")
        
        if not transcript or transcript.strip() == "":
            await websocket.send_json({
                "type": "error", 
                "message": "음성을 인식할 수 없었습니다. 명확하게 말씀해주시고 다시 시도해주세요."
            })
            return
        
        # STT 결과 전송 (기존 로직)
        await websocket.send_json({
            "type": "stt_result",
            "text": transcript,
            "timestamp": datetime.now().isoformat()
        })
        
        # NEW: 대화 기록에 추가
        add_to_conversation_history(client_id, "user", transcript)
        
        # NEW: 최적화된 AI 응답 생성
        await generate_ai_response_optimized(websocket, transcript, client_id)
        
    except Exception as e:
        logger.error(f"⚠️ 오디오 처리 오류 {client_id}: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": f"오디오 처리 중 오류가 발생했습니다: {str(e)}"
        })

async def process_speech_to_text(audio_data: bytes) -> str:
    """Google Speech-to-Text 처리 (기존 로직 완전 보존)"""
    if not speech_client:
        logger.error("STT 클라이언트가 초기화되지 않았습니다.")
        return ""
    
    try:
        logger.info(f"🎤 STT 처리 시작: {len(audio_data)} bytes")
        
        # 다양한 STT 설정 (우선순위별) - 기존 로직
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
                
                # STT 요청 (타임아웃 10초) - 기존 로직
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

# NEW: 최적화된 AI 응답 생성 (1초 목표 + 고품질 음성)
async def generate_ai_response_optimized(websocket: WebSocket, user_input: str, client_id: str):
    """AI 응답 생성 - 1초 이내 응답 + 음성 품질 최우선"""
    try:
        response_in_progress.add(client_id)
        start_time = time.time()
        
        # 의도 분석 및 응답 전략 결정 (50ms 이내)
        response_strategy = analyze_user_intent_fast(user_input)
        
        # 응답 시작 알림 (즉시 전송)
        await websocket.send_json({
            "type": "response_start",
            "strategy": response_strategy,
            "timestamp": datetime.now().isoformat()
        })
        
        # 대화 맥락 구성
        conversation_context = get_conversation_context(client_id)
        
        # GPT 스트리밍 처리
        await process_streaming_with_quality_priority(
            websocket, user_input, client_id, response_strategy, 
            start_time, conversation_context
        )
        
    finally:
        response_in_progress.discard(client_id)

async def process_streaming_with_quality_priority(websocket: WebSocket, user_input: str, 
                                                client_id: str, strategy: str, start_time: float,
                                                conversation_context: list):
    """스트리밍 + TTS 품질 최우선 처리"""
    
    tutor_config = tutor_configs.get(client_id, {})
    tutor_prompt = create_adaptive_prompt(tutor_config, strategy, conversation_context)
    
    # GPT 스트리밍 시작
    stream = await openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": tutor_prompt},
            {"role": "user", "content": user_input}
        ],
        max_tokens=get_max_tokens(strategy),
        temperature=0.7,
        stream=True
    )
    
    # 스트리밍 상태 관리
    sentence_buffer = ""
    word_buffer = ""
    sentence_count = 0
    first_response_sent = False
    response_text = ""
    
    # TTS 태스크 관리
    tts_tasks = []
    
    async for chunk in stream:
        # 중단 체크
        if client_id not in response_in_progress:
            logger.info(f"🛑 응답 중단됨: {client_id}")
            break
            
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            word_buffer += content
            sentence_buffer += content
            response_text += content
            
            # 실시간 텍스트 전송 (단어 단위)
            if any(char in content for char in [' ', '\n', '\t']) or chunk.choices[0].finish_reason:
                if word_buffer.strip():
                    # 첫 응답 타이밍 로깅
                    if not first_response_sent:
                        elapsed = time.time() - start_time
                        logger.info(f"⚡ 첫 응답 시간: {elapsed:.3f}초")
                        first_response_sent = True
                    
                    await websocket.send_json({
                        "type": "text_chunk",
                        "content": word_buffer,
                        "timestamp": datetime.now().isoformat()
                    })
                    word_buffer = ""
            
            # 문장 완료 시 고품질 TTS 처리 (200-300ms 버퍼링 허용)
            if any(punct in content for punct in ['.', '!', '?', '다', '요', '죠', '니다', '습니다']):
                if sentence_buffer.strip() and len(sentence_buffer.strip()) > 3:
                    sentence_count += 1
                    
                    # 비동기 TTS 태스크 생성 (블로킹하지 않음)
                    tts_task = asyncio.create_task(
                        create_quality_tts_with_buffer(websocket, sentence_buffer.strip(), sentence_count)
                    )
                    tts_tasks.append(tts_task)
                    sentence_buffer = ""
    
    # 남은 텍스트 처리
    if sentence_buffer.strip():
        sentence_count += 1
        tts_task = asyncio.create_task(
            create_quality_tts_with_buffer(websocket, sentence_buffer.strip(), sentence_count)
        )
        tts_tasks.append(tts_task)
    
    # 응답 완료 알림
    await websocket.send_json({
        "type": "response_complete",
        "total_sentences": sentence_count,
        "timestamp": datetime.now().isoformat()
    })
    
    # 대화 기록에 추가
    add_to_conversation_history(client_id, "assistant", response_text)
    
    # 모든 TTS 태스크 완료 대기 (병렬 처리)
    if tts_tasks:
        await asyncio.gather(*tts_tasks, return_exceptions=True)
    
    # 모든 오디오 완료 알림
    await websocket.send_json({
        "type": "all_audio_complete",
        "timestamp": datetime.now().isoformat()
    })

async def create_quality_tts_with_buffer(websocket: WebSocket, sentence: str, sequence: int):
    """고품질 TTS (200-300ms 버퍼링 허용) - 기존 TTS 로직 기반"""
    if not tts_client:
        logger.warning("TTS 클라이언트가 비활성화되어 텍스트만 전송합니다.")
        return
    
    try:
        logger.info(f"🔊 TTS 처리 시작: {sentence[:30]}... ({len(sentence)}자)")
        
        # 품질 우선 TTS 설정
        synthesis_input = texttospeech.SynthesisInput(text=sentence)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="ko-KR",
            name="ko-KR-Standard-A",  # 고품질 음성
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,  # 자연스러운 속도
            pitch=0.0,
            volume_gain_db=0.0,
            effects_profile_id=["headphone-class-device"]  # 고품질 프로파일
        )
        
        # TTS 요청 (200-300ms 허용)
        start_tts = time.time()
        response = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None,
                lambda: tts_client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config
                )
            ),
            timeout=1.0  # 1초 타임아웃
        )
        tts_time = time.time() - start_tts
        
        # Base64 인코딩
        audio_base64 = base64.b64encode(response.audio_content).decode('utf-8')
        
        # 순서가 있는 고품질 오디오 전송
        await websocket.send_json({
            "type": "audio_stream_quality",
            "sequence": sequence,
            "sentence": sentence,
            "audio": audio_base64,
            "audio_size": len(response.audio_content),
            "tts_time": round(tts_time, 3),
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"✅ TTS 전송 완료: {len(response.audio_content)} bytes")
        
    except asyncio.TimeoutError:
        logger.error(f"⏰ TTS 타임아웃: {sentence[:20]}...")
        # 타임아웃 시 텍스트만 전송
        await websocket.send_json({
            "type": "text_fallback",
            "sequence": sequence,
            "sentence": sentence,
            "error": "TTS 타임아웃"
        })
    except Exception as e:
        logger.error(f"⚠️ TTS 오류: {str(e)}")

# NEW: 빠른 의도 분석
def analyze_user_intent_fast(user_input: str) -> str:
    """빠른 의도 분석 (50ms 이내)"""
    user_input_lower = user_input.lower()
    
    # 단순하고 빠른 키워드 기반 분석
    if len(user_input) < 5 or any(word in user_input_lower for word in ["응", "네", "예", "아니", "맞아", "틀려"]):
        return "very_short"
    elif any(word in user_input_lower for word in ["짧게", "간단히", "요약"]):
        return "short"
    elif any(word in user_input_lower for word in ["자세히", "설명", "구체적으로", "예시"]):
        return "long"
    elif any(word in user_input_lower for word in ["문제", "퀴즈", "테스트"]):
        return "interactive"
    else:
        return "medium"

def get_max_tokens(strategy: str) -> int:
    """전략별 최대 토큰 (응답 속도 최적화)"""
    return {
        "very_short": 50,
        "short": 100,
        "medium": 200,
        "long": 300,
        "interactive": 150
    }.get(strategy, 150)

# NEW: 대화 기억 관리
def add_to_conversation_history(client_id: str, role: str, content: str):
    """대화 기록에 추가 (최근 10턴 유지)"""
    if client_id not in conversation_history:
        conversation_history[client_id] = []
    
    conversation_history[client_id].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })
    
    # 최근 10턴 (20개 메시지)만 유지
    if len(conversation_history[client_id]) > 20:
        conversation_history[client_id] = conversation_history[client_id][-20:]

def get_conversation_context(client_id: str) -> list:
    """대화 맥락 반환 (최근 5턴)"""
    if client_id not in conversation_history:
        return []
    
    # 최근 10개 메시지 (5턴) 반환
    recent_messages = conversation_history[client_id][-10:]
    return [{"role": msg["role"], "content": msg["content"]} for msg in recent_messages]

# NEW: 실시간 피드백 처리
async def handle_response_interrupt(websocket: WebSocket, user_text: str, client_id: str):
    """응답 중단 + 새로운 응답 처리"""
    try:
        logger.info(f"🛑 응답 중단 + 새 질문: '{user_text[:30]}...' from {client_id}")
        
        # 기존 응답 중단
        await interrupt_current_response(websocket, client_id)
        
        # 피드백인지 새 질문인지 판단
        feedback_analysis = analyze_feedback_intent(user_text)
        
        if feedback_analysis["is_feedback"]:
            # 피드백 처리
            await process_feedback_response(websocket, feedback_analysis, client_id)
        else:
            # 새로운 질문으로 처리
            add_to_conversation_history(client_id, "user", user_text)
            await generate_ai_response_optimized(websocket, user_text, client_id)
            
    except Exception as e:
        logger.error(f"⚠️ 응답 중단 처리 오류: {str(e)}")

async def handle_realtime_feedback(websocket: WebSocket, message: dict, client_id: str):
    """실시간 피드백 처리"""
    try:
        action = message.get("action")
        original_input = message.get("original_input", "")
        
        logger.info(f"💬 실시간 피드백: {action} for '{original_input[:20]}...'")
        
        # 현재 응답 중단
        await interrupt_current_response(websocket, client_id)
        
        if action == "make_shorter":
            await generate_shorter_response(websocket, original_input, client_id)
        elif action == "make_detailed":
            await generate_detailed_response(websocket, original_input, client_id)
        else:
            await websocket.send_json({
                "type": "error",
                "message": f"지원하지 않는 피드백 액션: {action}"
            })
            
    except Exception as e:
        logger.error(f"⚠️ 실시간 피드백 처리 오류: {str(e)}")

async def interrupt_current_response(websocket: WebSocket, client_id: str):
    """현재 응답 즉시 중단"""
    if client_id in response_in_progress:
        response_in_progress.discard(client_id)
        
        # 클라이언트에 중단 신호 전송
        await websocket.send_json({
            "type": "response_interrupted",
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"🛑 응답 중단 완료: {client_id}")

def analyze_feedback_intent(user_text: str) -> dict:
    """사용자 입력이 피드백인지 새 질문인지 분석"""
    user_text_lower = user_text.lower()
    
    feedback_patterns = {
        "shorter": ["짧게", "간단히", "요약", "줄여", "그만"],
        "longer": ["자세히", "더", "구체적으로", "예시", "설명"],
        "stop": ["중단", "멈춰", "그만", "스톱"],
        "clarify": ["이해 안", "모르겠", "설명해", "뭔 뜻"]
    }
    
    for action, patterns in feedback_patterns.items():
        if any(pattern in user_text_lower for pattern in patterns):
            return {
                "is_feedback": True,
                "action": action,
                "confidence": 0.9,
                "original_text": user_text
            }
    
    return {
        "is_feedback": False,
        "action": "new_question",
        "confidence": 0.1,
        "original_text": user_text
    }

async def generate_shorter_response(websocket: WebSocket, original_input: str, client_id: str):
    """짧은 요약 응답 생성"""
    try:
        response_in_progress.add(client_id)
        
        await websocket.send_json({
            "type": "response_start",
            "strategy": "summary",
            "message": "더 간단히 설명해드릴게요!",
            "timestamp": datetime.now().isoformat()
        })
        
        tutor_config = tutor_configs.get(client_id, {})
        summary_prompt = create_summary_prompt(tutor_config)
        
        stream = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": summary_prompt},
                {"role": "user", "content": f"다음 질문에 대해 1-2문장으로 핵심만 간단히 답변해주세요: {original_input}"}
            ],
            max_tokens=100,
            temperature=0.5,
            stream=True
        )
        
        await process_simple_streaming(websocket, stream, client_id, "short")
        
    finally:
        response_in_progress.discard(client_id)

async def generate_detailed_response(websocket: WebSocket, original_input: str, client_id: str):
    """자세한 응답 생성"""
    try:
        response_in_progress.add(client_id)
        
        await websocket.send_json({
            "type": "response_start",
            "strategy": "detailed",
            "message": "더 자세히 설명해드릴게요!",
            "timestamp": datetime.now().isoformat()
        })
        
        tutor_config = tutor_configs.get(client_id, {})
        detailed_prompt = create_detailed_prompt(tutor_config)
        
        stream = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": detailed_prompt},
                {"role": "user", "content": f"다음 질문에 대해 예시와 함께 자세히 설명해주세요: {original_input}"}
            ],
            max_tokens=400,
            temperature=0.7,
            stream=True
        )
        
        await process_simple_streaming(websocket, stream, client_id, "detailed")
        
    finally:
        response_in_progress.discard(client_id)

async def process_simple_streaming(websocket: WebSocket, stream, client_id: str, response_type: str):
    """간단한 스트리밍 처리 (피드백 전용)"""
    response_text = ""
    word_buffer = ""
    
    async for chunk in stream:
        if client_id not in response_in_progress:
            break
            
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            word_buffer += content
            response_text += content
            
            # 실시간 텍스트 전송
            if any(char in content for char in [' ', '\n', '\t']) or chunk.choices[0].finish_reason:
                if word_buffer.strip():
                    await websocket.send_json({
                        "type": "text_chunk",
                        "content": word_buffer,
                        "response_type": response_type,
                        "timestamp": datetime.now().isoformat()
                    })
                    word_buffer = ""
    
    # 응답 완료
    await websocket.send_json({
        "type": "response_complete",
        "response_type": response_type,
        "timestamp": datetime.now().isoformat()
    })
    
    # 대화 기록에 추가
    add_to_conversation_history(client_id, "assistant", response_text)
    
    # 단일 TTS 처리
    if response_text.strip():
        await create_quality_tts_with_buffer(websocket, response_text.strip(), 1)

def create_adaptive_prompt(tutor_config: dict, strategy: str, conversation_context: list) -> str:
    """응답 전략과 대화 맥락을 고려한 적응형 프롬프트"""
    # 기본 정보 (기존 로직 보존)
    name = tutor_config.get("name", "AI 튜터")
    subject = tutor_config.get("subject", "일반")
    level = tutor_config.get("level", "중학교")
    
    # 성격 설정 (기존 로직 보존)
    personality = tutor_config.get("personality", {})
    friendliness = personality.get("friendliness", 70)
    humor_level = personality.get("humor_level", 30)
    encouragement = personality.get("encouragement", 80)
    explanation_detail = personality.get("explanation_detail", 70)
    
    # 성격 기반 지시사항 생성 (기존 로직)
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
    
    # NEW: 전략별 추가 지침
    strategy_instructions = {
        "very_short": "1문장으로 핵심만 간단히 답변하세요.",
        "short": "1-2문장으로 간결하게 답변하세요.",
        "medium": "2-3문장으로 적절히 설명하세요.",
        "long": "3-5문장으로 자세히 설명하세요.",
        "interactive": "2-3문장으로 답변하고 추가 질문을 유도하세요."
    }
    
    # NEW: 대화 맥락 요약
    context_summary = ""
    if conversation_context:
        context_summary = f"\n\n최근 대화 맥락:\n"
        for msg in conversation_context[-4:]:  # 최근 2턴
            role = "학생" if msg["role"] == "user" else "선생님"
            context_summary += f"- {role}: {msg['content'][:100]}...\n"
    
    # 최종 프롬프트 구성 (기존 + 새로운 요소)
    prompt = f"""당신은 {name}이라는 {subject} 전문 선생님입니다.
{level} 수준의 학생들을 가르치는 경험이 풍부한 교육자입니다.

성격 특성:
- 친근함: {friendliness}%
- 유머 수준: {humor_level}%
- 격려 수준: {encouragement}%
- 설명 상세도: {explanation_detail}%

교육 지침:
{chr(10).join(f"- {instruction}" for instruction in personality_instructions)}

응답 전략 ({strategy}):
- {strategy_instructions.get(strategy, "적절한 길이로 답변하세요.")}

기본 규칙:
- 항상 한국어로 답변하세요.
- 학생의 수준({level})에 맞춰 설명하세요.
- {subject} 분야에 대한 전문 지식을 활용하세요.
- 질문이 {subject}와 관련 없다면 {subject}와 연관지어 설명해보세요.
- 자연스럽고 대화하는 듯한 말투를 사용하세요.
- 이전 대화 내용을 참고하여 연속성 있는 답변을 하세요.{context_summary}

현재 학생의 질문이나 요청에 대해 위 특성을 모두 반영하여 교육적이고 도움이 되는 답변을 해주세요."""
    
    return prompt

def create_summary_prompt(tutor_config: dict) -> str:
    """요약 전용 프롬프트"""
    name = tutor_config.get("name", "AI 튜터")
    subject = tutor_config.get("subject", "일반")
    
    return f"""당신은 {name}이라는 {subject} 전문 튜터입니다.

**핵심 지침:**
- 1-2문장으로 핵심만 간단명료하게 답변하세요
- 불필요한 부연설명은 절대 하지 마세요
- 가장 중요한 포인트만 전달하세요
- "더 자세한 설명이 필요하면 말씀해주세요"라고 마무리하세요

질문의 핵심을 파악하고 가장 중요한 답변만 제공해주세요."""

def create_detailed_prompt(tutor_config: dict) -> str:
    """상세 설명 프롬프트"""
    name = tutor_config.get("name", "AI 튜터")
    subject = tutor_config.get("subject", "일반")
    
    return f"""당신은 {name}이라는 {subject} 전문 튜터입니다.

**상세 설명 지침:**
- 구체적인 예시와 함께 자세히 설명하세요
- 단계별로 나누어 설명하세요
- 학생이 이해하기 쉬운 비유를 사용하세요
- 3-5문장으로 충분히 설명하세요
- 추가 질문을 유도하는 문장으로 마무리하세요

학생의 이해도를 높이는 것을 목표로 자세하고 교육적으로 설명해주세요."""

async def process_feedback_response(websocket: WebSocket, feedback_analysis: dict, client_id: str):
    """피드백 기반 응답 처리"""
    action = feedback_analysis["action"]
    
    if action == "shorter":
        await websocket.send_json({
            "type": "feedback_acknowledged",
            "message": "더 간단히 설명해드릴게요!",
            "action": "shorter"
        })
    elif action == "longer":
        await websocket.send_json({
            "type": "feedback_acknowledged", 
            "message": "더 자세히 설명해드릴게요!",
            "action": "longer"
        })
    elif action == "stop":
        await websocket.send_json({
            "type": "feedback_acknowledged",
            "message": "응답을 중단했습니다.",
            "action": "stop"
        })

# 예외 처리 핸들러 (기존 유지)
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

# 서버 실행 (기존 유지 + 새로운 기능 정보 추가)
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    log_level = os.getenv("LOG_LEVEL", "info")
    
    logger.info(f"🚀 AI 튜터 서버 시작 (v3.0.0)")
    logger.info(f"📡 포트: {port}")
    logger.info(f"🎤 음성 입력: {'✅ 활성화' if speech_client else '❌ 비활성화'}")
    logger.info(f"🔊 음성 출력: {'✅ 활성화 (고품질 우선)' if tts_client else '❌ 비활성화'}")
    logger.info(f"💬 텍스트 입력: ✅ 활성화")
    logger.info(f"🤖 AI 모델: GPT-3.5 Turbo (스트리밍)")
    logger.info(f"🔄 상태 관리: ✅ 활성화")
    logger.info(f"📝 스트리밍: ✅ 1초 이내 시작 + 단어 단위")
    logger.info(f"🛑 즉시 중단: ✅ 활성화")
    logger.info(f"💭 실시간 피드백: ✅ 활성화")
    logger.info(f"🧠 의도 분석: ✅ 활성화")
    logger.info(f"💾 대화 기억: ✅ 5-10턴 관리")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level=log_level,
        access_log=True
    )
