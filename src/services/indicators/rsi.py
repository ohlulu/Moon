import pandas as pd
import numpy as np
from src.services.indicators.indicator import Indicator

class RSI(Indicator):
    def __init__(self, period: int = 14):
        self.period = period
        
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate RSI
        
        Args:
            df: DataFrame with 'close' column
            
        Returns:
            DataFrame with additional 'rsi' column
        """
        # Create a copy of the DataFrame
        result_df = df.copy()
        
        # Calculate price changes
        delta = result_df['close'].diff()
        
        # Create gain (up) and loss (down) series
        gain = (delta.where(delta > 0, 0))
        loss = (-delta.where(delta < 0, 0))
        
        # Calculate average gain and loss using EMA to avoid NA values
        avg_gain = gain.ewm(span=self.period, min_periods=self.period).mean()
        avg_loss = loss.ewm(span=self.period, min_periods=self.period).mean()
        
        # Calculate RS and RSI, handling division by zero
        rs = avg_gain / avg_loss.replace(0, np.inf)  # 當 avg_loss 為 0 時，RSI 應為 100
        result_df.loc[:, 'rsi'] = 100 - (100 / (1 + rs))
        
        # Handle edge cases
        result_df.loc[avg_gain == 0, 'rsi'] = 0  # 當 avg_gain 為 0 時，RSI 應為 0
        result_df.loc[avg_loss == 0, 'rsi'] = 100  # 當 avg_loss 為 0 時，RSI 應為 100
        
        return result_df
    
    def get_name(self) -> str:
        return f"RSI_{self.period}" 