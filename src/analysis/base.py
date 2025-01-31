from abc import ABC, abstractmethod
from typing import Dict, Any, List
import pandas as pd
from datetime import datetime

class BaseAnalyzer(ABC):
    """Base class for all market analyzers."""
    
    def __init__(self, timeframe: str = '1d'):
        """
        Initialize the analyzer.
        
        Args:
            timeframe: The timeframe for analysis ('1h', '1d', '1w', etc.)
        """
        self.timeframe = timeframe
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform market analysis.
        
        Args:
            data: Dictionary containing market data, indicators, news, etc.
            
        Returns:
            Dict containing analysis results
        """
        pass
    
    @abstractmethod
    def get_analysis_requirements(self) -> List[str]:
        """
        Get list of required data for analysis.
        
        Returns:
            List of required data keys
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Get analyzer description.
        
        Returns:
            String describing the analyzer's purpose and methodology
        """
        pass 