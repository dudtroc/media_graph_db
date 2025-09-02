#!/usr/bin/env python3
"""
간단한 환경 설정 테스트
"""

import os
import sys
from dotenv import load_dotenv

def test_environment():
    """환경 변수 테스트"""
    print("🔧 환경 설정 테스트")
    print("=" * 30)
    
    # 환경 변수 로드
    load_dotenv()
    
    # 필수 환경 변수 확인
    required_vars = [
        "API_URL",
        "DB_HOST", 
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
        "DB_PORT"
    ]
    
    print("📋 환경 변수 확인:")
    all_good = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: {value}")
        else:
            print(f"  ❌ {var}: 설정되지 않음")
            all_good = False
    
    print()
    
    if all_good:
        print("✅ 모든 환경 변수가 설정되었습니다.")
        print("💡 이제 API 테스트를 실행할 수 있습니다.")
    else:
        print("⚠️  일부 환경 변수가 설정되지 않았습니다.")
        print("💡 env.example 파일을 .env로 복사하고 설정을 확인하세요.")
    
    return all_good

def test_python_packages():
    """Python 패키지 테스트"""
    print("\n🐍 Python 패키지 테스트")
    print("=" * 30)
    
    required_packages = [
        "requests",
        "numpy",
        "python-dotenv"
    ]
    
    print("📦 필수 패키지 확인:")
    all_good = True
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}: 설치됨")
        except ImportError:
            print(f"  ❌ {package}: 설치되지 않음")
            all_good = False
    
    print()
    
    if all_good:
        print("✅ 모든 필수 패키지가 설치되었습니다.")
    else:
        print("⚠️  일부 패키지가 설치되지 않았습니다.")
        print("💡 pip install -r requirements.txt를 실행하세요.")
    
    return all_good

def main():
    """메인 테스트 함수"""
    print("🚀 Scene Graph Database 환경 설정 테스트")
    print("=" * 50)
    
    # 환경 변수 테스트
    env_ok = test_environment()
    
    # 패키지 테스트
    packages_ok = test_python_packages()
    
    print("\n" + "=" * 50)
    
    if env_ok and packages_ok:
        print("🎉 모든 테스트가 통과했습니다!")
        print("💡 이제 API 서버를 시작하고 API 테스트를 실행할 수 있습니다.")
    else:
        print("⚠️  일부 테스트가 실패했습니다.")
        print("💡 위의 안내에 따라 문제를 해결하세요.")
    
    return env_ok and packages_ok

if __name__ == "__main__":
    main()
