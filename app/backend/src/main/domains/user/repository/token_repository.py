from redis import Redis

class TokenRepository:
    def __init__(self, redis_client: Redis):
        self.redis_client = redis_client

    def store_refresh_token(self, user_id: str, token: str, expire_time: int):
        """Store a refresh token"""
        self.redis_client.setex(f"refresh_token: {user_id}", expire_time, token)

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