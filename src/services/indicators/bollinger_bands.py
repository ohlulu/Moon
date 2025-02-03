import pandas as pd
import numpy as np
import talib
from src.services.indicators.indicator import Indicator

class BollingerBands(Indicator):
    def __init__(self, period: int = 20, num_std: float = 2.0):
        self.period = period
        self.num_std = num_std
        
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        upper, middle, lower = talib.BBANDS(
            df['close'],
            timeperiod=self.period,
            nbdevup=self.num_std,
            nbdevdn=self.num_std,
            matype=talib.MA_Type.SMA
        )
        
        df['bb_upper'] = upper
        df['bb_middle'] = middle
        df['bb_lower'] = lower
        
        # Calculate bandwidth
        bb_diff = df['bb_upper'] - df['bb_lower']
        middle_band = df['bb_middle'].replace(0, np.nan)
        df['bb_bandwidth'] = bb_diff / middle_band
        
        # Calculate %B
        price_from_lower = df['close'] - df['bb_lower']
        band_range = bb_diff.replace(0, np.nan)
        df['bb_percent_b'] = price_from_lower / band_range
        
        # Handle edge cases for %B
        df.loc[band_range.isna(), 'bb_percent_b'] = 0.5
        df.loc[df['bb_percent_b'] > 1, 'bb_percent_b'] = 1
        df.loc[df['bb_percent_b'] < 0, 'bb_percent_b'] = 0
        
        return df
    
    def get_name(self) -> str:
        return f"BB_{self.period}_{self.num_std}" 