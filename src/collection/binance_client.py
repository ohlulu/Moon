import os
import logging
import ccxt
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class BinanceClient:
    """Client for interacting with Binance API."""
    
    def __init__(self):
        """Initialize Binance client."""
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_SECRET_KEY')
        
        # Initialize CCXT Binance client
        self.exchange = ccxt.binance({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'  # 'spot', 'future', 'margin'
            }
        })
        
        # Initialize markets cache
        self._markets_cache: Optional[Dict] = None
        self._last_markets_update: Optional[datetime] = None
        
    async def get_top_pairs(self, quote_currency: str = 'USDT', limit: int = 500) -> List[Dict]:
        """Get top trading pairs by market cap."""
        try:
            # Refresh markets if needed
            await self._refresh_markets_if_needed()
            
            # Filter and sort pairs
            pairs = []
            for symbol, market in self._markets_cache.items():
                if not symbol.endswith(quote_currency):
                    continue
                    
                ticker = await self.get_ticker(symbol)
                if not ticker:
                    continue
                
                market_data = {
                    'pair_symbol': symbol,
                    'market_type': 'spot',
                    'market_cap': float(ticker.get('quoteVolume', 0)),  # Using 24h volume as proxy
                    'volume_24h': float(ticker.get('quoteVolume', 0)),
                    'last_updated': datetime.utcnow(),
                    'metadata': {
                        'base_currency': market['base'],
                        'quote_currency': market['quote'],
                        'price_precision': market.get('precision', {}).get('price', 8),
                        'minimum_order_size': market.get('limits', {}).get('amount', {}).get('min', 0)
                    }
                }
                pairs.append(market_data)
            
            # Sort by market cap and return top pairs
            pairs.sort(key=lambda x: x['market_cap'], reverse=True)
            return pairs[:limit]
            
        except Exception as e:
            logger.error(f"Error fetching top pairs: {str(e)}")
            raise
    
    async def get_ticker(self, symbol: str) -> Optional[Dict]:
        """Get ticker information for a symbol."""
        try:
            return await self.exchange.fetch_ticker(symbol)
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {str(e)}")
            return None
    
    async def get_historical_data(
        self,
        symbol: str,
        timeframe: str = '1d',
        limit: int = 100
    ) -> List[Dict]:
        """Get historical OHLCV data for a symbol."""
        try:
            ohlcv = await self.exchange.fetch_ohlcv(
                symbol,
                timeframe=timeframe,
                limit=limit
            )
            
            return [{
                'timestamp': datetime.fromtimestamp(candle[0] / 1000),
                'open': candle[1],
                'high': candle[2],
                'low': candle[3],
                'close': candle[4],
                'volume': candle[5]
            } for candle in ohlcv]
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            raise
    
    async def _refresh_markets_if_needed(self):
        """Refresh markets cache if needed."""
        now = datetime.utcnow()
        if (not self._markets_cache or
            not self._last_markets_update or
            now - self._last_markets_update > timedelta(hours=1)):
            
            try:
                self._markets_cache = await self.exchange.load_markets()
                self._last_markets_update = now
                logger.info("Successfully refreshed markets cache")
            except Exception as e:
                logger.error(f"Error refreshing markets: {str(e)}")
                raise
    
    async def get_futures_positions(self) -> List[Dict]:
        """Get current futures positions."""
        try:
            self.exchange.options['defaultType'] = 'future'
            positions = await self.exchange.fetch_positions()
            self.exchange.options['defaultType'] = 'spot'  # Reset to default
            return positions
        except Exception as e:
            logger.error(f"Error fetching futures positions: {str(e)}")
            self.exchange.options['defaultType'] = 'spot'  # Reset to default
            raise
    
    async def close(self):
        """Close the client connection."""
        await self.exchange.close() 