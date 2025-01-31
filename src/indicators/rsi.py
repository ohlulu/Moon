from typing import Dict, Any
import pandas as pd
from ta.momentum import RSIIndicator as TaRSI
from .base import BaseIndicator

class RSI(BaseIndicator):
    """Relative Strength Index (RSI) indicator."""
    
    def __init__(
        self,
        df: pd.DataFrame,
        period: int = 14,
        overbought: float = 70,
        oversold: float = 30
    ):
        """
        Initialize RSI indicator.
        
        Args:
            df: DataFrame with OHLCV data
            period: The number of periods to use for RSI calculation
            overbought: The overbought threshold
            oversold: The oversold threshold
        """
        super().__init__(df)
        self._period = period
        self._overbought = overbought
        self._oversold = oversold
        self._indicator = TaRSI(
            close=self.df['close'],
            window=self._period
        )
        self._current_value = None
    
    def calculate(self) -> Dict[str, Any]:
        """Calculate RSI values."""
        try:
            self._current_value = self._indicator.rsi().iloc[-1]
            
            return {
                'value': self._current_value,
                'overbought': self._overbought,
                'oversold': self._oversold
            }
            
        except Exception as e:
            raise ValueError(f"Error calculating RSI: {str(e)}")
    
    def generate_signal(self) -> str:
        """Generate trading signal based on RSI value."""
        if self._current_value is None:
            self.calculate()
            
        if self._current_value > self._overbought:
            return 'SELL'
        elif self._current_value < self._oversold:
            return 'BUY'
        return 'NEUTRAL'
    
    @property
    def params(self) -> Dict[str, Any]:
        """Get indicator parameters."""
        return {
            'period': self._period,
            'overbought': self._overbought,
            'oversold': self._oversold
        } 