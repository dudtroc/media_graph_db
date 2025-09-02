#!/bin/bash

echo "📊 Docker 로그 모니터링 스크립트"
echo "================================="

# 로그 크기 임계값 설정 (MB)
THRESHOLD=100

while true; do
    clear
    echo "🕐 $(date)"
    echo "📊 Docker 로그 모니터링 중... (Ctrl+C로 종료)"
    echo "================================================"
    
    # 로그 크기 확인
    echo "📋 컨테이너별 로그 크기:"
    sudo find /var/lib/docker/containers -type f -name "*-json.log" \
      -printf '%s %p\n' 2>/dev/null | sort -nr | head -10 | \
      awk -v threshold="$THRESHOLD" '{
          size_mb = $1/1024/1024;
          if (size_mb > threshold) {
              printf "⚠️  %10.1f MB %s\n", size_mb, $2;
          } else {
              printf "✅ %10.1f MB %s\n", size_mb, $2;
          }
      }'
    
    # 전체 사용량 확인
    echo -e "\n💾 전체 Docker 사용량:"
    sudo du -sh /var/lib/docker/overlay2 2>/dev/null | head -1
    
    # 실행 중인 컨테이너 상태
    echo -e "\n🐳 실행 중인 컨테이너:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -10
    
    # 경고 메시지
    echo -e "\n🔔 경고:"
    sudo find /var/lib/docker/containers -type f -name "*-json.log" \
      -printf '%s %p\n' 2>/dev/null | awk -v threshold="$THRESHOLD" '
        $1/1024/1024 > threshold {
            printf "⚠️  %s: %.1f MB (임계값 %d MB 초과)\n", $2, $1/1024/1024, threshold;
        }
    ' | head -5
    
    # 30초 대기
    sleep 30
done
