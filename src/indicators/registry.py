from typing import Dict, Type, List
import logging
from .base import BaseIndicator
from .rsi import RSI
from .macd import MACD
from .bollinger import BollingerBands

logger = logging.getLogger(__name__)

class IndicatorRegistry:
    """Registry for managing technical indicators."""
    
    def __init__(self):
        """Initialize registry with default indicators."""
        self._indicators: Dict[str, Type[BaseIndicator]] = {}
        self._register_default_indicators()
    
    def _register_default_indicators(self):
        """Register default technical indicators."""
        self.register_indicator('RSI', RSI)
        self.register_indicator('MACD', MACD)
        self.register_indicator('BOLLINGER', BollingerBands)
    
    def register_indicator(self, name: str, indicator_class: Type[BaseIndicator]):
        """
        Register a new indicator.
        
        Args:
            name: Unique name for the indicator
            indicator_class: The indicator class to register
        """
        if not issubclass(indicator_class, BaseIndicator):
            raise ValueError(
                f"Indicator class must inherit from BaseIndicator: {indicator_class}"
            )
        
        if name in self._indicators:
            logger.warning(f"Overwriting existing indicator: {name}")
        
        self._indicators[name] = indicator_class
        logger.info(f"Registered indicator: {name}")
    
    def unregister_indicator(self, name: str):
        """
        Unregister an indicator.
        
        Args:
            name: Name of the indicator to unregister
        """
        if name in self._indicators:
            del self._indicators[name]
            logger.info(f"Unregistered indicator: {name}")
        else:
            logger.warning(f"Indicator not found: {name}")
    
    def get_indicator(self, name: str) -> Type[BaseIndicator]:
        """
        Get an indicator class by name.
        
        Args:
            name: Name of the indicator
            
        Returns:
            The indicator class
            
        Raises:
            KeyError: If indicator is not found
        """
        if name not in self._indicators:
            raise KeyError(f"Indicator not found: {name}")
        return self._indicators[name]
    
    def list_indicators(self) -> List[str]:
        """
        Get list of registered indicator names.
        
        Returns:
            List of indicator names
        """
        return list(self._indicators.keys())
    
    def get_indicator_info(self, name: str) -> Dict:
        """
        Get information about an indicator.
        
        Args:
            name: Name of the indicator
            
        Returns:
            Dict containing indicator information
        """
        indicator_class = self.get_indicator(name)
        return {
            'name': name,
            'description': indicator_class.__doc__,
            'params': self._get_default_params(indicator_class)
        }
    
    def _get_default_params(self, indicator_class: Type[BaseIndicator]) -> Dict:
        """Get default parameters from indicator class."""
        import inspect
        signature = inspect.signature(indicator_class.__init__)
        params = {}
        
        for name, param in signature.parameters.items():
            if name not in ['self', 'df']:  # Skip self and df parameters
                params[name] = param.default if param.default != param.empty else None
        
        return params

# Global registry instance
registry = IndicatorRegistry() 