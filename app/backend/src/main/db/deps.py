from src.main.db.database import AsyncSessionLocal

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
        # with을 사용하면 알아서 session을 닫아줌
        # await session.close()