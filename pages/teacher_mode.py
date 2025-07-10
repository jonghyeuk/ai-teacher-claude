import asyncio
import base64
import json
import os
import tempfile
import uuid
from datetime import datetime
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import AsyncOpenAI
from google.cloud import texttospeech
from google.cloud import speech
import httpx

# FastAPI 앱 초기화
app = FastAPI(
    title="AI Tutor Realtime System",
    description="실시간 AI 튜터 시스템",
    version="2.0.0"
)

# CORS 설정 (기존 유지)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://*.streamlit.app",
        "https://*.streamlit.io", 
        "http://localhost:8501",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 환경변수 설정 (기존 유지)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")

# OpenAI 클라이언트 초기화 (기존 유지)
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Google TTS 클라이언트 초기화 (기존 유지)
tts_client = texttospeech.TextToSpeechClient()

# Google STT 클라이언트 초기화 (기존 유지)
speech_client = speech.SpeechClient()

# 전역 변수 (기존 유지)
active_connections: Dict[str, WebSocket] = {}
tutor_configs: Dict[str, Dict[str, Any]] = {}

# 기본 엔드포인트들 (기존 유지)
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
    """서비스 상태 확인"""
    try:
        # OpenAI API 연결 테스트
        openai_status = "✅" if OPENAI_API_KEY else "❌"
        
        # Google TTS 연결 테스트
        try:
            tts_client.list_voices()
            tts_status = "✅"
        except Exception:
            tts_status = "❌"
            
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "active_connections": len(active_connections),
            "services": {
                "openai": openai_status,
                "google_tts": tts_status
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.get("/info")
async def system_info():
    """시스템 정보"""
    return {
        "system": "AI Tutor Realtime System",
        "architecture": "2단계: 성능과 비용 균형",
        "components": {
            "frontend": "Streamlit Cloud",
            "backend": "FastAPI on Google Cloud Run",
            "stt": "Google Cloud Speech-to-Text",
            "llm": "GPT-3.5 Turbo Streaming",
            "tts": "Google Cloud TTS Standard",
            "communication": "WebSocket"
        }
    }

# WebSocket 엔드포인트 (기존 유지)
@app.websocket("/ws/tutor/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    active_connections[client_id] = websocket
    print(f"✅ 클라이언트 {client_id} 연결됨")
    
    try:
        # 연결 확인 메시지 전송
        await websocket.send_json({
            "type": "connection_established",
            "message": f"🎓 AI 튜터와 연결되었습니다!"
        })
        
        while True:
            try:
                # 메시지 수신 (타임아웃 설정)
                data = await asyncio.wait_for(websocket.receive(), timeout=60.0)
                
                if data["type"] == "websocket.disconnect":
                    print(f"❌ 클라이언트 {client_id} 정상 연결 종료")
                    break
                
                # JSON 메시지 처리 (튜터 설정 등)
                if data["type"] == "websocket.receive" and "text" in data:
                    try:
                        message = json.loads(data["text"])
                        await handle_text_message(websocket, message, client_id)
                    except json.JSONDecodeError:
                        print(f"⚠️ JSON 파싱 오류: {data['text']}")
                
                # 바이너리 메시지 (오디오) 처리
                elif data["type"] == "websocket.receive" and "bytes" in data:
                    audio_data = data["bytes"]
                    await handle_audio_message(websocket, audio_data, client_id)
                    
            except asyncio.TimeoutError:
                # 타임아웃 시 연결 상태 확인
                try:
                    await websocket.send_json({"type": "ping"})
                except:
                    break
                
    except WebSocketDisconnect:
        print(f"❌ 클라이언트 {client_id} 연결 끊김 (정상)")
    except Exception as e:
        print(f"⚠️ WebSocket 에러: {str(e)}")
    finally:
        # 연결 정리
        if client_id in active_connections:
            del active_connections[client_id]
        if client_id in tutor_configs:
            del tutor_configs[client_id]
        print(f"🔄 클라이언트 {client_id} 정리 완료")

async def handle_text_message(websocket: WebSocket, message: dict, client_id: str):
    """텍스트 메시지 처리 (기존 유지)"""
    try:
        if message.get("type") == "config_update":
            # 튜터 설정 업데이트 (voice_settings 포함)
            config = message.get("config", {})
            
            # voice_settings가 없으면 기본값 추가
            if "voice_settings" not in config:
                config["voice_settings"] = {
                    "auto_play": True,
                    "speed": 1.0,
                    "pitch": 1.0
                }
            
            tutor_configs[client_id] = config
            print(f"📋 튜터 설정 업데이트: {tutor_configs[client_id]}")
            
            await websocket.send_json({
                "type": "config_updated",
                "message": "튜터 설정이 업데이트되었습니다."
            })
        else:
            print(f"⚠️ 알 수 없는 메시지 타입: {message.get('type')}")
            
    except Exception as e:
        print(f"⚠️ 텍스트 메시지 처리 오류: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": f"메시지 처리 중 오류가 발생했습니다: {str(e)}"
        })

async def handle_audio_message(websocket: WebSocket, audio_data: bytes, client_id: str):
    """오디오 메시지 처리 (개선된 버전)"""
    try:
        print(f"🎤 오디오 수신: {len(audio_data)} bytes from {client_id}")
        
        # 오디오 데이터 유효성 검사
        if len(audio_data) < 1000:  # 너무 짧은 오디오
            await websocket.send_json({
                "type": "error", 
                "message": "녹음이 너무 짧습니다. 조금 더 길게 말씀해주세요."
            })
            return
        
        if len(audio_data) > 10 * 1024 * 1024:  # 10MB 초과
            await websocket.send_json({
                "type": "error", 
                "message": "녹음이 너무 깁니다. 짧게 나누어서 말씀해주세요."
            })
            return
        
        # STT 처리
        transcript = await process_speech_to_text(audio_data)
        print(f"🔤 최종 STT 결과: '{transcript}'")
        
        if not transcript or transcript.strip() == "":
            await websocket.send_json({
                "type": "error", 
                "message": "음성을 인식할 수 없었습니다. 명확하게 말씀해주시고 다시 시도해주세요."
            })
            return
        
        # STT 결과 전송
        await websocket.send_json({
            "type": "stt_result",
            "text": transcript
        })
        
        # GPT 응답 생성 및 TTS
        await generate_ai_response(websocket, transcript, client_id)
        
    except Exception as e:
        print(f"⚠️ 오디오 처리 오류: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": f"오디오 처리 중 오류가 발생했습니다: {str(e)}"
        })

