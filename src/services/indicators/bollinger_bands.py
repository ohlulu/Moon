import pandas as pd
import numpy as np
from src.services.indicators.indicator import Indicator

class BollingerBands(Indicator):
    def __init__(self, period: int = 20, num_std: float = 2.0):
        self.period = period
        self.num_std = num_std
        
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Bollinger Bands
        
        Args:
            df: DataFrame with 'close' column
            
        Returns:
            DataFrame with additional 'bb_middle', 'bb_upper', and 'bb_lower' columns
        """
        # Calculate middle band (SMA)
        df['bb_middle'] = df['close'].rolling(window=self.period).mean()
        
        # Calculate standard deviation
        rolling_std = df['close'].rolling(window=self.period).std()
        
        # Calculate upper and lower bands
        df['bb_upper'] = df['bb_middle'] + (rolling_std * self.num_std)
        df['bb_lower'] = df['bb_middle'] - (rolling_std * self.num_std)
        
        # Calculate bandwidth and %B (optional but useful)
        df['bb_bandwidth'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_percent_b'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        return df
    
    def get_name(self) -> str:
        return f"BB_{self.period}_{self.num_std}" 