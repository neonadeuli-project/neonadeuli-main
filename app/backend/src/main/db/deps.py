from src.main.db.database import AsyncSessionLocal

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
        await session.commit()
        # with을 사용하면 알아서 session을 닫아줌
        # await session.close()