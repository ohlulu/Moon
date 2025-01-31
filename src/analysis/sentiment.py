from typing import Dict, Any, List
import pandas as pd
from datetime import datetime
from .base import BaseAnalyzer

class SentimentAnalyzer(BaseAnalyzer):
    """Analyzer for market sentiment analysis."""
    
    def __init__(self, timeframe: str = '1d'):
        """Initialize sentiment analyzer."""
        super().__init__(timeframe)
        self._sentiment_threshold = 0.3  # Threshold for significant sentiment
    
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform sentiment analysis."""
        try:
            news_data = data.get('news_data', {})
            social_data = data.get('social_data', {})
            
            # Analyze news sentiment
            news_sentiment = self._analyze_news_sentiment(news_data)
            
            # Analyze social sentiment
            social_sentiment = self._analyze_social_sentiment(social_data)
            
            # Analyze overall market sentiment
            overall_sentiment = self._calculate_overall_sentiment(
                news_sentiment,
                social_sentiment
            )
            
            # Generate summary
            summary = self._generate_summary(
                news_sentiment,
                social_sentiment,
                overall_sentiment
            )
            
            return {
                'timestamp': datetime.utcnow(),
                'timeframe': self.timeframe,
                'news_sentiment': news_sentiment,
                'social_sentiment': social_sentiment,
                'overall_sentiment': overall_sentiment,
                'summary': summary
            }
            
        except Exception as e:
            raise ValueError(f"Error in sentiment analysis: {str(e)}")
    
    def _analyze_news_sentiment(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment from news data."""
        articles = news_data.get('articles', [])
        if not articles:
            return {
                'score': 0,
                'direction': 'NEUTRAL',
                'confidence': 0,
                'sources': 0,
                'keywords': []
            }
        
        # Calculate average sentiment
        sentiments = [
            article.get('sentiment_score', 0)
            for article in articles
            if article.get('sentiment_score') is not None
        ]
        
        if not sentiments:
            return {
                'score': 0,
                'direction': 'NEUTRAL',
                'confidence': 0,
                'sources': len(articles),
                'keywords': []
            }
        
        avg_sentiment = sum(sentiments) / len(sentiments)
        
        # Extract common keywords
        keywords = {}
        for article in articles:
            for keyword in article.get('keywords', []):
                keywords[keyword] = keywords.get(keyword, 0) + 1
        
        top_keywords = sorted(
            keywords.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Calculate confidence based on source diversity and sentiment consistency
        unique_sources = len({
            article['source'] for article in articles
            if 'source' in article
        })
        sentiment_std = pd.Series(sentiments).std()
        confidence = (unique_sources / max(10, len(articles))) * (1 - sentiment_std)
        
        return {
            'score': avg_sentiment,
            'direction': self._get_sentiment_direction(avg_sentiment),
            'confidence': confidence,
            'sources': unique_sources,
            'keywords': [k for k, _ in top_keywords]
        }
    
    def _analyze_social_sentiment(self, social_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment from social media data."""
        tweets = social_data.get('tweets', [])
        if not tweets:
            return {
                'score': 0,
                'direction': 'NEUTRAL',
                'confidence': 0,
                'engagement': 0,
                'trending_topics': []
            }
        
        # Calculate weighted sentiment based on engagement
        weighted_sentiments = []
        total_engagement = 0
        
        for tweet in tweets:
            sentiment = tweet.get('sentiment_score', 0)
            if sentiment is None:
                continue
                
            metrics = tweet.get('metrics', {})
            engagement = (
                metrics.get('likes', 0) +
                metrics.get('retweets', 0) * 2 +
                metrics.get('replies', 0) * 3
            )
            
            weighted_sentiments.append(sentiment * engagement)
            total_engagement += engagement
        
        if not weighted_sentiments or total_engagement == 0:
            return {
                'score': 0,
                'direction': 'NEUTRAL',
                'confidence': 0,
                'engagement': total_engagement,
                'trending_topics': []
            }
        
        avg_sentiment = sum(weighted_sentiments) / total_engagement
        
        # Extract trending topics
        trending = social_data.get('trending_topics', [])
        
        # Calculate confidence based on engagement and tweet volume
        confidence = min(1.0, len(tweets) / 1000) * min(1.0, total_engagement / 10000)
        
        return {
            'score': avg_sentiment,
            'direction': self._get_sentiment_direction(avg_sentiment),
            'confidence': confidence,
            'engagement': total_engagement,
            'trending_topics': trending[:5]
        }
    
    def _calculate_overall_sentiment(
        self,
        news_sentiment: Dict[str, Any],
        social_sentiment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate overall market sentiment."""
        # Weight sentiments by their confidence
        news_weight = news_sentiment['confidence']
        social_weight = social_sentiment['confidence']
        total_weight = news_weight + social_weight
        
        if total_weight == 0:
            return {
                'score': 0,
                'direction': 'NEUTRAL',
                'confidence': 0,
                'components': {
                    'news': 0,
                    'social': 0
                }
            }
        
        # Calculate weighted average sentiment
        overall_score = (
            news_sentiment['score'] * news_weight +
            social_sentiment['score'] * social_weight
        ) / total_weight
        
        # Calculate overall confidence
        confidence = (news_weight + social_weight) / 2
        
        return {
            'score': overall_score,
            'direction': self._get_sentiment_direction(overall_score),
            'confidence': confidence,
            'components': {
                'news': news_weight / total_weight,
                'social': social_weight / total_weight
            }
        }
    
    def _get_sentiment_direction(self, score: float) -> str:
        """Convert sentiment score to direction."""
        if score > self._sentiment_threshold:
            return 'BULLISH'
        elif score < -self._sentiment_threshold:
            return 'BEARISH'
        return 'NEUTRAL'
    
    def _generate_summary(
        self,
        news_sentiment: Dict[str, Any],
        social_sentiment: Dict[str, Any],
        overall_sentiment: Dict[str, Any]
    ) -> str:
        """Generate analysis summary."""
        summary = []
        
        # Overall sentiment summary
        if overall_sentiment['direction'] != 'NEUTRAL':
            summary.append(
                f"Overall market sentiment is {overall_sentiment['direction'].lower()} "
                f"with {overall_sentiment['confidence']:.1%} confidence"
            )
        else:
            summary.append("Market sentiment is neutral")
        
        # News sentiment summary
        if news_sentiment['direction'] != 'NEUTRAL':
            summary.append(
                f"News sentiment is {news_sentiment['direction'].lower()} "
                f"based on {news_sentiment['sources']} sources"
            )
        
        # Social sentiment summary
        if social_sentiment['direction'] != 'NEUTRAL':
            summary.append(
                f"Social sentiment is {social_sentiment['direction'].lower()} "
                f"with {social_sentiment['engagement']:,} engagements"
            )
        
        # Add trending topics if available
        if social_sentiment['trending_topics']:
            topics = ', '.join(social_sentiment['trending_topics'][:3])
            summary.append(f"Trending topics: {topics}")
        
        return " | ".join(summary)
    
    def get_analysis_requirements(self) -> List[str]:
        """Get required data for analysis."""
        return ['news_data', 'social_data']
    
    @property
    def description(self) -> str:
        """Get analyzer description."""
        return (
            "Sentiment analyzer that evaluates market sentiment using news and "
            "social media data, considering source credibility, engagement levels, "
            "and sentiment consistency."
        ) 