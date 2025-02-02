import json
import os
from typing import List

from src.models.market_model import MarketModel
from src.models.market_cap_model import MarketCapModel
from src.utils.db.market_store import MarketStore
from src.utils.db.market_cap_store import MarketCapStore

class FileStore(MarketStore, MarketCapStore):
    """Implementation of MarketStore that uses a JSON file for storage"""
    
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.market_file_path = os.path.join(current_dir, "storage", "markets.json")
        self.market_cap_file_path = os.path.join(current_dir, "storage", "market_caps.json")
        
        # Create empty files if they don't exist
        for file_path in [self.market_file_path, self.market_cap_file_path]:
            if not os.path.exists(file_path):
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w') as f:
                    pass

    ## Market

    def save(self, markets: List[MarketModel]) -> None:
        self.delete_all()
        market_dicts = [market.model_dump(mode='json') for market in markets]
        with open(self.market_file_path, 'w') as f:
            json.dump(market_dicts, f, indent=2)
    
    def find_all(self) -> List[MarketModel]:
        try:
            with open(self.market_file_path, 'r') as f:
                market_dicts = json.load(f)
            return [MarketModel(**market_dict) for market_dict in market_dicts]
        except FileNotFoundError:
            return []
    
    def delete_all(self) -> None:
        with open(self.market_file_path, 'w') as f:
            f.truncate(0)

    ## Market Cap

    def save_market_caps(self, market_caps: List[MarketCapModel]) -> None:
        self.delete_all_market_caps()
        market_cap_dicts = [market_cap.model_dump(mode='json') for market_cap in market_caps]
        with open(self.market_cap_file_path, 'w') as f:
            json.dump(market_cap_dicts, f, indent=2)
    
    def find_all_market_caps(self) -> List[MarketCapModel]:
        try:
            with open(self.market_cap_file_path, 'r') as f:
                market_cap_dicts = json.load(f)
            return [MarketCapModel.Crypto.model_validate(market_cap_dict) for market_cap_dict in market_cap_dicts]
        except FileNotFoundError:
            return []
    
    def delete_all_market_caps(self) -> None:
        with open(self.market_cap_file_path, 'w') as f:
            f.truncate(0)
