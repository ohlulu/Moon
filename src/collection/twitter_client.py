import os
import logging
import tweepy
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TwitterClient:
    """Client for interacting with Twitter API."""
    
    def __init__(self):
        """Initialize Twitter client."""
        self.application_key = os.getenv('TWITTER_API_KEY')
        self.application_secret = os.getenv('TWITTER_API_SECRET')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        
        # Initialize Tweepy client
        auth = tweepy.OAuthHandler(self.application_key, self.application_secret)
        auth.set_access_token(self.access_token, self.access_token_secret)
        self.api = tweepy.API(auth, wait_on_rate_limit=True)
        self.client = tweepy.Client(
            consumer_key=self.application_key,
            consumer_secret=self.application_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret
        )
    
    async def search_crypto_tweets(
        self,
        crypto_pairs: List[str],
        days_ago: int = 10,
        max_tweets: int = 100
    ) -> List[Dict]:
        """Search for tweets related to specific cryptocurrency pairs."""
        try:
            tweets = []
            start_time = datetime.utcnow() - timedelta(days=days_ago)
            
            for pair in crypto_pairs:
                # Create search query
                base_currency = pair.split('/')[0]
                query = f"#{base_currency} OR {base_currency} crypto -is:retweet lang:en"
                
                # Search tweets
                tweet_results = self.client.search_recent_tweets(
                    query=query,
                    start_time=start_time,
                    max_results=max_tweets,
                    tweet_fields=['created_at', 'public_metrics', 'entities', 'lang']
                )
                
                if not tweet_results.data:
                    continue
                
                for tweet in tweet_results.data:
                    tweet_data = {
                        'tweet_id': str(tweet.id),
                        'content': tweet.text,
                        'author': tweet.author_id,  # Need to fetch user details separately
                        'created_at': tweet.created_at,
                        'related_pairs': [pair],
                        'metrics': {
                            'likes': tweet.public_metrics['like_count'],
                            'retweets': tweet.public_metrics['retweet_count'],
                            'replies': tweet.public_metrics['reply_count']
                        },
                        'hashtags': [
                            tag['tag']
                            for tag in tweet.entities.get('hashtags', [])
                        ] if tweet.entities else [],
                        'mentions': [
                            mention['username']
                            for mention in tweet.entities.get('mentions', [])
                        ] if tweet.entities else [],
                        'urls': [
                            url['expanded_url']
                            for url in tweet.entities.get('urls', [])
                        ] if tweet.entities else [],
                        'language': tweet.lang
                    }
                    tweets.append(tweet_data)
            
            return tweets
            
        except Exception as e:
            logger.error(f"Error searching crypto tweets: {str(e)}")
            raise
    
    async def get_user_details(self, user_id: str) -> Optional[Dict]:
        """Get user details by user ID."""
        try:
            user = self.client.get_user(
                id=user_id,
                user_fields=['description', 'public_metrics', 'verified']
            )
            
            if not user.data:
                return None
            
            return {
                'id': str(user.data.id),
                'username': user.data.username,
                'name': user.data.name,
                'description': user.data.description,
                'followers_count': user.data.public_metrics['followers_count'],
                'verified': user.data.verified
            }
            
        except Exception as e:
            logger.error(f"Error fetching user details for {user_id}: {str(e)}")
            return None
    
    async def get_trending_crypto_topics(self) -> List[Dict]:
        """Get trending cryptocurrency-related topics."""
        try:
            # Get trending topics from major financial centers
            locations = ['1', '2459115', '23424977']  # World, New York, USA
            trending_topics = []
            
            for woeid in locations:
                trends = self.api.get_place_trends(woeid)
                if not trends:
                    continue
                
                # Filter crypto-related trends
                crypto_trends = [
                    trend for trend in trends[0]['trends']
                    if any(keyword in trend['name'].lower()
                          for keyword in ['crypto', 'bitcoin', 'btc', 'eth'])
                ]
                
                trending_topics.extend(crypto_trends)
            
            return trending_topics
            
        except Exception as e:
            logger.error(f"Error fetching trending topics: {str(e)}")
            raise
    
    async def close(self):
        """Close the client connection."""
        # No specific cleanup needed for Twitter client
        pass 