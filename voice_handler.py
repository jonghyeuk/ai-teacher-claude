import streamlit as st
import os
import time
import base64
from google.cloud import texttospeech
from typing import Dict, Optional
import tempfile
import json

def initialize_tts_client():
    """Google Cloud Text-to-Speech 클라이언트 초기화"""
    try:
        # Google Cloud 서비스 계정 키 설정
        credentials_json = os.getenv('GOOGLE_CLOUD_CREDENTIALS') or st.secrets.get('GOOGLE_CLOUD_CREDENTIALS')
        
        if credentials_json:
            # 임시 파일에 인증 정보 저장
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(json.loads(credentials_json), f)
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f.name
        
        client = texttospeech.TextToSpeechClient()
        return client
    except Exception as e:
        st.warning(f"Google Cloud TTS 초기화 실패: {str(e)}. 브라우저 기본 TTS를 사용합니다.")
        return None

def text_to_speech(text: str, voice_settings: Dict) -> Optional[str]:
    """텍스트를 음성으로 변환"""
    client = initialize_tts_client()
    
    if client:
        return google_cloud_tts(text, voice_settings, client)
    else:
        return browser_tts(text, voice_settings)

def google_cloud_tts(text: str, voice_settings: Dict, client) -> Optional[str]:
    """Google Cloud TTS를 사용한 음성 생성"""
    try:
        # 텍스트 전처리 (SSML 태그 제거)
        clean_text = clean_text_for_tts(text)
        
        # 음성 합성 요청 설정
        synthesis_input = texttospeech.SynthesisInput(text=clean_text)
        
        # 음성 설정
        voice = texttospeech.VoiceSelectionParams(
            language_code="ko-KR",
            name="ko-KR-Standard-A",  # 한국어 여성 음성
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )
        
        # 오디오 설정
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=voice_settings.get('speed', 1.0),
            pitch=voice_settings.get('pitch', 1.0)
        )
        
        # 음성 합성 실행
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # 오디오 데이터를 base64로 인코딩
        audio_base64 = base64.b64encode(response.audio_content).decode()
        
        # Streamlit에서 오디오 재생
        if voice_settings.get('auto_play', True):
            st.audio(response.audio_content, format='audio/mp3', autoplay=True)
        
        return audio_base64
        
    except Exception as e:
        st.error(f"Google Cloud TTS 오류: {str(e)}")
        return browser_tts(text, voice_settings)

def browser_tts(text: str, voice_settings: Dict) -> str:
    """브라우저 내장 TTS를 사용한 음성 생성"""
    try:
        # JavaScript를 사용한 브라우저 TTS
        clean_text = clean_text_for_tts(text)
        speed = voice_settings.get('speed', 1.0)
        pitch = voice_settings.get('pitch', 1.0)
        
        # Web Speech API를 사용한 TTS
        tts_script = f"""
        <script>
        function speakText() {{
            const text = `{clean_text}`;
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'ko-KR';
            utterance.rate = {speed};
            utterance.pitch = {pitch};
            
            // 한국어 음성 찾기
            const voices = speechSynthesis.getVoices();
            const koreanVoice = voices.find(voice => voice.lang.includes('ko'));
            if (koreanVoice) {{
                utterance.voice = koreanVoice;
            }}
            
            speechSynthesis.speak(utterance);
        }}
        
        // 음성 목록이 로드되면 실행
        if (speechSynthesis.getVoices().length > 0) {{
            speakText();
        }} else {{
            speechSynthesis.onvoiceschanged = function() {{
                speakText();
            }};
        }}
        </script>
        """
        
        if voice_settings.get('auto_play', True):
            st.components.v1.html(tts_script, height=0)
        
        return "browser_tts_played"
        
    except Exception as e:
        st.error(f"브라우저 TTS 오류: {str(e)}")
        return None

