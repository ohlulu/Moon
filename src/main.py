import os
import logging
from dotenv import load_dotenv
from pathlib import Path
from database.mongodb import MongoDB
from collection.collector import DataCollector
from indicators.manager import IndicatorManager
from utils.logging import setup_logging

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logging(__name__)

# Global instances
collector: DataCollector = None
indicator_manager: IndicatorManager = None

async def initialize():
    """Initialize required services."""
    global collector, indicator_manager
    
    logger.info("Starting Moon Crypto application...")
    
    try:
        # Initialize database connection
        await MongoDB.connect()
        logger.info("Database connection established")
        
        # Initialize data collector
        collector = DataCollector()
        logger.info("Data collector initialized")
        
        # Initialize indicator manager
        indicator_manager = IndicatorManager()
        logger.info("Indicator manager initialized")
        
    except Exception as e:
        logger.error(f"Initialization failed: {str(e)}")
        raise

async def cleanup():
    """Cleanup resources."""
    global collector
    
    logger.info("Cleaning up Moon Crypto application...")
    
    try:
        # Close collector connections
        if collector:
            await collector.close()
        
        # Close database connection
        await MongoDB.close()
        
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")

async def collect_and_analyze_data():
    """Collect market data and calculate indicators."""
    global collector, indicator_manager
    
    try:
        logger.info("Starting data collection and analysis...")
        
        # Collect market data
        data = await collector.collect_all_data()
        pairs = data['market_data']
        
        # Calculate indicators for each pair
        for pair in pairs:
            # Get historical data
            historical_data = await collector.binance_client.get_historical_data(
                pair['pair_symbol']
            )
            
            # Calculate and store indicators
            await indicator_manager.calculate_indicators(
                pair['pair_symbol'],
                historical_data
            )
            
            # Analyze trend
            trend_analysis = await indicator_manager.analyze_trend(
                pair['pair_symbol']
            )
            logger.info(
                f"Analysis for {pair['pair_symbol']}: "
                f"Trend={trend_analysis['trend']}, "
                f"Strength={trend_analysis['strength']:.2f}, "
                f"Confidence={trend_analysis['confidence']:.2f}"
            )
        
        logger.info("Data collection and analysis completed")
        
    except Exception as e:
        logger.error(f"Data collection and analysis error: {str(e)}")

async def main():
    """Main execution function."""
    try:
        await initialize()
        await collect_and_analyze_data()
    finally:
        await cleanup()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 