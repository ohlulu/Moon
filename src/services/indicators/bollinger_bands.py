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
        # Create a copy of the DataFrame
        result_df = df.copy()
        
        # Calculate middle band (SMA)
        result_df.loc[:, 'bb_middle'] = result_df['close'].rolling(window=self.period).mean()
        
        # Calculate standard deviation
        rolling_std = result_df['close'].rolling(window=self.period).std()
        
        # Calculate upper and lower bands
        result_df.loc[:, 'bb_upper'] = result_df['bb_middle'] + (rolling_std * self.num_std)
        result_df.loc[:, 'bb_lower'] = result_df['bb_middle'] - (rolling_std * self.num_std)
        
        # Calculate bandwidth and %B (optional but useful)
        result_df.loc[:, 'bb_bandwidth'] = (result_df['bb_upper'] - result_df['bb_lower']) / result_df['bb_middle']
        result_df.loc[:, 'bb_percent_b'] = (result_df['close'] - result_df['bb_lower']) / (result_df['bb_upper'] - result_df['bb_lower'])
        
        return result_df
    
    def get_name(self) -> str:
        return f"BB_{self.period}_{self.num_std}" 