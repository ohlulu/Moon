import pandas as pd
from src.services.indicators.indicator import Indicator

class MACD(Indicator):
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate MACD
        
        Args:
            df: DataFrame with 'close' column
            
        Returns:
            DataFrame with additional 'macd', 'macd_signal' and 'macd_hist' columns
        """
        # Calculate the EMA
        exp1 = df['close'].ewm(span=self.fast_period, adjust=False).mean()
        exp2 = df['close'].ewm(span=self.slow_period, adjust=False).mean()
        
        # Calculate MACD line
        df['macd'] = exp1 - exp2
        
        # Calculate signal line
        df['macd_signal'] = df['macd'].ewm(span=self.signal_period, adjust=False).mean()
        
        # Calculate histogram
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        return df
    
    def get_name(self) -> str:
        return f"MACD_{self.fast_period}_{self.slow_period}_{self.signal_period}" 