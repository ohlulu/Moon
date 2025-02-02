from typing import List, Dict

from src.utils.clients.binance_client import BinanceClient
from src.utils.clients.conin_market_cap_client import CoinMarketCapClient
from src.utils.db.file_store import FileStore

class MarketDataCollector:
    """Service for collecting market data from Binance and storing it"""
    
    def __init__(self):
        """Initialize the collector with Binance client and file store"""
        self.binance_client = BinanceClient()
        self.coin_market_cap_client = CoinMarketCapClient()
        self.market_store = FileStore()
    
    def collect_and_store(self) -> None:
        """Collect market data from Binance and store it in the file"""
        # 從 Binance 獲取市場資料並儲存到檔案
        market_models = self.binance_client.fetch_markets()
        self.market_store.save(market_models)

        # 從 CoinMarketCap 獲取市場資料並儲存到檔案
        market_cap_models = self.coin_market_cap_client.fetch_market_caps()
        self.market_store.save_market_caps(market_cap_models)

if __name__ == "__main__":
    collector = MarketDataCollector()
    collector.collect_and_store()
