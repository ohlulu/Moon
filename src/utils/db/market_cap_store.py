from abc import ABC, abstractmethod
from typing import List, Optional

from src.models.market_cap_model import MarketCapModel

class MarketCapStore(ABC):
    """Abstract base class for market data access"""
    
    @abstractmethod
    def save_market_caps(self, markets: List[MarketCapModel]) -> None:
        """Save multiple markets to the store
        
        Args:
            markets: List of market cap models to save
        """
        pass
    
    @abstractmethod
    def find_all_market_caps(self) -> List[MarketCapModel]:
        """Find all markets in the store
        
        Returns:
            List of all markets
        """
        pass
    
    @abstractmethod
    def delete_all_market_caps(self) -> None:
        """Delete all markets from the store"""
        pass
