import logging
import pandas as pd
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from ..database.mongodb import MongoDB
from .registry import registry

logger = logging.getLogger(__name__)

class IndicatorManager:
    """Manager for calculating and storing technical indicators."""
    
    def __init__(self, active_indicators: Optional[List[str]] = None):
        """
        Initialize indicator manager.
        
        Args:
            active_indicators: List of indicator names to use. If None, use all registered indicators.
        """
        self.db = MongoDB.get_database()
        self.active_indicators = (
            active_indicators if active_indicators is not None
            else registry.list_indicators()
        )
    
    def add_indicator(self, name: str):
        """Add an indicator to active indicators."""
        if name not in registry.list_indicators():
            raise ValueError(f"Unknown indicator: {name}")
        if name not in self.active_indicators:
            self.active_indicators.append(name)
    
    def remove_indicator(self, name: str):
        """Remove an indicator from active indicators."""
        if name in self.active_indicators:
            self.active_indicators.remove(name)
    
    async def calculate_indicators(
        self,
        pair_symbol: str,
        historical_data: List[Dict]
    ) -> Dict[str, Any]:
        """Calculate technical indicators for a trading pair."""
        try:
            # Convert historical data to DataFrame
            df = pd.DataFrame(historical_data)
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            # Calculate indicators
            results = {}
            signals = {}
            
            for indicator_name in self.active_indicators:
                # Get indicator class and create instance
                indicator_class = registry.get_indicator(indicator_name)
                indicator = indicator_class(df)
                
                # Calculate values and signal
                values = indicator.calculate()
                signal = indicator.generate_signal()
                
                results[indicator_name.lower()] = values
                signals[indicator_name.lower()] = signal
            
            # Prepare indicator document
            indicator_doc = {
                'pair_symbol': pair_symbol,
                'timestamp': df.index[-1],
                'close_price': df['close'].iloc[-1],
                'volume': df['volume'].iloc[-1],
                'indicators': results,
                'signals': signals,
                'active_indicators': self.active_indicators
            }
            
            # Store in database
            await self.store_indicators(indicator_doc)
            
            return indicator_doc
            
        except Exception as e:
            logger.error(f"Error calculating indicators for {pair_symbol}: {str(e)}")
            raise
    
    async def store_indicators(self, indicator_data: Dict):
        """Store technical indicators in database."""
        try:
            await self.db.technical_indicators.update_one(
                {
                    'pair_symbol': indicator_data['pair_symbol'],
                    'timestamp': indicator_data['timestamp']
                },
                {'$set': indicator_data},
                upsert=True
            )
            
            logger.info(f"Stored indicators for {indicator_data['pair_symbol']}")
            
        except Exception as e:
            logger.error(f"Error storing indicators: {str(e)}")
            raise
    
    async def get_latest_indicators(
        self,
        pair_symbol: str
    ) -> Optional[Dict]:
        """Get latest technical indicators for a trading pair."""
        try:
            indicator = await self.db.technical_indicators.find_one(
                {'pair_symbol': pair_symbol},
                sort=[('timestamp', -1)]
            )
            return indicator
            
        except Exception as e:
            logger.error(f"Error fetching latest indicators for {pair_symbol}: {str(e)}")
            raise
    
    async def get_historical_indicators(
        self,
        pair_symbol: str,
        start_time: datetime,
        end_time: Optional[datetime] = None
    ) -> List[Dict]:
        """Get historical technical indicators for a trading pair."""
        try:
            query = {
                'pair_symbol': pair_symbol,
                'timestamp': {'$gte': start_time}
            }
            
            if end_time:
                query['timestamp']['$lte'] = end_time
            
            indicators = await self.db.technical_indicators.find(
                query,
                sort=[('timestamp', 1)]
            ).to_list(length=None)
            
            return indicators
            
        except Exception as e:
            logger.error(
                f"Error fetching historical indicators for {pair_symbol}: {str(e)}"
            )
            raise
    
    async def analyze_trend(
        self,
        pair_symbol: str,
        timeframe: str = '1d'
    ) -> Dict:
        """Analyze trend for a trading pair."""
        try:
            # Get recent indicators
            end_time = datetime.utcnow()
            if timeframe == '1d':
                start_time = end_time - timedelta(days=30)
            elif timeframe == '1h':
                start_time = end_time - timedelta(days=7)
            else:
                start_time = end_time - timedelta(days=90)
            
            indicators = await self.get_historical_indicators(
                pair_symbol,
                start_time,
                end_time
            )
            
            if not indicators:
                return {
                    'trend': 'UNKNOWN',
                    'strength': 0,
                    'confidence': 0
                }
            
            # Analyze signals from all active indicators
            latest = indicators[-1]
            signals = latest['signals']
            
            # Count buy/sell signals
            buy_count = sum(1 for signal in signals.values() if signal == 'BUY')
            sell_count = sum(1 for signal in signals.values() if signal == 'SELL')
            total_signals = len(signals)
            
            # Determine trend direction
            if buy_count > sell_count:
                trend = 'BUY'
            elif sell_count > buy_count:
                trend = 'SELL'
            else:
                trend = 'NEUTRAL'
            
            # Calculate trend strength and confidence
            strength = abs(buy_count - sell_count) / total_signals
            
            # Calculate signal consistency over time
            consistent_signals = 0
            for ind in indicators:
                ind_buy_count = sum(1 for s in ind['signals'].values() if s == trend)
                if ind_buy_count > len(ind['signals']) / 2:
                    consistent_signals += 1
            
            confidence = consistent_signals / len(indicators)
            
            return {
                'trend': trend,
                'strength': strength,
                'confidence': confidence,
                'signals': signals,
                'updated_at': latest['timestamp']
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trend for {pair_symbol}: {str(e)}")
            raise 