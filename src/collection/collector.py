import logging
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from .binance_client import BinanceClient
from .twitter_client import TwitterClient
from .news_client import NewsClient
from ..database.mongodb import MongoDB

logger = logging.getLogger(__name__)

class DataCollector:
    """Coordinator for collecting data from various sources."""
    
    def __init__(self):
        """Initialize data collector."""
        self.binance_client = BinanceClient()
        self.twitter_client = TwitterClient()
        self.news_client = NewsClient()
        self.db = MongoDB.get_database()
    
    async def collect_market_data(self, quote_currency: str = 'USDT', limit: int = 500):
        """Collect market data for top trading pairs."""
        try:
            # Get top trading pairs
            pairs = await self.binance_client.get_top_pairs(
                quote_currency=quote_currency,
                limit=limit
            )
            
            # Store pairs in database
            for pair_data in pairs:
                await self.db.crypto_pairs.update_one(
                    {'pair_symbol': pair_data['pair_symbol']},
                    {'$set': pair_data},
                    upsert=True
                )
            
            logger.info(f"Collected market data for {len(pairs)} trading pairs")
            return pairs
            
        except Exception as e:
            logger.error(f"Error collecting market data: {str(e)}")
            raise
    
    async def collect_social_data(
        self,
        crypto_pairs: List[str],
        days_ago: int = 10
    ):
        """Collect social media data for crypto pairs."""
        try:
            # Collect tweets
            tweets = await self.twitter_client.search_crypto_tweets(
                crypto_pairs=crypto_pairs,
                days_ago=days_ago
            )
            
            # Store tweets in database
            for tweet_data in tweets:
                await self.db.tweets.update_one(
                    {'tweet_id': tweet_data['tweet_id']},
                    {'$set': tweet_data},
                    upsert=True
                )
            
            # Get trending topics
            trending = await self.twitter_client.get_trending_crypto_topics()
            
            logger.info(f"Collected {len(tweets)} tweets and {len(trending)} trending topics")
            return {
                'tweets': tweets,
                'trending_topics': trending
            }
            
        except Exception as e:
            logger.error(f"Error collecting social data: {str(e)}")
            raise
    
    async def collect_news_data(
        self,
        crypto_pairs: List[str],
        days_ago: int = 10
    ):
        """Collect news data for crypto pairs."""
        try:
            # Collect news articles
            articles = await self.news_client.get_crypto_news(
                crypto_pairs=crypto_pairs,
                days_ago=days_ago
            )
            
            # Store articles in database
            for article_data in articles:
                await self.db.news.update_one(
                    {
                        'url': article_data['url'],
                        'source': article_data['source']
                    },
                    {'$set': article_data},
                    upsert=True
                )
            
            # Get market news summary
            summary = await self.news_client.get_market_news_summary()
            
            logger.info(f"Collected {len(articles)} news articles")
            return {
                'articles': articles,
                'market_summary': summary
            }
            
        except Exception as e:
            logger.error(f"Error collecting news data: {str(e)}")
            raise
    
    async def collect_all_data(
        self,
        quote_currency: str = 'USDT',
        limit: int = 500,
        days_ago: int = 10
    ):
        """Collect all types of data."""
        try:
            # Collect market data first
            pairs = await self.collect_market_data(
                quote_currency=quote_currency,
                limit=limit
            )
            pair_symbols = [pair['pair_symbol'] for pair in pairs]
            
            # Collect social and news data concurrently
            social_task = asyncio.create_task(
                self.collect_social_data(
                    crypto_pairs=pair_symbols,
                    days_ago=days_ago
                )
            )
            
            news_task = asyncio.create_task(
                self.collect_news_data(
                    crypto_pairs=pair_symbols,
                    days_ago=days_ago
                )
            )
            
            # Wait for all tasks to complete
            social_data = await social_task
            news_data = await news_task
            
            return {
                'market_data': pairs,
                'social_data': social_data,
                'news_data': news_data,
                'collected_at': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error collecting all data: {str(e)}")
            raise
    
    async def close(self):
        """Close all client connections."""
        await asyncio.gather(
            self.binance_client.close(),
            self.twitter_client.close(),
            self.news_client.close()
        ) 