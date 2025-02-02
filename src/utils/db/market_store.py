from abc import ABC, abstractmethod
from typing import List, Optional

from src.models.market_model import MarketModel

class MarketStore(ABC):
    """Abstract base class for market data access"""
    
    @abstractmethod
    def save(self, market: MarketModel) -> None:
        """Save a market to the store
        
        Args:
            market: The market model to save
        """
        pass
    
    @abstractmethod
    def save_all(self, markets: List[MarketModel]) -> None:
        """Save multiple markets to the store
        
        Args:
            markets: List of market models to save
        """
        pass
    
    @abstractmethod
    def find_by_id(self, market_id: str) -> Optional[MarketModel]:
        """Find a market by its ID
        
        Args:
            market_id: The ID of the market to find
            
        Returns:
            The market if found, None otherwise
        """
        pass
    
    @abstractmethod
    def find_by_symbol(self, symbol: str) -> Optional[MarketModel]:
        """Find a market by its symbol
        
        Args:
            symbol: The symbol of the market to find
            
        Returns:
            The market if found, None otherwise
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
    def find_by_exchange(self, exchange: str) -> List[MarketModel]:
        """Find all markets for a specific exchange
        
        Args:
            exchange: The name of the exchange
            
        Returns:
            List of markets for the specified exchange
        """
        pass
    
    @abstractmethod
    def delete(self, market_id: str) -> None:
        """Delete a market from the store
        
        Args:
            market_id: The ID of the market to delete
        """
        pass
    
    @abstractmethod
    def delete_all(self) -> None:
        """Delete all markets from the store"""
        pass
