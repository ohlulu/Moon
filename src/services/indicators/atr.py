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
        # Create a copy of the DataFrame
        result_df = df.copy()
        
        # Calculate True Range
        high_low = result_df['high'] - result_df['low']
        high_close = np.abs(result_df['high'] - result_df['close'].shift().fillna(result_df['high']))
        low_close = np.abs(result_df['low'] - result_df['close'].shift().fillna(result_df['low']))
        
        # Calculate true range using vectorized operations
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        
        # Calculate ATR using EMA to avoid NA values
        result_df.loc[:, 'atr'] = true_range.ewm(span=self.period, min_periods=1).mean()
        
        return result_df
    
    def get_name(self) -> str:
        return f"ATR_{self.period}" 