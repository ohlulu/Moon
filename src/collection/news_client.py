import os
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from newsapi import NewsApiClient

logger = logging.getLogger(__name__)

class NewsClient:
    """Client for interacting with News API."""
    
    def __init__(self):
        """Initialize News API client."""
        self.api_key = os.getenv('NEWS_API_KEY')
        self.client = NewsApiClient(api_key=self.api_key)
        
        # Define crypto-related keywords
        self.crypto_keywords = [
            'cryptocurrency', 'crypto', 'bitcoin', 'ethereum',
            'blockchain', 'digital currency', 'crypto market',
            'crypto trading', 'defi', 'nft'
        ]
    
    async def get_crypto_news(
        self,
        crypto_pairs: List[str],
        days_ago: int = 10,
        language: str = 'en',
        sort_by: str = 'publishedAt'
    ) -> List[Dict]:
        """Get cryptocurrency-related news articles."""
        try:
            news_articles = []
            from_date = datetime.utcnow() - timedelta(days=days_ago)
            
            # Get news for each crypto pair
            for pair in crypto_pairs:
                base_currency = pair.split('/')[0]
                
                # Create search query
                query = f"{base_currency} AND ({' OR '.join(self.crypto_keywords)})"
                
                # Search news
                articles = self.client.get_everything(
                    q=query,
                    from_param=from_date.strftime('%Y-%m-%d'),
                    language=language,
                    sort_by=sort_by
                )
                
                if not articles['articles']:
                    continue
                
                # Process articles
                for article in articles['articles']:
                    if not self._is_relevant_article(article, base_currency):
                        continue
                        
                    article_data = {
                        'title': article['title'],
                        'content': article['content'],
                        'source': article['source']['name'],
                        'published_at': datetime.strptime(
                            article['publishedAt'],
                            '%Y-%m-%dT%H:%M:%SZ'
                        ),
                        'related_pairs': [pair],
                        'url': article['url'],
                        'author': article.get('author'),
                        'summary': article['description'],
                        'keywords': self._extract_keywords(article)
                    }
                    news_articles.append(article_data)
            
            return news_articles
            
        except Exception as e:
            logger.error(f"Error fetching crypto news: {str(e)}")
            raise
    
    def _is_relevant_article(self, article: Dict, currency: str) -> bool:
        """Check if the article is relevant to the cryptocurrency."""
        if not article['title'] or not article['content']:
            return False
            
        text = f"{article['title']} {article['content']}".lower()
        currency = currency.lower()
        
        # Check if the currency is mentioned and at least one crypto keyword
        has_currency = currency in text
        has_crypto_keyword = any(keyword.lower() in text
                               for keyword in self.crypto_keywords)
        
        return has_currency and has_crypto_keyword
    
    def _extract_keywords(self, article: Dict) -> List[str]:
        """Extract relevant keywords from the article."""
        keywords = set()
        text = f"{article['title']} {article['description']}".lower()
        
        # Add cryptocurrency names if found
        for currency in ['bitcoin', 'ethereum', 'bnb', 'xrp', 'cardano',
                        'solana', 'dogecoin', 'polkadot']:
            if currency in text:
                keywords.add(currency.upper())
        
        # Add crypto-related keywords if found
        for keyword in self.crypto_keywords:
            if keyword.lower() in text:
                keywords.add(keyword.title())
        
        # Add market sentiment keywords
        sentiment_keywords = {
            'bullish': ['bullish', 'surge', 'rally', 'gain', 'rise'],
            'bearish': ['bearish', 'crash', 'drop', 'fall', 'decline']
        }
        
        for sentiment, words in sentiment_keywords.items():
            if any(word in text for word in words):
                keywords.add(sentiment.upper())
        
        return sorted(list(keywords))
    
    async def get_market_news_summary(self) -> Dict:
        """Get a summary of overall crypto market news."""
        try:
            # Get general crypto market news
            articles = self.client.get_everything(
                q='cryptocurrency OR "crypto market"',
                language='en',
                sort_by='relevancy',
                page_size=10
            )
            
            if not articles['articles']:
                return {
                    'major_events': [],
                    'sources': [],
                    'trending_topics': []
                }
            
            # Process articles to extract major events and topics
            major_events = []
            sources = set()
            topics = set()
            
            for article in articles['articles']:
                if article['title'] and article['source']['name']:
                    major_events.append({
                        'title': article['title'],
                        'source': article['source']['name'],
                        'url': article['url'],
                        'published_at': article['publishedAt']
                    })
                    sources.add(article['source']['name'])
                    topics.update(self._extract_keywords(article))
            
            return {
                'major_events': major_events[:5],  # Top 5 major events
                'sources': sorted(list(sources)),
                'trending_topics': sorted(list(topics))
            }
            
        except Exception as e:
            logger.error(f"Error fetching market news summary: {str(e)}")
            raise
    
    async def close(self):
        """Close the client connection."""
        # No specific cleanup needed for News API client
        pass 