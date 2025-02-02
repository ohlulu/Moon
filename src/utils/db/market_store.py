from abc import ABC, abstractmethod
from typing import List, Optional

from src.models.market_model import MarketModel

class MarketStore(ABC):
    """Abstract base class for market data access"""
    
    @abstractmethod
    def save(self, markets: List[MarketModel]) -> None:
        """Save multiple markets to the store
        
        Args:
            markets: List of market models to save
        """
        pass
    
    @abstractmethod
    def find_all(self) -> List[MarketModel]:
        """Find all markets in the store
        
        Returns:
            List of all markets
        """
        pass
    
    @abstractmethod
    def delete_all(self) -> None:
        """Delete all markets from the store"""
        pass
