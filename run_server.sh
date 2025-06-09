#!/bin/bash

# 서버 실행 스크립트
# 이 스크립트는 FastAPI 서버를 실행합니다.

echo "===== 서버 실행 스크립트 ====="

# 현재 디렉토리 확인
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"
echo "작업 디렉토리: $(pwd)"

# 서버 실행
echo "FastAPI 서버를 실행합니다..."
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# 이 스크립트는 서버가 종료될 때까지 실행됩니다.
# Ctrl+C를 눌러 서버를 종료할 수 있습니다.
