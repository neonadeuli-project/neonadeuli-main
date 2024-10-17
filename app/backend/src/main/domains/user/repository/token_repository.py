from asyncio.log import logger
from redis import Redis

class TokenRepository:
    def __init__(self, redis_client: Redis):
        self.redis_client = redis_client

    def store_refresh_token(self, user_id: str, token: str, expire_time: int):
        """refresh 토큰 저장"""
        key = f"user {user_id}:refresh_token"
        result = self.redis_client.setex(key, expire_time, token)

        if result:
            logger.info(f"유저 ID {user_id}가 성공적으로 refresh 토큰을 저장했습니다.")
        else:
            logger.error(f"유저 ID {user_id}가 refresh 토큰을 저장하는데 실패했습니다.")

    def get_refresh_token(self, user_id: str) -> str:
        """Retrieve a refresh token"""
        return self.redis_client.get(f"refresh_token: {user_id}")
    
    def delete_refresh_token(self, user_id: str):
        """Delete a refresh token"""
        self.redis_client.delete(f"refresh_token: {user_id}")

    def is_token_blacklisted(self, token: str) -> bool:
        """Check if a token is blacklisted"""
        return self.redis_client.sismember("token_blacklisted", token)
    
    def blacklist_token(self, token: str):
        """Add a blacklisted token"""
        self.redis_client.sadd("token_blacklisted", token)

    def store_oauth_state(self, state: str, provider: str, expire_seconds: int):
        self.redis_client.setex(f"oauth_state:{state}", expire_seconds, provider)

    def get_oauth_state(self, state: str) -> str:
        return self.redis_client.get(f"oauth_state:{state}")

    def delete_oauth_state(self, state: str):
        self.redis_client.delete(f"oauth_state:{state}")
            