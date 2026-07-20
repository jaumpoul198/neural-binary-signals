from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import pandas as pd
import numpy as np
import logging
import uvicorn
import time

from ..core import DecisionEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Neural Binary Signals API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = DecisionEngine()

class SignalRequest(BaseModel):
    symbol: str = "EURUSD"
    timeframe: str = "M5"
    is_otc: bool = False

class SignalResponse(BaseModel):
    symbol: str
    signal_type: str
    confidence: float
    strength: str
    timestamp: datetime
    timeframe: str
    reasons: List[str]
    metadata: Dict[str, Any]

def generate_synthetic_data(n=100, trend=0.1):
    """Gera dados sintéticos para teste"""
    np.random.seed(int(time.time()) % 1000)
    prices = 100 + np.cumsum(np.random.randn(n) * 0.5 + trend)
    prices = np.maximum(prices, 50)
    
    return pd.DataFrame({
        'open': prices[:-1],
        'high': prices[:-1] + np.abs(np.random.randn(n-1) * 0.3),
        'low': prices[:-1] - np.abs(np.random.randn(n-1) * 0.3),
        'close': prices[1:],
        'volume': np.random.randint(1000, 5000, n-1)
    })

@app.get("/")
async def root():
    return {"message": "Neural Binary Signals API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "online", "timestamp": datetime.now()}

@app.post("/signal", response_model=SignalResponse)
async def generate_signal(request: SignalRequest):
    try:
        logger.info(f"Gerando sinal para {request.symbol}")
        
        # SEMPRE usa dados sintéticos
        data = generate_synthetic_data(100)
        logger.info(f"Usando dados sintéticos para {request.symbol}")
        
        signal = engine.analyze(data, symbol=request.symbol, timeframe=request.timeframe, is_otc=request.is_otc)
        
        if not signal:
            raise HTTPException(400, "Não foi possível gerar sinal")
        
        return SignalResponse(
            symbol=signal.symbol,
            signal_type=signal.signal_type.value,
            confidence=signal.confidence,
            strength=signal.strength.value,
            timestamp=signal.timestamp,
            timeframe=signal.timeframe,
            reasons=signal.reasons,
            metadata=signal.metadata
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro: {e}")
        raise HTTPException(500, str(e))

@app.get("/signal/{symbol}")
async def generate_signal_get(
    symbol: str,
    timeframe: str = Query("M5"),
    is_otc: bool = Query(False)
):
    request = SignalRequest(symbol=symbol, timeframe=timeframe, is_otc=is_otc)
    return await generate_signal(request)

@app.get("/symbols")
async def get_symbols():
    return {
        "forex": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"],
        "crypto": ["BTC", "ETH", "SOL"],
        "indices": ["SP500", "DJI", "IXIC"]
    }

if __name__ == "__main__":
    uvicorn.run("src.api.rest_api:app", host="0.0.0.0", port=8000, reload=True)