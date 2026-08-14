from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import os

from src.pipeline import inspect_market, run_forecast
from src.config import settings
from src.skills import initialize_skill_index
from src.schemas import ForecastRequest, ForecastResponse, MarketContext

@asynccontextmanager
async def lifespan(server: FastAPI):

    print("loading embedding model")

    # Load embedding model and intialize skill index
    await initialize_skill_index(
            vector_storage_directory=settings.vector_index_storage, 
            embedding_model=settings.embedding_model, 
            embedding_model_path= settings.embedding_model_path
    )

    yield

    print("closing connection")

server = FastAPI(
    title="Polymarket Event Forecasting Most Viable Product",
    version="0.2.0",
    lifespan=lifespan
)

@server.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@server.post("/inspect", response_model=MarketContext)
async def inspect_endpoint(request: ForecastRequest) -> MarketContext:
    try:
        return await inspect_market(
            request.url,
            market_query=request.market_query,
            market_index=request.market_index,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@server.post("/forecast", response_model=ForecastResponse)
async def forecast_endpoint(request: ForecastRequest) -> ForecastResponse:
    # try:
        return await run_forecast(
            request.url,
            market_query=request.market_query,
            market_index=request.market_index,
        )
    # except Exception as exc:
    #     raise HTTPException(status_code=500, detail=str(exc)) from exc
