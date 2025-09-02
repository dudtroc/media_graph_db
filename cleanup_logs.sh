#!/bin/bash

echo "🧹 Docker 로그 정리 스크립트"
echo "================================"

# 현재 Docker 로그 사용량 확인
echo "📊 현재 Docker 로그 사용량:"
sudo du -sh /var/lib/docker/containers/*/ 2>/dev/null | sort -hr | head -10

# 로그 파일 크기별 정렬
echo -e "\n📋 로그 파일 크기별 정렬:"
sudo find /var/lib/docker/containers -type f -name "*-json.log" \
  -printf '%s %p\n' 2>/dev/null | sort -nr | head -10 | \
  awk '{printf "%10.1f MB %s\n",$1/1024/1024,$2}'

# 실행 중인 컨테이너 확인
echo -e "\n🐳 실행 중인 컨테이너:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 로그 정리 옵션
echo -e "\n🔧 로그 정리 옵션:"
echo "1. 특정 컨테이너 로그만 정리"
echo "2. 모든 컨테이너 로그 정리"
echo "3. Docker 시스템 정리 (사용하지 않는 이미지, 컨테이너, 볼륨)"
echo "4. 종료"

read -p "선택 (1-4): " choice

case $choice in
    1)
        echo -e "\n📝 특정 컨테이너 로그 정리"
        docker ps --format "{{.Names}}" | nl
        read -p "컨테이너 번호 선택: " container_num
        container_name=$(docker ps --format "{{.Names}}" | sed -n "${container_num}p")
        if [ -n "$container_name" ]; then
            echo "🧹 $container_name 컨테이너 로그 정리 중..."
            docker logs --since 1h "$container_name" > /dev/null 2>&1
            echo "✅ 로그 정리 완료"
        else
            echo "❌ 잘못된 컨테이너 번호"
        fi
        ;;
    2)
        echo -e "\n🧹 모든 컨테이너 로그 정리 중..."
        docker system prune -f
        echo "✅ 모든 로그 정리 완료"
        ;;
    3)
        echo -e "\n🗑️  Docker 시스템 정리 중..."
        docker system prune -a -f --volumes
        echo "✅ 시스템 정리 완료"
        ;;
    4)
        echo "👋 종료합니다."
        exit 0
        ;;
    *)
        echo "❌ 잘못된 선택입니다."
        ;;
esac

# 정리 후 상태 확인
echo -e "\n📊 정리 후 Docker 로그 사용량:"
sudo du -sh /var/lib/docker/containers/*/ 2>/dev/null | sort -hr | head -5
