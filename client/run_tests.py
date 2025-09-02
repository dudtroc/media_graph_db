#!/usr/bin/env python3
"""
테스트 실행 스크립트
"""

import sys
import os
import subprocess

def run_command(command, description):
    """명령어 실행 및 결과 출력"""
    print(f"\n🚀 {description}")
    print(f"명령어: {command}")
    print("-" * 50)
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✅ 성공!")
        if result.stdout:
            print("출력:")
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 실패: {e}")
        if e.stderr:
            print("오류:")
            print(e.stderr)
        return False

def main():
    """메인 실행 함수"""
    print("🧪 Scene Graph Database 테스트 실행기")
    print("=" * 50)
    
    # 현재 디렉토리 확인
    current_dir = os.getcwd()
    print(f"현재 디렉토리: {current_dir}")
    
    # 테스트 실행 옵션
    print("\n실행할 테스트를 선택하세요:")
    print("1. API 테스트")
    print("2. 모든 테스트")
    print("3. 종료")
    
    while True:
        try:
            choice = input("\n선택 (1-3): ").strip()
            
            if choice == "1":
                print("\n🌐 API 테스트 실행")
                print("⚠️  API 서버가 실행 중인지 확인하세요!")
                success = run_command(
                    "python test_api.py",
                    "API 테스트"
                )
                if success:
                    print("\n✅ API 테스트 완료!")
                break
                
            elif choice == "2":
                print("\n🔍 모든 테스트 실행")
                
                # API 테스트
                api_success = run_command(
                    "python test_api.py",
                    "API 테스트"
                )
                
                if api_success:
                    print("\n✅ 모든 테스트 완료!")
                else:
                    print("\n⚠️  일부 테스트가 실패했습니다.")
                break
                
            elif choice == "3":
                print("👋 테스트 실행기를 종료합니다.")
                break
                
            else:
                print("❌ 잘못된 선택입니다. 1-3 중에서 선택해주세요.")
                
        except KeyboardInterrupt:
            print("\n\n👋 테스트 실행기를 종료합니다.")
            break
        except Exception as e:
            print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    main()

