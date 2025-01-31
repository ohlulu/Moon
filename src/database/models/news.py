from typing import List, Optional
from datetime import datetime
from pydantic import Field
from .base_model import BaseModel

class News(BaseModel):
    """Model for cryptocurrency news articles."""
    title: str = Field(..., description="News article title")
    content: str = Field(..., description="News article content")
    source: str = Field(..., description="News source name")
    published_at: datetime = Field(..., description="Article publication date")
    related_pairs: List[str] = Field(default_factory=list, description="Related cryptocurrency pairs")
    sentiment_score: Optional[float] = Field(None, description="Sentiment analysis score (-1 to 1)")
    url: str = Field(..., description="URL of the news article")
    author: Optional[str] = Field(None, description="Article author")
    summary: Optional[str] = Field(None, description="Article summary")
    keywords: List[str] = Field(default_factory=list, description="Keywords extracted from the article")

    class Config:
        schema_extra = {
            "example": {
                "title": "Bitcoin Surges Past $50,000 as Institutional Interest Grows",
                "content": "Bitcoin has surpassed the $50,000 mark for the first time since...",
                "source": "CryptoNews",
                "published_at": "2024-01-31T12:00:00Z",
                "related_pairs": ["BTC/USDT", "BTC/USD"],
                "sentiment_score": 0.8,
                "url": "https://cryptonews.com/bitcoin-surge",
                "author": "John Doe",
                "summary": "Bitcoin reaches new milestone as institutional investors increase their holdings",
                "keywords": ["Bitcoin", "institutional investors", "cryptocurrency", "market"]
            }
        } 