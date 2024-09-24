# 개발 환경을 위한 Dockerfile
FROM node:18-alpine

WORKDIR /app

# 패키지 파일 복사 및 의존성 설치
COPY package.json package-lock.json ./
RUN npm ci

# 소스 코드 복사
COPY . .

# 개발 서버 실행
CMD ["npm", "run", "dev"]