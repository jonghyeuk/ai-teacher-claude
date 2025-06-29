#!/usr/bin/env python3
"""
AI 튜터 팩토리 실행 스크립트

이 스크립트는 Streamlit 앱을 실행하고 초기 설정을 수행합니다.

사용법:
    python run.py
    python run.py --port 8502
    python run.py --debug
    python run.py --setup
"""

import os
import sys
import argparse
import subprocess
import platform
from pathlib import Path

def check_python_version():
    """Python 버전 확인"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 이상이 필요합니다.")
        print(f"현재 버전: {sys.version}")
        sys.exit(1)
    else:
        print(f"✅ Python {sys.version.split()[0]} 사용 중")

def check_dependencies():
    """필요한 패키지들이 설치되어 있는지 확인"""
    required_packages = [
        "streamlit",
        "anthropic", 
        "google-cloud-texttospeech",
        "python-dotenv"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} 설치됨")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} 누락")
    
    if missing_packages:
        print(f"\n누락된 패키지들을 설치하려면 다음 명령을 실행하세요:")
        print(f"pip install {' '.join(missing_packages)}")
        
        response = input("\n지금 설치하시겠습니까? (y/n): ")
        if response.lower() == 'y':
            install_packages(missing_packages)
        else:
            print("패키지를 먼저 설치한 후 다시 실행해주세요.")
            sys.exit(1)

def install_packages(packages):
    """패키지 설치"""
    try:
        print("패키지 설치 중...")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)
        print("✅ 모든 패키지가 설치되었습니다!")
    except subprocess.CalledProcessError:
        print("❌ 패키지 설치에 실패했습니다.")
        sys.exit(1)

def check_env_file():
    """환경 변수 파일 확인"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print("⚠️ .env 파일이 없습니다.")
            response = input(".env.example을 복사하여 .env 파일을 생성하시겠습니까? (y/n): ")
            if response.lower() == 'y':
                import shutil
                shutil.copy(env_example, env_file)
                print("✅ .env 파일이 생성되었습니다.")
                print("📝 .env 파일을 열어서 API 키를 설정해주세요.")
                
                # 운영체제에 따라 파일 열기
                if platform.system() == "Windows":
                    os.startfile(env_file)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.call(["open", env_file])
                else:  # Linux
                    subprocess.call(["xdg-open", env_file])
                
                input("API 키 설정 완료 후 Enter를 눌러주세요...")
        else:
            print("❌ .env.example 파일이 없습니다.")
    else:
        print("✅ .env 파일 존재")

def check_api_keys():
    """API 키 설정 확인"""
    from dotenv import load_dotenv
    load_dotenv()
    
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not anthropic_key:
        print("⚠️ ANTHROPIC_API_KEY가 설정되지 않았습니다.")
        print("Claude API를 사용하려면 .env 파일에 API 키를 설정해주세요.")
        return False
    elif anthropic_key.startswith("sk-ant-"):
        print("✅ Claude API 키 설정됨")
        return True
    else:
        print("⚠️ Claude API 키 형식이 올바르지 않습니다.")
        return False

def setup_directories():
    """필요한 디렉토리 생성"""
    directories = ["data", "logs", "uploads"]
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(exist_ok=True)
            print(f"✅ {directory} 디렉토리 생성됨")

def run_streamlit(port=8501, debug=False):
    """Streamlit 앱 실행"""
    print(f"\n🚀 AI 튜터 팩토리를 시작합니다...")
    print(f"포트: {port}")
    print(f"브라우저에서 http://localhost:{port} 를 열어주세요\n")
    
    # Streamlit 명령어 구성
    cmd = [
        "streamlit", "run", "app.py",
        "--server.port", str(port),
        "--server.address", "localhost"
    ]
    
    if debug:
        cmd.extend(["--logger.level", "debug"])
    
    # 환경 변수 설정
    env = os.environ.copy()
    if debug:
        env["STREAMLIT_ENV"] = "development"
        env["DEBUG"] = "true"
    
    try:
        subprocess.run(cmd, env=env)
    except KeyboardInterrupt:
        print("\n👋 AI 튜터 팩토리를 종료합니다.")
    except FileNotFoundError:
        print("❌ Streamlit이 설치되지 않았습니다.")
        print("다음 명령으로 설치해주세요: pip install streamlit")

def setup_mode():
    """초기 설정 모드"""
    print("🔧 AI 튜터 팩토리 초기 설정을 시작합니다...\n")
    
    check_python_version()
    check_dependencies() 
    setup_directories()
    check_env_file()
    
    api_configured = check_api_keys()
    
    print("\n" + "="*50)
    print("📋 설정 완료 상태:")
    print("="*50)
    print(f"✅ Python 버전: {sys.version.split()[0]}")
    print(f"✅ 필요 패키지: 설치됨")
    print(f"✅ 디렉토리: 생성됨")
    print(f"{'✅' if api_configured else '⚠️'} API 키: {'설정됨' if api_configured else '미설정'}")
    
    if not api_configured:
        print("\n📝 .env 파일에서 ANTHROPIC_API_KEY를 설정해주세요.")
        print("Claude API 키는 https://console.anthropic.com/ 에서 발급받을 수 있습니다.")
    
    print("\n설정이 완료되었습니다!")
    print("다음 명령으로 앱을 실행하세요: python run.py")

def main():
    parser = argparse.ArgumentParser(description="AI 튜터 팩토리 실행 스크립트")
    parser.add_argument("--port", type=int, default=8501, help="포트 번호 (기본값: 8501)")
    parser.add_argument("--debug", action="store_true", help="디버그 모드로 실행")
    parser.add_argument("--setup", action="store_true", help="초기 설정 모드")
    parser.add_argument("--check", action="store_true", help="시스템 상태 확인만 수행")
    
    args = parser.parse_args()
    
    if args.setup:
        setup_mode()
        return
    
    if args.check:
        print("🔍 시스템 상태 확인 중...\n")
        check_python_version()
        check_dependencies()
        check_env_file()
        check_api_keys()
        print("\n시스템 상태 확인 완료!")
        return
    
    # 기본 실행 모드
    print("🎓 AI 튜터 팩토리")
    print("="*30)
    
    # 빠른 상태 확인
    check_python_version()
    
    try:
        import streamlit
        print("✅ Streamlit 사용 가능")
    except ImportError:
        print("❌ Streamlit이 설치되지 않았습니다.")
        print("설치: pip install streamlit")
        sys.exit(1)
    
    # API 키 확인 (경고만 표시)
    try:
        from dotenv import load_dotenv
        load_dotenv()
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("⚠️ Claude API 키가 설정되지 않았습니다.")
            print("일부 기능이 제한될 수 있습니다.")
    except:
        pass
    
    # Streamlit 실행
    run_streamlit(port=args.port, debug=args.debug)

if __name__ == "__main__":
    main()
