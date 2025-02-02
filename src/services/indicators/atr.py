import pandas as pd
import numpy as np
from src.services.indicators.indicator import Indicator

class ATR(Indicator):
    def __init__(self, period: int = 14):
        self.period = period
        
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Average True Range
        
        Args:
            df: DataFrame with 'high', 'low', 'close' columns
            
        Returns:
            DataFrame with additional 'atr' column
        """
        # Calculate True Range
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        
        # Calculate ATR
        df['atr'] = true_range.rolling(window=self.period).mean()
        
        return df
    
    def get_name(self) -> str:
        return f"ATR_{self.period}" 