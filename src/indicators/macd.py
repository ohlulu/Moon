from typing import Dict, Any
import pandas as pd
from ta.trend import MACD as TaMACD
from .base import BaseIndicator

class MACD(BaseIndicator):
    """Moving Average Convergence Divergence (MACD) indicator."""
    
    def __init__(
        self,
        df: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ):
        """
        Initialize MACD indicator.
        
        Args:
            df: DataFrame with OHLCV data
            fast_period: The short-term period
            slow_period: The long-term period
            signal_period: The signal line period
        """
        super().__init__(df)
        self._fast_period = fast_period
        self._slow_period = slow_period
        self._signal_period = signal_period
        self._indicator = TaMACD(
            close=self.df['close'],
            window_fast=self._fast_period,
            window_slow=self._slow_period,
            window_sign=self._signal_period
        )
        self._current_values = None
    
    def calculate(self) -> Dict[str, Any]:
        """Calculate MACD values."""
        try:
            macd_line = self._indicator.macd().iloc[-1]
            signal_line = self._indicator.macd_signal().iloc[-1]
            histogram = self._indicator.macd_diff().iloc[-1]
            
            self._current_values = {
                'macd_line': macd_line,
                'signal_line': signal_line,
                'histogram': histogram
            }
            
            return {
                **self._current_values,
                'fast_period': self._fast_period,
                'slow_period': self._slow_period,
                'signal_period': self._signal_period
            }
            
        except Exception as e:
            raise ValueError(f"Error calculating MACD: {str(e)}")
    
    def generate_signal(self) -> str:
        """Generate trading signal based on MACD values."""
        if self._current_values is None:
            self.calculate()
            
        # Signal based on MACD line crossing signal line
        if self._current_values['macd_line'] > self._current_values['signal_line']:
            return 'BUY'
        elif self._current_values['macd_line'] < self._current_values['signal_line']:
            return 'SELL'
        return 'NEUTRAL'
    
    @property
    def params(self) -> Dict[str, Any]:
        """Get indicator parameters."""
        return {
            'fast_period': self._fast_period,
            'slow_period': self._slow_period,
            'signal_period': self._signal_period
        } 