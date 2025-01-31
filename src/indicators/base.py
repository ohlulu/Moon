from abc import ABC, abstractmethod
from typing import Dict, Any
import pandas as pd

class BaseIndicator(ABC):
    """Base class for all technical indicators."""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize the indicator.
        
        Args:
            df: DataFrame with OHLCV data, indexed by timestamp
        """
        self.df = df
        self.name = self.__class__.__name__
    
    @abstractmethod
    def calculate(self) -> Dict[str, Any]:
        """
        Calculate the indicator values.
        
        Returns:
            Dict containing the calculated values and any additional metadata
        """
        pass
    
    @abstractmethod
    def generate_signal(self) -> str:
        """
        Generate trading signal based on the indicator.
        
        Returns:
            String indicating the trading signal ('BUY', 'SELL', or 'NEUTRAL')
        """
        pass
    
    @property
    @abstractmethod
    def params(self) -> Dict[str, Any]:
        """
        Get the indicator's parameters.
        
        Returns:
            Dict containing the parameter names and their values
        """
        pass 