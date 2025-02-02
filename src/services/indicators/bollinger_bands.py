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
        
        # Calculate middle band (SMA) with min_periods=1
        result_df.loc[:, 'bb_middle'] = result_df['close'].ewm(
            span=self.period, 
            min_periods=1
        ).mean()
        
        # Calculate standard deviation with min_periods=1
        rolling_std = result_df['close'].rolling(
            window=self.period,
            min_periods=1
        ).std()
        
        # Calculate upper and lower bands
        result_df.loc[:, 'bb_upper'] = result_df['bb_middle'] + (rolling_std * self.num_std)
        result_df.loc[:, 'bb_lower'] = result_df['bb_middle'] - (rolling_std * self.num_std)
        
        # Calculate bandwidth, handling division by zero
        bb_diff = result_df['bb_upper'] - result_df['bb_lower']
        middle_band = result_df['bb_middle'].replace(0, np.nan)
        result_df.loc[:, 'bb_bandwidth'] = bb_diff / middle_band
        
        # Calculate %B, handling division by zero
        price_from_lower = result_df['close'] - result_df['bb_lower']
        band_range = bb_diff.replace(0, np.nan)  # 避免除以零
        result_df.loc[:, 'bb_percent_b'] = price_from_lower / band_range
        
        # Handle edge cases for %B
        result_df.loc[band_range.isna(), 'bb_percent_b'] = 0.5  # 當上下軌道重合時，視為在中間
        result_df.loc[result_df['bb_percent_b'] > 1, 'bb_percent_b'] = 1  # 限制在 0-1 之間
        result_df.loc[result_df['bb_percent_b'] < 0, 'bb_percent_b'] = 0
        
        return result_df
    
    def get_name(self) -> str:
        return f"BB_{self.period}_{self.num_std}" 