async def process_speech_to_text(audio_data: bytes) -> str:
    """Google Speech-to-Text 처리 (개선된 버전)"""
    try:
        print(f"🎤 STT 처리 시작: {len(audio_data)} bytes")
        
        # 다양한 설정으로 시도
        configs_to_try = [
            # 설정 1: WEBM_OPUS (최신 브라우저)
            {
                "encoding": speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                "sample_rate_hertz": 48000,
                "description": "WEBM_OPUS 48kHz"
            },
            # 설정 2: WEBM_OPUS (낮은 샘플레이트)
            {
                "encoding": speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                "sample_rate_hertz": 16000,
                "description": "WEBM_OPUS 16kHz"
            },
            # 설정 3: OGG_OPUS (대안)
            {
                "encoding": speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
                "sample_rate_hertz": 48000,
                "description": "OGG_OPUS 48kHz"
            },
            # 설정 4: 자동 감지
            {
                "encoding": speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,
                "sample_rate_hertz": 48000,
                "description": "AUTO_DETECT"
            }
        ]
        
        for i, config_params in enumerate(configs_to_try):
            try:
                print(f"🔄 STT 시도 {i+1}: {config_params['description']}")
                
                config = speech.RecognitionConfig(
                    encoding=config_params["encoding"],
                    sample_rate_hertz=config_params["sample_rate_hertz"],
                    language_code="ko-KR",
                    enable_automatic_punctuation=True,
                    model="latest_short",
                    # 추가 개선 설정
                    enable_word_time_offsets=False,
                    enable_word_confidence=True,
                    use_enhanced=True,  # 향상된 모델 사용
                    alternative_language_codes=["en-US"]  # 영어 혼재 대응
                )
                
                audio = speech.RecognitionAudio(content=audio_data)
                
                # STT 요청 (타임아웃 추가)
                response = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, 
                        lambda: speech_client.recognize(config=config, audio=audio)
                    ),
                    timeout=10.0
                )
                
                if response.results:
                    transcript = response.results[0].alternatives[0].transcript
                    confidence = response.results[0].alternatives[0].confidence
                    
                    print(f"✅ STT 성공 ({config_params['description']})")
                    print(f"📝 결과: '{transcript}' (신뢰도: {confidence:.2f})")
                    
                    # 신뢰도가 너무 낮으면 다음 설정 시도
                    if confidence < 0.3:
                        print(f"⚠️ 신뢰도 낮음 ({confidence:.2f}), 다음 설정 시도")
                        continue
                    
                    return transcript.strip()
                else:
                    print(f"⚠️ STT 결과 없음 ({config_params['description']})")
                    
            except asyncio.TimeoutError:
                print(f"⏰ STT 타임아웃 ({config_params['description']})")
                continue
            except Exception as e:
                print(f"⚠️ STT 설정 {i+1} 실패: {str(e)}")
                continue
        
        # 모든 설정 실패
        print("❌ 모든 STT 설정 실패")
        return ""
        
    except Exception as e:
        print(f"⚠️ STT 전체 처리 오류: {str(e)}")
        return ""

