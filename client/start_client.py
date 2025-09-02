#!/usr/bin/env python3
"""
Scene Graph Database 클라이언트 테스트 실행 스크립트
"""

import os
import sys
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def main():
    """클라이언트 테스트 실행"""
    print("🧪 Scene Graph Database 클라이언트 테스트")
    print("=" * 50)
    
    # 환경 설정 확인
    api_url = os.getenv("API_URL", "http://localhost:8000")
    
    print(f"🌐 API 서버: {api_url}")
    print("=" * 50)
    
    # Docker 환경 감지
    is_docker = (
        os.path.exists('/.dockerenv') or 
        os.environ.get('DOCKER_CONTAINER') == 'true' or
        os.environ.get('KUBERNETES_SERVICE_HOST') is not None or
        'docker' in os.environ.get('HOSTNAME', '').lower()
    )
    
    if is_docker:
        print("\n🐳 Docker 환경에서 실행 중...")
        print("💡 이제 컨테이너에 접속하여 직접 테스트를 실행할 수 있습니다.")
        print("💡 예시: docker exec -it scene_graph_client_test bash")
        print("💡 또는: docker exec -it scene_graph_client_test python")
        print("\n⏳ 컨테이너가 실행 중입니다. Ctrl+C로 종료하거나 다른 터미널에서 접속하세요.")
        
        # Docker 환경에서는 무한 대기
        try:
            while True:
                import time
                time.sleep(3600)  # 1시간마다 로그 출력
                print("🔄 컨테이너가 계속 실행 중입니다...")
        except KeyboardInterrupt:
            print("\n👋 컨테이너를 종료합니다.")
        return
    
    # 로컬 환경에서는 대화형 선택
    print("\n실행할 테스트를 선택하세요:")
    print("1. 환경 설정 테스트 (권장)")
    print("2. API 테스트 (FastAPI 서버 필요)")
    print("3. 모든 테스트")
    print("4. 종료")
    
    while True:
        try:
            choice = input("\n선택 (1-4): ").strip()
            
            if choice == "1":
                print("\n🔧 환경 설정 테스트 실행")
                os.system("python test_simple.py")
                break
                
            elif choice == "2":
                print("\n🌐 API 테스트 실행")
                print("⚠️  API 서버가 실행 중인지 확인하세요!")
                os.system("python test_api.py")
                break
                
            elif choice == "3":
                print("\n🔍 모든 테스트 실행")
                os.system("python run_tests.py")
                break
                
            elif choice == "4":
                print("👋 클라이언트 테스트를 종료합니다.")
                break
                
            else:
                print("❌ 잘못된 선택입니다. 1-4 중에서 선택해주세요.")
                
        except KeyboardInterrupt:
            print("\n\n👋 클라이언트 테스트를 종료합니다.")
            break
        except Exception as e:
            print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    main()
