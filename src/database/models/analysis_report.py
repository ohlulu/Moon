from typing import List, Dict, Optional
from datetime import datetime
from pydantic import Field, BaseModel
from .base_model import BaseModel as MongoBaseModel

class PairAnalysis(BaseModel):
    """Analysis details for a single trading pair."""
    pair_symbol: str
    current_price: float
    price_change_24h: float
    volume_change_24h: float
    technical_signals: Dict[str, str]  # e.g., {"rsi": "BUY", "macd": "SELL"}
    sentiment_analysis: Dict[str, float]  # e.g., {"news": 0.8, "social": 0.6}
    risk_score: float  # 0 to 100
    opportunity_score: float  # 0 to 100
    recommendation: str  # "BUY", "SELL", "HOLD"
    supporting_data: Dict  # Additional analysis data

class RiskAssessment(BaseModel):
    """Overall risk assessment for the analyzed pairs."""
    market_volatility: float  # 0 to 100
    market_sentiment: float  # -1 to 1
    global_risk_level: str  # "LOW", "MEDIUM", "HIGH"
    risk_factors: List[str]
    market_correlation: Dict[str, float]  # Correlation between pairs

class AnalysisReport(MongoBaseModel):
    """Model for cryptocurrency analysis reports."""
    report_id: str = Field(..., description="Unique report identifier")
    timestamp: datetime = Field(..., description="Report generation timestamp")
    type: str = Field(..., description="Report type (daily, weekly, monthly)")
    
    # Market Overview
    market_summary: Dict = Field(
        ...,
        description="Overall market summary including trends and key metrics"
    )
    
    # Detailed Analysis
    pairs_analysis: List[PairAnalysis] = Field(
        ...,
        description="Detailed analysis for each trading pair"
    )
    
    # Risk Assessment
    risk_assessment: RiskAssessment = Field(
        ...,
        description="Overall risk assessment and market conditions"
    )
    
    # Recommendations
    top_opportunities: List[Dict] = Field(
        default_factory=list,
        description="Top investment opportunities identified"
    )
    
    # News and Social Media Impact
    news_summary: Optional[Dict] = Field(
        None,
        description="Summary of important news affecting the market"
    )
    social_trends: Optional[Dict] = Field(
        None,
        description="Summary of social media trends and sentiment"
    )
    
    # Additional Information
    notes: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    data_sources: List[str] = Field(default_factory=list)

    class Config:
        schema_extra = {
            "example": {
                "report_id": "DAILY_20240131",
                "timestamp": "2024-01-31T12:00:00Z",
                "type": "daily",
                "market_summary": {
                    "total_market_cap": 2100000000000,
                    "total_volume_24h": 100000000000,
                    "btc_dominance": 45.5,
                    "market_trend": "BULLISH"
                },
                "pairs_analysis": [
                    {
                        "pair_symbol": "BTC/USDT",
                        "current_price": 48000.0,
                        "price_change_24h": 2.5,
                        "volume_change_24h": 15.0,
                        "technical_signals": {
                            "rsi": "BUY",
                            "macd": "BUY",
                            "ma": "NEUTRAL"
                        },
                        "sentiment_analysis": {
                            "news": 0.8,
                            "social": 0.7
                        },
                        "risk_score": 65.0,
                        "opportunity_score": 75.0,
                        "recommendation": "BUY",
                        "supporting_data": {
                            "key_resistance": 50000.0,
                            "key_support": 45000.0
                        }
                    }
                ],
                "risk_assessment": {
                    "market_volatility": 45.0,
                    "market_sentiment": 0.6,
                    "global_risk_level": "MEDIUM",
                    "risk_factors": [
                        "High leverage in futures market",
                        "Regulatory uncertainty"
                    ],
                    "market_correlation": {
                        "BTC/ETH": 0.85,
                        "BTC/ALTs": 0.72
                    }
                },
                "top_opportunities": [
                    {
                        "pair": "BTC/USDT",
                        "type": "LONG",
                        "confidence": 0.85
                    }
                ],
                "news_summary": {
                    "major_events": [
                        "ETF approval news",
                        "Major partnership announcements"
                    ],
                    "sentiment": "POSITIVE"
                },
                "social_trends": {
                    "trending_topics": ["Bitcoin ETF", "DeFi"],
                    "overall_sentiment": "BULLISH"
                },
                "notes": "Strong institutional buying pressure observed",
                "warnings": [
                    "High volatility expected due to upcoming economic data"
                ],
                "data_sources": [
                    "Binance",
                    "Twitter",
                    "CryptoNews"
                ]
            }
        } 