async def generate_ai_response(websocket: WebSocket, user_input: str, client_id: str):
    """AI 응답 생성 (기존 유지)"""
    try:
        # 튜터 설정 가져오기
        tutor_config = tutor_configs.get(client_id, {})
        
        # 튜터 개성 프롬프트 생성
        tutor_prompt = create_tutor_prompt(tutor_config, user_input)
        print(f"📝 생성된 프롬프트: {tutor_prompt[:100]}...")
        
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
        sentence_buffer = ""
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                response_text += content
                sentence_buffer += content
                
                # 문장 단위로 TTS 처리
                if any(punct in content for punct in ['.', '!', '?', '다', '요', '죠', '니다', '습니다']):
                    if sentence_buffer.strip():
                        await process_and_send_tts(websocket, sentence_buffer.strip())
                        sentence_buffer = ""
        
        # 남은 텍스트 처리
        if sentence_buffer.strip():
            await process_and_send_tts(websocket, sentence_buffer.strip())
            
        print(f"💬 완성된 응답: {response_text}")
        
    except Exception as e:
        print(f"⚠️ AI 응답 생성 오류: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": f"AI 응답 생성 중 오류가 발생했습니다: {str(e)}"
        })

def create_tutor_prompt(tutor_config: dict, user_input: str) -> str:
    """튜터 설정 기반 프롬프트 생성 (기존 유지)"""
    
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
    
    # 성격 기반 지시사항
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
    
    # 최종 프롬프트 생성
    prompt = f"""당신은 {name}이라는 {subject} 전문 선생님입니다.
{level} 수준의 학생들을 가르치는 경험이 풍부합니다.

성격 특성:
- 친근함: {friendliness}%
- 유머 수준: {humor_level}%
- 격려 수준: {encouragement}%
- 설명 상세도: {explanation_detail}%

지시사항:
{chr(10).join(f"- {instruction}" for instruction in personality_instructions)}

- 항상 한국어로 답변하세요.
- 학생의 수준에 맞춰 설명하세요.
- {subject} 분야에 대한 전문 지식을 활용하세요.
- 질문이 {subject}와 관련 없다면 {subject}와 연관지어 설명해보세요.
- 답변은 300자 이내로 간결하게 해주세요.
- 자연스럽고 대화하는 듯한 말투를 사용하세요.

현재 학생의 질문이나 요청에 대해 위 특성을 반영하여 답변해주세요."""
    
    return prompt

async def process_and_send_tts(websocket: WebSocket, text: str):
    """TTS 처리 및 전송 (기존 유지)"""
    try:
        # TTS 요청
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="ko-KR",
            name="ko-KR-Standard-A"
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        response = tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Base64 인코딩
        audio_base64 = base64.b64encode(response.audio_content).decode('utf-8')
        
        # 클라이언트에 전송
        await websocket.send_json({
            "type": "audio_chunk",
            "content": text,
            "audio": audio_base64
        })
        
    except Exception as e:
        print(f"⚠️ TTS 처리 오류: {str(e)}")
        # TTS 실패 시 텍스트만 전송
        await websocket.send_json({
            "type": "text_chunk",
            "content": text
        })

# 서버 실행 (기존 유지)
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
