from asyncio.log import logger
import secrets
import aioredis
from redis import Redis
import redis

class TokenRepository:
    def __init__(self, redis_client: aioredis.Redis):
        self.redis_client = redis_client

    async def store_refresh_token(self, user_id: str, token: str, expire_time: int):
        """refresh 토큰 저장"""
        key = f"user:{user_id}:refresh_token"
        result = await self.redis_client.setex(key, expire_time, token)
        if result:
            logger.info(f"유저 ID {user_id}가 성공적으로 refresh 토큰을 저장했습니다.")
        else:
            logger.error(f"유저 ID {user_id}가 refresh 토큰을 저장하는데 실패했습니다.")

    async def get_refresh_token(self, user_id: str) -> str:
        """refresh 토큰 조회"""
        key = f"user:{user_id}:refresh_token"
        return await self.redis_client.get(key)
    
    async def delete_refresh_token(self, user_id: str):
        """refresh 토큰 삭제"""
        try:
            await self.redis_client.delete(f"user:{user_id}:refresh_token")
            logger.info(f"Refresh token deleted for user: {user_id}")
        except Exception as e:
            logger.error(f"Error deleting refresh token: {str(e)}", exc_info=True)
            raise

    async def is_token_blacklisted(self, token: str) -> bool:
        """Check if a token is blacklisted"""
        try:
            result = await self.redis_client.sismember("token_blacklist", token)
            logger.info(f"Token blacklist check result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error checking token blacklist: {str(e)}")
            return False  # 오류 발생 시 기본적으로 토큰이 유효하다고 가정
    
    async def blacklist_token(self, token: str):
        """Add a blacklisted token"""
        try:
            await self.redis_client.sadd("token_blacklist", token)
            logger.info(f"Token blacklisted: {token[:10]}...")
        except Exception as e:
            logger.error(f"Error blacklisting token: {str(e)}", exc_info=True)
            raise

    async def store_oauth_state(self, provider: str) -> str:
        try:
            state = secrets.token_urlsafe(32)
            await self.redis_client.setex(f"oauth_state:{state}", 300, provider)
            logger.error(f"{provider} 상태 값 저장 완료.")
            return state
        except redis.RedisError as e:
            logger.error(f"store_oauth_state 메서드에서 Redis 에러 발생: {str(e)}")
            raise

    async def verify_oauth_state(self, state: str, provider: str) -> bool:
        stored_provider = await self.redis_client.get(f"oauth_state:{state}")
        return stored_provider == provider
    
    async def get_oauth_state(self, state: str) -> str:
        return await self.redis_client.get(f"oauth_state:{state}")

    async def delete_oauth_state(self, state: str):
        await self.redis_client.delete(f"oauth_state:{state}")
            