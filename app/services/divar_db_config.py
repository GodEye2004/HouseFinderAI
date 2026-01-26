# from fastapi import FastAPI, HTTPException, Depends
# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.future import select
# from typing import List

# from models import DivarProperty  # your SQLAlchemy model
# from schemas import DivarPropertyResponse  # the Pydantic model

# DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/your_db"

# engine = create_async_engine(DATABASE_URL, echo=True)
# async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# app = FastAPI()

# async def get_session() -> AsyncSession:
#     async with async_session() as session:
#         yield session
