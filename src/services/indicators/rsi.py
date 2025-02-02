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
        # Calculate price changes
        delta = df['close'].diff()
        
        # Create gain (up) and loss (down) series
        gain = (delta.where(delta > 0, 0))
        loss = (-delta.where(delta < 0, 0))
        
        # Calculate average gain and loss
        avg_gain = gain.rolling(window=self.period).mean()
        avg_loss = loss.rolling(window=self.period).mean()
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        return df
    
    def get_name(self) -> str:
        return f"RSI_{self.period}" 