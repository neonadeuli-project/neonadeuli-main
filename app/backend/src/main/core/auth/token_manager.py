from src.main.db.database import redis_client

class RedisTokenManager:
    @staticmethod
    def store_refresh_token(user_id: str, token: str, expire_time: int):
        """Store a refresh token"""
        redis_client.setex(f"refresh_token: {user_id}", expire_time, token)

    @staticmethod
    def get_refresh_token(user_id: str) -> str:
        """Retrieve a refresh token"""
        return redis_client.get(f"refresh_token: {user_id}")
    
    @staticmethod
    def delete_refresh_token(user_id: str):
        """Delete a refresh token"""
        redis_client.delete(f"refresh_token: {user_id}")

    @staticmethod
    def is_token_blacklisted(token: str) -> bool:
        """Check if a token is blacklisted"""
        return redis_client.sismember("token_blacklisted", token)
    
    @staticmethod
    def blacklist_token(token: str):
        """Add a blacklisted token"""
        redis_client.sadd("token_blacklisted", token)