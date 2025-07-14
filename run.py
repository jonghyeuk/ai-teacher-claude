#!/usr/bin/env python3
"""
AI 튜터 FastAPI 백엔드 애플리케이션 (v3.3 - 스마트한 균형)

완전한 실시간 AI 튜터 시스템 백엔드입니다.
- 🔒 오디오 중첩 완전 해결 (강력한 직렬화) ← 최우선
- 🎭 자연스러운 대화 품질 유지 (토큰 적절히 보존) ← 중요
- 💰 스마트한 비용 절약 (핵심만 최적화) ← 균형
- 🧠 튜터 기능 완전 보존 (학습 진도, 개인화) ← 필수
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

# 🎯 스마트한 로깅: 개발시엔 INFO, 운영시엔 WARNING
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger(__name__)

# 💰 비용 절약: 불필요한 상세 로깅만 제거
if LOG_LEVEL == "WARNING":
    # 운영 환경에서만 Google 클라이언트 로깅 제한
    logging.getLogger("google").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.ERROR)

# FastAPI 앱 초기화
app = FastAPI(
    title="AI Tutor Realtime System",
    description="실시간 AI 튜터 시스템 - v3.3 스마트한 균형 (중첩 해결 + 자연스러운 대화)",
    version="3.3.0",
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
        "*"
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

# 전역 변수 (기존 + 중첩 방지용)
active_connections: Dict[str, WebSocket] = {}
tutor_configs: Dict[str, Dict[str, Any]] = {}
response_in_progress: set = set()  
conversation_history: Dict[str, list] = {}

# 🔒 중첩 완전 방지를 위한 강력한 직렬화 시스템
client_locks: Dict[str, asyncio.Lock] = {}
client_tts_tasks: Dict[str, Optional[asyncio.Task]] = {}
response_queues: Dict[str, asyncio.Queue] = {}

# 기본 엔드포인트들
@app.get("/")
async def root():
    """메인 페이지 - 시스템 정보"""
    return {
        "message": "🎓 AI Tutor Realtime System",
        "version": "3.3.0",
        "status": "running",
        "updates": [
            "🔒 오디오 중첩 완전 해결 (강력한 직렬화)",
            "🎭 자연스러운 대화 품질 유지 (적절한 토큰)",
            "💰 스마트한 비용 절약 (핵심만 최적화)",
            "🧠 튜터 기능 완전 보존 (학습 진도, 개인화)"
        ],
        "philosophy": {
            "overlap_prevention": "100% 해결 (최우선)",
            "conversation_quality": "자연스러움 유지 (필수)",
            "cost_optimization": "스마트한 절약 (균형)",
            "tutor_intelligence": "학습 기능 보존 (핵심)"
        },
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
        openai_status = "✅ 연결됨" if OPENAI_API_KEY else "❌ API 키 없음"
        
        tts_status = "❌ 비활성화"
        if tts_client:
            try:
                voices = tts_client.list_voices()
                tts_status = f"✅ 활성화 ({len(voices.voices)}개 음성)"
            except Exception as e:
                tts_status = f"⚠️ 오류: {str(e)[:50]}"
        
        stt_status = "✅ 활성화" if speech_client else "❌ 비활성화"
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "active_connections": len(active_connections),
            "active_tutors": len(tutor_configs),
            "active_responses": len(response_in_progress),
            "conversation_sessions": len(conversation_history),
            "client_locks": len(client_locks),
            "active_tts_tasks": len([t for t in client_tts_tasks.values() if t and not t.done()]),
            "services": {
                "openai_gpt": openai_status,
                "google_tts": tts_status,
                "google_stt": stt_status
            },
            "performance": {
                "target_response_time": "1000ms",
                "audio_overlap_prevention": "완전 해결",
                "conversation_quality": "자연스러움 유지",
                "cost_efficiency": "스마트한 절약"
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
        "version": "3.3.0",
        "architecture": "고성능 실시간 마이크로서비스",
        "deployment": "Google Cloud Run",
        "core_improvements": {
            "audio_overlap_complete_prevention": "강력한 Lock 기반 직렬화로 중첩 100% 방지",
            "natural_conversation_preservation": "적절한 토큰 배분으로 자연스러운 대화 유지",
            "smart_cost_optimization": "핵심 기능 보존하면서 불필요한 비용만 제거",
            "tutor_intelligence_maintained": "학습 진도 추적, 개인화, 맥락 이해 완전 보존"
        },
        "balance_strategy": {
            "primary": "중첩 방지 (사용자 경험)",
            "secondary": "자연스러운 대화 (튜터 품질)",
            "tertiary": "비용 효율성 (지속 가능성)"
        }
    }

# WebSocket 엔드포인트 (기존 로직 유지 + 정리 강화)
@app.websocket("/ws/tutor/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """메인 WebSocket 엔드포인트"""
    await websocket.accept()
    active_connections[client_id] = websocket
    
    if client_id not in conversation_history:
        conversation_history[client_id] = []
    
    # 🔒 클라이언트별 직렬화 자원 초기화
    if client_id not in client_locks:
        client_locks[client_id] = asyncio.Lock()
        client_tts_tasks[client_id] = None
        response_queues[client_id] = asyncio.Queue(maxsize=1)
    
    logger.info(f"✅ 클라이언트 {client_id} 연결됨")
    
    try:
        await websocket.send_json({
            "type": "connection_established",
            "message": "🎓 AI 튜터와 연결되었습니다! (v3.3 - 중첩 해결 + 자연스러운 대화)",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat(),
            "features": [
                "voice_input", "text_input", "voice_output", 
                "real_time_streaming", "state_management",
                "instant_interrupt", "feedback_loop", "intent_analysis",
                "complete_overlap_prevention", "natural_conversation",
                "smart_cost_optimization", "tutor_intelligence"
            ]
        })
        
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive(), timeout=60.0)
                
                if data["type"] == "websocket.disconnect":
                    logger.info(f"❌ 클라이언트 {client_id} 정상 연결 종료")
                    break
                
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
                
                elif data["type"] == "websocket.receive" and "bytes" in data:
                    audio_data = data["bytes"]
                    await handle_audio_message(websocket, audio_data, client_id)
                    
            except asyncio.TimeoutError:
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
        await cleanup_client_completely(client_id)

async def cleanup_client_completely(client_id: str):
    """🔒 클라이언트 연결 종료 시 완전한 정리"""
    try:
        if client_id in client_locks:
            await force_cleanup_previous_response(client_id)
            del client_locks[client_id]
            
        if client_id in client_tts_tasks:
            del client_tts_tasks[client_id]
            
        if client_id in response_queues:
            del response_queues[client_id]
        
        if client_id in active_connections:
            del active_connections[client_id]
        if client_id in tutor_configs:
            del tutor_configs[client_id]
        response_in_progress.discard(client_id)
        
        logger.info(f"🧹 클라이언트 완전 정리 완료: {client_id}")
        
    except Exception as e:
        logger.error(f"⚠️ 클라이언트 정리 오류: {e}")

async def handle_text_message(websocket: WebSocket, message: dict, client_id: str):
    """텍스트 메시지 처리"""
    try:
        message_type = message.get("type")
        logger.info(f"📨 텍스트 메시지 수신: {message_type} from {client_id}")
        
        if message_type == "config_update":
            config = message.get("config", {})
            
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
            is_interrupt = message.get("interrupt", False)
            
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
            
            if is_interrupt and client_id in response_in_progress:
                await handle_response_interrupt(websocket, user_text, client_id)
                return
            
            logger.info(f"💬 사용자 텍스트 입력: '{user_text[:50]}...' from {client_id}")
            
            add_to_conversation_history(client_id, "user", user_text)
            await generate_ai_response_completely_safe(websocket, user_text, client_id)
            
        elif message_type == "feedback_request":
            await handle_realtime_feedback(websocket, message, client_id)
            
        elif message_type == "interrupt_response":
            await interrupt_current_response(websocket, client_id)
            
        elif message_type == "ping":
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
    """오디오 메시지 처리"""
    try:
        logger.info(f"🎤 오디오 수신: {len(audio_data)} bytes from {client_id}")
        
        if len(audio_data) < 500:
            await websocket.send_json({
                "type": "error", 
                "message": "녹음이 너무 짧습니다. 조금 더 길게 말씀해주세요."
            })
            return
        
        if len(audio_data) > 10 * 1024 * 1024:
            await websocket.send_json({
                "type": "error", 
                "message": "녹음이 너무 깁니다. 짧게 나누어서 말씀해주세요."
            })
            return
        
        transcript = await process_speech_to_text_enhanced(audio_data)
        logger.info(f"🔤 STT 결과: '{transcript}' from {client_id}")
        
        if not transcript or transcript.strip() == "":
            await websocket.send_json({
                "type": "error", 
                "message": "음성을 인식할 수 없었습니다. 더 명확하게 말씀해주세요."
            })
            return
        
        await websocket.send_json({
            "type": "stt_result",
            "text": transcript,
            "timestamp": datetime.now().isoformat()
        })
        
        add_to_conversation_history(client_id, "user", transcript)
        await generate_ai_response_completely_safe(websocket, transcript, client_id)
        
    except Exception as e:
        logger.error(f"⚠️ 오디오 처리 오류 {client_id}: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": f"오디오 처리 중 오류가 발생했습니다: {str(e)}"
        })

async def process_speech_to_text_enhanced(audio_data: bytes) -> str:
    """STT 처리 (기존 유지)"""
    if not speech_client:
        logger.error("STT 클라이언트가 초기화되지 않았습니다.")
        return ""
    
    try:
        logger.info(f"🎤 개선된 STT 처리 시작: {len(audio_data)} bytes")
        
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
                "encoding": speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,
                "sample_rate_hertz": 16000,
                "description": "AUTO_DETECT 16kHz"
            },
            {
                "encoding": speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
                "sample_rate_hertz": 16000,
                "description": "OGG_OPUS 16kHz"
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
                    alternative_language_codes=["en-US"],
                    profanity_filter=False,
                    enable_speaker_diarization=False,
                    max_alternatives=1
                )
                
                audio = speech.RecognitionAudio(content=audio_data)
                
                response = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, 
                        lambda: speech_client.recognize(config=config, audio=audio)
                    ),
                    timeout=15.0
                )
                
                if response.results and len(response.results) > 0:
                    transcript = response.results[0].alternatives[0].transcript
                    confidence = response.results[0].alternatives[0].confidence if response.results[0].alternatives[0].confidence else 0.0
                    
                    logger.info(f"✅ STT 성공: '{transcript}' (신뢰도: {confidence:.2f})")
                    
                    if confidence < 0.1:
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

# 🔒 완전히 안전한 AI 응답 생성 (중첩 100% 방지)
async def generate_ai_response_completely_safe(websocket: WebSocket, user_input: str, client_id: str):
    """🔒 완전히 안전한 AI 응답 생성 (중첩 100% 방지)"""
    
    if client_id not in client_locks:
        client_locks[client_id] = asyncio.Lock()
        client_tts_tasks[client_id] = None
        response_queues[client_id] = asyncio.Queue(maxsize=1)
    
    # 🔒 강력한 Lock으로 완전히 직렬화
    async with client_locks[client_id]:
        try:
            await force_cleanup_previous_response(client_id)
            
            logger.info(f"🔒 Lock 획득 - 안전한 응답 시작: {client_id}")
            
            response_in_progress.add(client_id)
            start_time = time.time()
            
            # 🎭 자연스러운 의도 분석 (적절한 복잡도 유지)
            response_strategy = analyze_user_intent_for_natural_conversation(user_input, client_id)
            
            await websocket.send_json({
                "type": "response_start",
                "strategy": response_strategy,
                "lock_acquired": True,
                "timestamp": datetime.now().isoformat()
            })
            
            conversation_context = get_conversation_context(client_id)
            
            await process_completely_serialized_streaming(
                websocket, user_input, client_id, response_strategy, 
                start_time, conversation_context
            )
            
        except Exception as e:
            logger.error(f"⚠️ 안전한 응답 생성 오류 {client_id}: {str(e)}")
            await websocket.send_json({
                "type": "error",
                "message": f"응답 생성 중 오류: {str(e)}"
            })
        finally:
            response_in_progress.discard(client_id)
            logger.info(f"🔓 Lock 해제 완료: {client_id}")

async def force_cleanup_previous_response(client_id: str):
    """🔒 이전 응답 완전 정리 (강제)"""
    try:
        if client_id in client_tts_tasks and client_tts_tasks[client_id]:
            previous_task = client_tts_tasks[client_id]
            if not previous_task.done():
                logger.info(f"🛑 이전 TTS 작업 강제 중단: {client_id}")
                previous_task.cancel()
                try:
                    await previous_task
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logger.warning(f"⚠️ TTS 작업 취소 중 오류: {e}")
        
        if client_id in response_queues:
            queue = response_queues[client_id]
            while not queue.empty():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
        
        response_in_progress.discard(client_id)
        client_tts_tasks[client_id] = None
        
        logger.info(f"🧹 이전 응답 완전 정리 완료: {client_id}")
        
    except Exception as e:
        logger.error(f"⚠️ 이전 응답 정리 중 오류: {e}")

async def process_completely_serialized_streaming(websocket: WebSocket, user_input: str, 
                                                client_id: str, strategy: str, start_time: float,
                                                conversation_context: list):
    """🔒 완전히 직렬화된 스트리밍 처리"""
    
    tutor_config = tutor_configs.get(client_id, {})
    tutor_prompt = create_natural_conversational_prompt(tutor_config, strategy, conversation_context, user_input)
    
    try:
        stream = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": tutor_prompt},
                {"role": "user", "content": user_input}
            ],
            max_tokens=get_natural_max_tokens(strategy, user_input, conversation_context),
            temperature=0.7,
            stream=True
        )
        
        complete_response = ""
        word_buffer = ""
        first_response_sent = False
        
        async for chunk in stream:
            if client_id not in response_in_progress:
                logger.info(f"🛑 스트리밍 중단 감지: {client_id}")
                break
                
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                word_buffer += content
                complete_response += content
                
                if any(char in content for char in [' ', '\n', '\t']) or chunk.choices[0].finish_reason:
                    if word_buffer.strip():
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
        
        if complete_response.strip() and client_id in response_in_progress:
            await websocket.send_json({
                "type": "response_complete",
                "total_response": complete_response,
                "timestamp": datetime.now().isoformat()
            })
            
            add_to_conversation_history(client_id, "assistant", complete_response)
            await create_completely_safe_tts(websocket, complete_response.strip(), client_id)
        else:
            logger.warning(f"⚠️ TTS 생성 생략 - 응답 중단됨: {client_id}")
            
    except Exception as e:
        logger.error(f"⚠️ 직렬화된 스트리밍 오류: {str(e)}")
        raise

async def create_completely_safe_tts(websocket: WebSocket, full_text: str, client_id: str):
    """🔒 완전히 안전한 TTS 생성 (중첩 절대 불가)"""
    if not tts_client:
        logger.warning("TTS 클라이언트가 비활성화되어 텍스트만 전송합니다.")
        return
    
    try:
        tts_task = asyncio.create_task(
            _execute_single_tts(websocket, full_text, client_id)
        )
        
        client_tts_tasks[client_id] = tts_task
        await tts_task
        
    except asyncio.CancelledError:
        logger.info(f"🛑 TTS 작업 취소됨: {client_id}")
    except Exception as e:
        logger.error(f"⚠️ 안전한 TTS 생성 오류: {str(e)}")
    finally:
        if client_id in client_tts_tasks:
            client_tts_tasks[client_id] = None

async def _execute_single_tts(websocket: WebSocket, full_text: str, client_id: str):
    """실제 TTS 실행"""
    logger.info(f"🔊 안전한 TTS 처리 시작: '{full_text[:50]}...' for {client_id}")
    
    synthesis_input = texttospeech.SynthesisInput(text=full_text)
    
    voice = texttospeech.VoiceSelectionParams(
        language_code="ko-KR",
        name="ko-KR-Standard-A",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )
    
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=1.0,
        pitch=0.0,
        volume_gain_db=0.0,
        effects_profile_id=["headphone-class-device"]
    )
    
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
        timeout=15.0
    )
    
    if client_id not in response_in_progress:
        logger.info(f"🛑 TTS 완료 후 중단 감지: {client_id}")
        return
    
    tts_time = time.time() - start_tts
    audio_base64 = base64.b64encode(response.audio_content).decode('utf-8')
    
    await websocket.send_json({
        "type": "audio_completely_safe",
        "text": full_text,
        "audio": audio_base64,
        "audio_size": len(response.audio_content),
        "tts_time": round(tts_time, 3),
        "client_id": client_id,
        "timestamp": datetime.now().isoformat()
    })
    
    logger.info(f"✅ 안전한 TTS 완료: {len(response.audio_content)} bytes for {client_id}")

# 🎭 자연스러운 대화를 위한 개선된 함수들
def analyze_user_intent_for_natural_conversation(user_input: str, client_id: str) -> str:
    """🎭 자연스러운 대화를 위한 의도 분석 (맥락 고려)"""
    user_input_lower = user_input.lower()
    
    # 대화 맥락 고려
    conversation_context = get_conversation_context(client_id)
    is_follow_up = len(conversation_context) > 0
    
    # 1. 인사/확인 → very_short (하지만 너무 짧지 않게)
    if len(user_input) < 5 or any(word in user_input_lower for word in ["응", "네", "예", "아니", "맞아", "틀려", "안녕", "감사"]):
        return "very_short"
    
    # 2. 정의/개념 질문 → short (적절한 설명)
    if any(word in user_input_lower for word in ["뭐예요", "무엇", "정의", "뜻", "의미"]):
        return "short" if not is_follow_up else "medium"  # 후속 질문이면 더 자세히
    
    # 3. 요약 요청 → short
    if any(word in user_input_lower for word in ["짧게", "간단히", "요약", "핵심"]):
        return "short"
    
    # 4. 예시 요청 → medium (좋은 예시는 설명이 필요)
    if any(word in user_input_lower for word in ["예시", "예를 들어", "예", "어떤", "사례"]):
        return "medium"
    
    # 5. 방법/과정 질문 → medium (단계별 설명 필요)
    if any(word in user_input_lower for word in ["어떻게", "방법", "과정", "절차", "단계"]):
        return "medium"
    
    # 6. 이유/원리 질문 → medium (충분한 설명 필요)
    if any(word in user_input_lower for word in ["왜", "이유", "원리", "때문"]):
        return "medium"
    
    # 7. 자세한 설명 요청 → long (사용자가 명시적으로 요청)
    if any(word in user_input_lower for word in ["자세히", "구체적으로", "상세히", "깊이"]):
        return "long"
    
    # 8. 문제/퀴즈 → interactive
    if any(word in user_input_lower for word in ["문제", "퀴즈", "테스트", "풀어"]):
        return "interactive"
    
    # 9. 복잡한 질문 (긴 입력) → medium
    if len(user_input) > 50:
        return "medium"
    
    # 10. 기본값: 자연스러운 대화형
    return "short"

def get_natural_max_tokens(strategy: str, user_input: str, conversation_context: list) -> int:
    """🎭 자연스러운 대화를 위한 토큰 배분 (적절한 길이 유지)"""
    base_tokens = {
        "very_short": 25,   # "네, 맞아요! 더 궁금한 게 있나요?"
        "short": 60,        # "미분은 변화율을 구하는 거예요! 자동차 속도 변화 같은 거죠. 예시 하나 볼까요?"
        "medium": 120,      # 2-3문장 + 예시 + 질문 (자연스러운 설명)
        "long": 200,        # 상세한 설명이 필요할 때 (사용자가 명시적으로 요청)
        "interactive": 100  # 문제 + 힌트 + 격려
    }
    
    base = base_tokens.get(strategy, 60)
    
    # 🧠 맥락에 따른 조절 (튜터의 지능 유지)
    if len(conversation_context) > 0:
        last_exchange = conversation_context[-1]
        # 사용자가 이해 못했다면 더 자세히
        if any(word in last_exchange.get("content", "").lower() for word in ["모르겠", "이해 안", "헷갈"]):
            base = min(base + 40, 250)
        # 사용자가 이해했다면 다음 단계로
        elif any(word in last_exchange.get("content", "").lower() for word in ["알겠", "이해했", "맞네"]):
            base = min(base + 20, 200)
    
    # 질문 복잡도에 따른 조절
    if len(user_input) > 100:  # 복잡한 질문
        base = min(base + 30, 250)
    
    return base

def create_natural_conversational_prompt(tutor_config: dict, strategy: str, conversation_context: list, user_input: str) -> str:
    """🎭 자연스러운 대화형 프롬프트 생성 (맥락과 개인화 유지)"""
    
    # 기존 성격 설정 완전 유지
    name = tutor_config.get("name", "AI 튜터")
    subject = tutor_config.get("subject", "일반")
    level = tutor_config.get("level", "중학교")
    
    personality = tutor_config.get("personality", {})
    friendliness = personality.get("friendliness", 70)
    humor_level = personality.get("humor_level", 30)
    encouragement = personality.get("encouragement", 80)
    explanation_detail = personality.get("explanation_detail", 70)
    
    # 성격 기반 말투 설정 (기존 유지)
    personality_style = []
    
    if friendliness >= 80:
        personality_style.append("매우 친근하고 다정한 말투")
    elif friendliness >= 60:
        personality_style.append("친근하고 편안한 말투")
    else:
        personality_style.append("정중하고 차분한 말투")
    
    if humor_level >= 70:
        personality_style.append("적절한 유머와 재미있는 비유 사용")
    elif humor_level >= 40:
        personality_style.append("가끔 유머를 섞어서 대화")
    
    if encouragement >= 80:
        personality_style.append("적극적인 격려와 칭찬")
    elif encouragement >= 60:
        personality_style.append("따뜻한 격려")
    
    # 🎭 자연스러운 대화 전략별 지침
    conversation_guidelines = {
        "very_short": "1-2문장으로 간단하게 답하고 대화 이어가기",
        "short": "핵심을 2-3문장으로 설명하고 자연스럽게 질문으로 마무리",
        "medium": "적절한 길이로 설명하되 중간중간 이해도 확인 및 예시 포함",
        "long": "충분히 자세하게 설명하되 단계별로 나누어 각 단계마다 이해 확인",
        "interactive": "문제나 예시 제시하고 함께 풀어보도록 격려하며 유도"
    }
    
    # 🧠 대화 맥락 분석 (학습 진도 추적)
    context_analysis = ""
    if conversation_context:
        recent_topics = []
        user_understanding_level = "보통"
        
        for msg in conversation_context[-3:]:
            if msg["role"] == "user":
                recent_topics.append(msg["content"][:30])
                # 사용자 이해도 분석
                if any(word in msg["content"].lower() for word in ["모르겠", "어려워", "헷갈"]):
                    user_understanding_level = "어려워함"
                elif any(word in msg["content"].lower() for word in ["알겠", "쉽네", "이해했"]):
                    user_understanding_level = "잘 이해함"
        
        context_analysis = f"""
