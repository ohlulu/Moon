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
        # Create a copy of the DataFrame
        result_df = df.copy()
        
        # Calculate the EMA with min_periods=1 to avoid initial NA values
        exp1 = result_df['close'].ewm(span=self.fast_period, min_periods=1, adjust=False).mean()
        exp2 = result_df['close'].ewm(span=self.slow_period, min_periods=1, adjust=False).mean()
        
        # Calculate MACD line
        result_df.loc[:, 'macd'] = exp1 - exp2
        
        # Calculate signal line
        result_df.loc[:, 'macd_signal'] = result_df['macd'].ewm(
            span=self.signal_period, 
            min_periods=1, 
            adjust=False
        ).mean()
        
        # Calculate histogram
        result_df.loc[:, 'macd_hist'] = result_df['macd'] - result_df['macd_signal']
        
        return result_df
    
    def get_name(self) -> str:
        return f"MACD_{self.fast_period}_{self.slow_period}_{self.signal_period}" 