def clean_text_for_tts(text: str) -> str:
    """TTS를 위한 텍스트 정리"""
    import re
    
    # 칠판 포맷팅 태그 제거
    text = re.sub(r'\[RED\]([^[]+)\[/RED\]', r'\1', text)
    text = re.sub(r'\[BLUE\]([^[]+)\[/BLUE\]', r'\1', text)
    text = re.sub(r'\[GREEN\]([^[]+)\[/GREEN\]', r'\1', text)
    text = re.sub(r'\[CIRCLE\]([^[]+)\[/CIRCLE\]', r'\1', text)
    
    # 마크다운 태그 제거
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'##\s*([^\n]+)', r'\1', text)
    text = re.sub(r'#\s*([^\n]+)', r'\1', text)
    
    # 수식 태그 제거하고 읽기 쉽게 변환
    text = re.sub(r'\$([^$]+)\$', r'\1', text)
    
    # 특수 문자 및 이모지 제거
    text = re.sub(r'[📋🎓👨‍🏫🔊💬⚙️📝🎯💾🏠🗑️🎤]', '', text)
    
    # 연속된 공백 정리
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def speech_to_text(audio_data=None) -> Optional[str]:
    """음성을 텍스트로 변환 (STT)"""
    try:
        # 실제 구현에서는 여기에 STT 로직이 들어감
        # Google Cloud Speech-to-Text API 또는 브라우저 Web Speech API 사용
        
        # 현재는 시뮬레이션을 위한 더미 데이터
        st.info("음성 인식 기능은 현재 개발 중입니다. 텍스트로 입력해주세요.")
        
        # 실제로는 오디오 데이터를 처리해서 텍스트 반환
        return None
        
    except Exception as e:
        st.error(f"음성 인식 오류: {str(e)}")
        return None

def create_audio_player(audio_data: bytes, voice_settings: Dict) -> str:
    """오디오 플레이어 생성"""
    try:
        # base64로 인코딩
        audio_base64 = base64.b64encode(audio_data).decode()
        
        # HTML 오디오 플레이어
        audio_html = f"""
        <audio controls style="width: 100%;">
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            Your browser does not support the audio element.
        </audio>
        """
        
        return audio_html
        
    except Exception as e:
        st.error(f"오디오 플레이어 생성 오류: {str(e)}")
        return ""

def get_available_voices():
    """사용 가능한 음성 목록 조회"""
    client = initialize_tts_client()
    
    if client:
        try:
            voices = client.list_voices()
            korean_voices = [
                voice for voice in voices.voices 
                if voice.language_codes[0].startswith('ko')
            ]
            return korean_voices
        except:
            pass
    
    # 기본 음성 목록
    return [
        {"name": "ko-KR-Standard-A", "gender": "FEMALE"},
        {"name": "ko-KR-Standard-B", "gender": "FEMALE"},
        {"name": "ko-KR-Standard-C", "gender": "MALE"},
        {"name": "ko-KR-Standard-D", "gender": "MALE"}
    ]

def record_audio_webrtc():
    """WebRTC를 사용한 실시간 오디오 녹음"""
    try:
        from streamlit_webrtc import webrtc_streamer, WebRtcMode
        
        # WebRTC 스트리머 설정
        webrtc_ctx = webrtc_streamer(
            key="speech-to-text",
            mode=WebRtcMode.SENDONLY,
            audio_receiver_size=1024,
            media_stream_constraints={"video": False, "audio": True},
        )
        
        if webrtc_ctx.audio_receiver:
            # 오디오 데이터 처리
            audio_frames = webrtc_ctx.audio_receiver.get_frames(timeout=1)
            if audio_frames:
                # 여기서 STT 처리
                pass
                
    except ImportError:
        st.warning("WebRTC 패키지가 설치되지 않았습니다. 대체 방법을 사용합니다.")
    except Exception as e:
        st.error(f"오디오 녹음 오류: {str(e)}")

def test_voice_settings(text="안녕하세요. 음성 테스트입니다.", voice_settings=None):
    """음성 설정 테스트"""
    if voice_settings is None:
        voice_settings = {"speed": 1.0, "pitch": 1.0, "auto_play": True}
    
    st.write("🔊 음성 테스트")
    
    if st.button("테스트 음성 재생"):
        text_to_speech(text, voice_settings)
        st.success("음성이 재생되었습니다!")
