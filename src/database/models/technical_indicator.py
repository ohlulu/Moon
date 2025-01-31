from typing import Dict, Optional
from datetime import datetime
from pydantic import Field, BaseModel
from .base_model import BaseModel as MongoBaseModel

class RSIIndicator(BaseModel):
    value: float
    period: int = 14
    overbought: float = 70
    oversold: float = 30

class MACDIndicator(BaseModel):
    macd_line: float
    signal_line: float
    histogram: float
    fast_period: int = 12
    slow_period: int = 26
    signal_period: int = 9

class BollingerBands(BaseModel):
    upper: float
    middle: float
    lower: float
    period: int = 20
    standard_deviation: float = 2.0

class MovingAverages(BaseModel):
    simple_moving_average_20: Optional[float] = None
    simple_moving_average_50: Optional[float] = None
    simple_moving_average_200: Optional[float] = None
    exponential_moving_average_12: Optional[float] = None
    exponential_moving_average_26: Optional[float] = None

class TechnicalIndicator(MongoBaseModel):
    """Model for technical indicators of cryptocurrency pairs."""
    pair_symbol: str = Field(..., description="Trading pair symbol")
    timestamp: datetime = Field(..., description="Timestamp of the indicators")
    close_price: float = Field(..., description="Closing price at the timestamp")
    volume: float = Field(..., description="Trading volume at the timestamp")
    
    # Technical indicators
    rsi: Optional[RSIIndicator] = None
    macd: Optional[MACDIndicator] = None
    bollinger_bands: Optional[BollingerBands] = None
    moving_averages: Optional[MovingAverages] = None
    
    # Additional metrics
    volatility: Optional[float] = None
    momentum: Optional[float] = None
    trend_strength: Optional[float] = None
    
    # Custom indicators and signals
    custom_indicators: Dict = Field(default_factory=dict)
    trading_signals: Dict = Field(default_factory=dict)

    class Config:
        schema_extra = {
            "example": {
                "pair_symbol": "BTC/USDT",
                "timestamp": "2024-01-31T12:00:00Z",
                "close_price": 48000.0,
                "volume": 1000000.0,
                "rsi": {
                    "value": 65.5,
                    "period": 14,
                    "overbought": 70,
                    "oversold": 30
                },
                "macd": {
                    "macd_line": 100.5,
                    "signal_line": 90.2,
                    "histogram": 10.3,
                    "fast_period": 12,
                    "slow_period": 26,
                    "signal_period": 9
                },
                "bollinger_bands": {
                    "upper": 49000.0,
                    "middle": 48000.0,
                    "lower": 47000.0,
                    "period": 20,
                    "standard_deviation": 2.0
                },
                "moving_averages": {
                    "simple_moving_average_20": 47500.0,
                    "simple_moving_average_50": 46000.0,
                    "simple_moving_average_200": 45000.0,
                    "exponential_moving_average_12": 47800.0,
                    "exponential_moving_average_26": 47200.0
                },
                "volatility": 0.15,
                "momentum": 0.8,
                "trend_strength": 0.7,
                "custom_indicators": {
                    "fibonacci_levels": {
                        "0.236": 47000.0,
                        "0.382": 46500.0,
                        "0.618": 46000.0
                    }
                },
                "trading_signals": {
                    "rsi_signal": "NEUTRAL",
                    "macd_signal": "BUY",
                    "bb_signal": "SELL"
                }
            }
        } 