from typing import List, Optional, Dict
from datetime import datetime
from pydantic import Field
from .base_model import BaseModel

class Tweet(BaseModel):
    """Model for cryptocurrency-related tweets."""
    tweet_id: str = Field(..., description="Twitter's unique tweet ID")
    content: str = Field(..., description="Tweet content")
    author: str = Field(..., description="Tweet author's username")
    created_at: datetime = Field(..., description="Tweet creation timestamp")
    related_pairs: List[str] = Field(default_factory=list, description="Related cryptocurrency pairs")
    sentiment_score: Optional[float] = Field(None, description="Sentiment analysis score (-1 to 1)")
    metrics: Dict = Field(
        default_factory=lambda: {"likes": 0, "retweets": 0, "replies": 0},
        description="Tweet engagement metrics"
    )
    hashtags: List[str] = Field(default_factory=list, description="Hashtags used in the tweet")
    mentions: List[str] = Field(default_factory=list, description="Users mentioned in the tweet")
    urls: List[str] = Field(default_factory=list, description="URLs included in the tweet")
    is_retweet: bool = Field(False, description="Whether the tweet is a retweet")
    language: str = Field("en", description="Tweet language code")

    class Config:
        schema_extra = {
            "example": {
                "tweet_id": "1234567890",
                "content": "Bitcoin looking bullish! 🚀 #BTC #crypto",
                "author": "crypto_trader",
                "created_at": "2024-01-31T12:00:00Z",
                "related_pairs": ["BTC/USDT"],
                "sentiment_score": 0.9,
                "metrics": {
                    "likes": 100,
                    "retweets": 50,
                    "replies": 10
                },
                "hashtags": ["BTC", "crypto"],
                "mentions": ["@trader"],
                "urls": ["https://example.com"],
                "is_retweet": False,
                "language": "en"
            }
        } 