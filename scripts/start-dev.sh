#!/bin/bash

# Set environment variables if needed
export $(grep -v '^#' ../.env | xargs)

echo "백엔드 서비스를 시작합니다..."
cd ../app/backend/src/main

# Stop if backend is already running
if lsof -i :8000 >/dev/null 2>&1; then
  echo "포트번호 8000번이 이미 사용중이에요! sudo lsof -i :8000 명령어로 PID 번호 확인하시고 sudo kill -9 {포트번호} 명령어로 없애주세요ㅎㅎ"
  exit 1
fi

uvicorn main:app --reload --port 8000 &

sleep 5

echo "로그인 테스트를 위한 프론트엔드 서비스를 시작합니다..."
cd ../test/social-login-test || { echo "Frontend path not found. Exiting."; exit 1; }

# Ensure "start" script exists in package.json
if ! grep -q '"start"' package.json; then
  echo '"start" 스크립트가 package.json에 없어요! 만들고 다시 시작하기!'
  exit 1
fi

npm start &

echo "백엔드 서버와 프론트 서버를 시작합니다..."