import os
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure

logger = logging.getLogger(__name__)

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    database = None

    @classmethod
    async def connect(cls):
        """Connect to MongoDB."""
        try:
            mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
            database_name = os.getenv('MONGODB_DB_NAME', 'moon_crypto')
            
            cls.client = AsyncIOMotorClient(mongodb_uri)
            cls.database = cls.client[database_name]
            
            # Verify connection
            await cls.client.admin.command('ping')
            logger.info(f"Connected to MongoDB at {mongodb_uri}")
            
            # Create indexes
            await cls._create_indexes()
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    @classmethod
    async def close(cls):
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            cls.client = None
            cls.database = None
            logger.info("Closed MongoDB connection")

    @classmethod
    async def _create_indexes(cls):
        """Create necessary indexes for collections."""
        try:
            # crypto_pairs indexes
            await cls.database.crypto_pairs.create_index([("pair_symbol", 1)], unique=True)
            await cls.database.crypto_pairs.create_index([("market_cap", -1)])

            # news indexes
            await cls.database.news.create_index([("published_at", -1)])
            await cls.database.news.create_index([("related_pairs", 1)])
            await cls.database.news.create_index([("sentiment_score", -1)])

            # tweets indexes
            await cls.database.tweets.create_index([("created_at", -1)])
            await cls.database.tweets.create_index([("related_pairs", 1)])
            await cls.database.tweets.create_index([("sentiment_score", -1)])

            # technical_indicators indexes
            await cls.database.technical_indicators.create_index([
                ("pair_symbol", 1),
                ("timestamp", -1)
            ])

            # analysis_reports indexes
            await cls.database.analysis_reports.create_index([("timestamp", -1)])
            await cls.database.analysis_reports.create_index([
                ("type", 1),
                ("timestamp", -1)
            ])

            logger.info("Created all database indexes")

        except Exception as e:
            logger.error(f"Failed to create indexes: {str(e)}")
            raise

    @classmethod
    def get_database(cls):
        """Get database instance."""
        if not cls.database:
            raise ConnectionError("Database not connected. Call connect() first.")
        return cls.database 