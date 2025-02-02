from typing import List, Dict

from src.models.market_model import MarketModel
from src.utils.clients.binance_client import BinanceClient
from src.utils.db.market_store_file import MarketStoreFile

class MarketDataCollector:
    """Service for collecting market data from Binance and storing it"""
    
    def __init__(self):
        """Initialize the collector with Binance client and file store"""
        self.binance_client = BinanceClient()
        self.market_store = MarketStoreFile()
    
    def collect_and_store(self) -> None:
        """Collect market data from Binance and store it in the file"""
        # 從 Binance 獲取市場資料並儲存到檔案
        market_models = self.binance_client.fetch_markets()
        self.market_store.save(market_models)

