from typing import Optional, Dict
from datetime import datetime
from pydantic import Field
from .base_model import BaseModel

class CryptoPair(BaseModel):
    """Model for cryptocurrency trading pairs."""
    pair_symbol: str = Field(..., description="Trading pair symbol (e.g., 'BTC/USDT')")
    market_type: str = Field(..., description="Market type ('spot' or 'futures')")
    market_cap: float = Field(..., description="Market capitalization in USD")
    volume_24h: float = Field(..., description="24-hour trading volume in USD")
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict] = Field(default_factory=dict, description="Additional metadata about the trading pair")

    class Config:
        schema_extra = {
            "example": {
                "pair_symbol": "BTC/USDT",
                "market_type": "spot",
                "market_cap": 800000000000.0,
                "volume_24h": 25000000000.0,
                "last_updated": "2024-01-31T12:00:00Z",
                "metadata": {
                    "base_currency": "BTC",
                    "quote_currency": "USDT",
                    "price_precision": 2,
                    "min_order_size": 0.0001
                }
            }
        } 