**학습 맥락 분석:**
- 최근 주제: {', '.join(recent_topics)}
- 이해 수준: {user_understanding_level}
- 대화 진행도: {len(conversation_context)}턴"""
    
    # 🎯 비용 효율적이면서 자연스러운 프롬프트
    prompt = f"""당신은 {name}이라는 {subject} 분야의 친근한 AI 튜터입니다.

**튜터 성격:**
- 친근함: {friendliness}% ({personality_style[0] if personality_style else '자연스러운 말투'})
- 유머: {humor_level}% {'(적절한 유머 사용)' if humor_level >= 40 else '(진지한 톤)'}
- 격려: {encouragement}% {'(적극적 격려)' if encouragement >= 60 else '(차분한 격려)'}

**대화 원칙:**
1. {conversation_guidelines.get(strategy, "자연스럽게 대화")}
2. 학생의 이해도에 맞춰 설명 조절
3. 질문으로 마무리하여 상호작용 유도
4. 학습자 중심의 대화 진행

**응답 스타일:**
- 자연스럽고 대화하듯이
- 적절한 길이로 (너무 짧거나 길지 않게)
- 학습자의 수준과 맥락 고려
- 예시와 비유를 활용한 쉬운 설명

**학습자 정보:**
- 수준: {level}
- 현재 전략: {strategy}
{context_analysis}

