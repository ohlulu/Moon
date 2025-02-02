import pandas as pd
from src.services.indicators.indicator import Indicator

class MA(Indicator):
    def __init__(self, period: int = 20):
        self.period = period
        
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Simple Moving Average
        
        Args:
            df: DataFrame with 'close' column
            
        Returns:
            DataFrame with additional 'ma_{period}' column
        """
        df[f'ma_{self.period}'] = df['close'].rolling(window=self.period).mean()
        return df
    
    def get_name(self) -> str:
        return f"MA_{self.period}" 