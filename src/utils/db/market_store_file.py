import json
import os
from typing import List

from src.models.market_model import MarketModel
from src.utils.db.market_store import MarketStore

class MarketStoreFile(MarketStore):
    """Implementation of MarketStore that uses a JSON file for storage"""
    
    def __init__(self):
        """Initialize the file store
        
        Args:
            file_path: Path to the JSON file for storage
        """
        self.file_path = "storage/markets.json"
        
        # Create file if it doesn't exist
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump([], f)
    
    def save(self, markets: List[MarketModel]) -> None:
        """Save multiple markets to the JSON file
        
        Args:
            markets: List of market models to save
        """

        self.delete_all()

        market_dicts = [market.dict() for market in markets]
        with open(self.file_path, 'w') as f:
            json.dump(market_dicts, f, indent=2)
    
    def find_all(self) -> List[MarketModel]:
        """Find all markets in the JSON file
        
        Returns:
            List of all markets
        """
        try:
            with open(self.file_path, 'r') as f:
                market_dicts = json.load(f)
            return [MarketModel(**market_dict) for market_dict in market_dicts]
        except FileNotFoundError:
            return []
    
    def delete_all(self) -> None:
        """Delete all markets by truncating the file"""
        with open(self.file_path, 'w') as f:
            f.truncate(0)
