#!/bin/bash

# 프론트엔드 개발 서버 시작
echo "Starting frontend development server..."
cd frontend && npm run dev &

# 백엔드 개발 서버 시작
echo "Starting backend development server..."
cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000 &

# 모든 백그라운드 프로세스가 완료될 때까지 대기
wait