from typing import Dict, Any
import pandas as pd
from ta.volatility import BollingerBands as TaBB
from .base import BaseIndicator

class BollingerBands(BaseIndicator):
    """Bollinger Bands indicator."""
    
    def __init__(
        self,
        df: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0
    ):
        """
        Initialize Bollinger Bands indicator.
        
        Args:
            df: DataFrame with OHLCV data
            period: The number of periods to use for calculations
            std_dev: Number of standard deviations for the bands
        """
        super().__init__(df)
        self._period = period
        self._std_dev = std_dev
        self._indicator = TaBB(
            close=self.df['close'],
            window=self._period,
            window_dev=self._std_dev
        )
        self._current_values = None
    
    def calculate(self) -> Dict[str, Any]:
        """Calculate Bollinger Bands values."""
        try:
            upper = self._indicator.bollinger_hband().iloc[-1]
            middle = self._indicator.bollinger_mavg().iloc[-1]
            lower = self._indicator.bollinger_lband().iloc[-1]
            
            self._current_values = {
                'upper': upper,
                'middle': middle,
                'lower': lower
            }
            
            # Calculate bandwidth and %B
            bandwidth = (upper - lower) / middle
            current_price = self.df['close'].iloc[-1]
            percent_b = (current_price - lower) / (upper - lower)
            
            return {
                **self._current_values,
                'bandwidth': bandwidth,
                'percent_b': percent_b,
                'period': self._period,
                'std_dev': self._std_dev
            }
            
        except Exception as e:
            raise ValueError(f"Error calculating Bollinger Bands: {str(e)}")
    
    def generate_signal(self) -> str:
        """Generate trading signal based on Bollinger Bands."""
        if self._current_values is None:
            self.calculate()
            
        current_price = self.df['close'].iloc[-1]
        
        # Signal based on price position relative to bands
        if current_price > self._current_values['upper']:
            return 'SELL'  # Overbought
        elif current_price < self._current_values['lower']:
            return 'BUY'   # Oversold
        return 'NEUTRAL'
    
    @property
    def params(self) -> Dict[str, Any]:
        """Get indicator parameters."""
        return {
            'period': self._period,
            'std_dev': self._std_dev
        } 