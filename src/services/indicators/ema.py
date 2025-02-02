import pandas as pd
from src.services.indicators.indicator import Indicator

class EMA(Indicator):
    def __init__(self, period: int = 20):
        self.period = period
        
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Exponential Moving Average
        
        Args:
            df: DataFrame with 'close' column
            
        Returns:
            DataFrame with additional 'ema_{period}' column
        """
        df[f'ema_{self.period}'] = df['close'].ewm(span=self.period, adjust=False).mean()
        return df
    
    def get_name(self) -> str:
        return f"EMA_{self.period}" 