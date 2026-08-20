from fastapi import APIRouter

from app.api.v1.endpoints import chat, health, ingestion, sentiment, stocks

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(stocks.router)
api_router.include_router(sentiment.router)
api_router.include_router(chat.router)
api_router.include_router(ingestion.router)