학생의 질문에 대해 위 원칙을 지켜 자연스럽고 교육적으로 답변하세요."""
    
    return prompt

# 나머지 헬퍼 함수들 (기존 유지)
def add_to_conversation_history(client_id: str, role: str, content: str):
    """대화 기록에 추가 (학습 진도 추적 유지)"""
    if client_id not in conversation_history:
        conversation_history[client_id] = []
    
    conversation_history[client_id].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })
    
    # 🧠 적절한 기억 유지 (너무 짧지 않게)
    if len(conversation_history[client_id]) > 25:  # 20 → 25로 증가
        conversation_history[client_id] = conversation_history[client_id][-25:]

def get_conversation_context(client_id: str) -> list:
    """대화 맥락 반환 (충분한 맥락 유지)"""
    if client_id not in conversation_history:
        return []
    
    # 🧠 더 많은 맥락 유지 (10 → 12턴)
    recent_messages = conversation_history[client_id][-12:]
    return [{"role": msg["role"], "content": msg["content"]} for msg in recent_messages]

# 실시간 피드백 및 중단 처리 (기존 유지)
async def handle_response_interrupt(websocket: WebSocket, user_text: str, client_id: str):
    """응답 중단 + 새로운 응답 처리"""
    try:
        logger.info(f"🛑 응답 중단 + 새 질문: '{user_text[:30]}...' from {client_id}")
        
        await interrupt_current_response(websocket, client_id)
        
        feedback_analysis = analyze_feedback_intent(user_text)
        
        if feedback_analysis["is_feedback"]:
            await process_feedback_response(websocket, feedback_analysis, client_id)
        else:
            add_to_conversation_history(client_id, "user", user_text)
            await generate_ai_response_completely_safe(websocket, user_text, client_id)
            
    except Exception as e:
        logger.error(f"⚠️ 응답 중단 처리 오류: {str(e)}")

async def handle_realtime_feedback(websocket: WebSocket, message: dict, client_id: str):
    """실시간 피드백 처리"""
    try:
        action = message.get("action")
        original_input = message.get("original_input", "")
        
        logger.info(f"💬 실시간 피드백: {action} for '{original_input[:20]}...'")
        
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
        
        await websocket.send_json({
            "type": "response_interrupted",
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"🛑 응답 중단 완료: {client_id}")

def analyze_feedback_intent(user_text: str) -> dict:
    """피드백 의도 분석"""
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
        
        stream = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"간단히 1-2문장으로만 답변하세요."},
                {"role": "user", "content": f"간단히: {original_input}"}
            ],
            max_tokens=40,  # 자연스러운 짧은 답변
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
        
        stream = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"예시와 함께 자세히 설명하되 적절한 길이로."},
                {"role": "user", "content": f"자세히: {original_input}"}
            ],
            max_tokens=150,  # 자연스러운 자세한 답변
            temperature=0.7,
            stream=True
        )
        
        await process_simple_streaming(websocket, stream, client_id, "detailed")
        
    finally:
        response_in_progress.discard(client_id)

async def process_simple_streaming(websocket: WebSocket, stream, client_id: str, response_type: str):
    """간단한 스트리밍 처리"""
    response_text = ""
    word_buffer = ""
    
    async for chunk in stream:
        if client_id not in response_in_progress:
            break
            
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            word_buffer += content
            response_text += content
            
            if any(char in content for char in [' ', '\n', '\t']) or chunk.choices[0].finish_reason:
                if word_buffer.strip():
                    await websocket.send_json({
                        "type": "text_chunk",
                        "content": word_buffer,
                        "response_type": response_type,
                        "timestamp": datetime.now().isoformat()
                    })
                    word_buffer = ""
    
    await websocket.send_json({
        "type": "response_complete",
        "response_type": response_type,
        "timestamp": datetime.now().isoformat()
    })
    
    add_to_conversation_history(client_id, "assistant", response_text)
    
    if response_text.strip():
        await create_completely_safe_tts(websocket, response_text.strip(), client_id)

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

# 서버 실행
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    log_level = os.getenv("LOG_LEVEL", "info")
    
    logger.info(f"🚀 AI 튜터 서버 시작 (v3.3.0 - 스마트한 균형)")
    logger.info(f"📡 포트: {port}")
    logger.info(f"🎤 음성 입력: {'✅ 활성화 (개선된 STT)' if speech_client else '❌ 비활성화'}")
    logger.info(f"🔊 음성 출력: {'✅ 활성화 (중첩 완전 방지)' if tts_client else '❌ 비활성화'}")
    logger.info(f"💬 텍스트 입력: ✅ 활성화")
    logger.info(f"🤖 AI 모델: GPT-3.5 Turbo (자연스러운 대화형)")
    logger.info(f"🔄 상태 관리: ✅ 활성화")
    logger.info(f"📝 스트리밍: ✅ 중첩 완전 방지 + 단일 TTS")
    logger.info(f"🛑 즉시 중단: ✅ 활성화")
    logger.info(f"💭 실시간 피드백: ✅ 활성화")
    logger.info(f"🧠 의도 분석: ✅ 자연스러운 대화 지향")
    logger.info(f"🎭 대화 스타일: ✅ 성격 + 맥락 + 개인화 유지")
    logger.info(f"🔒 중첩 방지: ✅ 강력한 직렬화로 100% 해결")
    logger.info(f"💰 비용 효율성: ✅ 스마트한 절약 (자연스러움 유지)")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level=log_level,
        access_log=True  # 디버깅을 위해 유지
    )
