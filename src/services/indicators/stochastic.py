import pandas as pd
from src.services.indicators.indicator import Indicator

class Stochastic(Indicator):
    def __init__(self, k_period: int = 14, d_period: int = 3):
        self.k_period = k_period
        self.d_period = d_period
        
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Stochastic Oscillator
        
        Args:
            df: DataFrame with 'high', 'low', 'close' columns
            
        Returns:
            DataFrame with additional 'stoch_k' and 'stoch_d' columns
        """
        # Calculate %K
        lowest_low = df['low'].rolling(window=self.k_period).min()
        highest_high = df['high'].rolling(window=self.k_period).max()
        
        df['stoch_k'] = 100 * ((df['close'] - lowest_low) / (highest_high - lowest_low))
        
        # Calculate %D (SMA of %K)
        df['stoch_d'] = df['stoch_k'].rolling(window=self.d_period).mean()
        
        return df
    
    def get_name(self) -> str:
        return f"Stochastic_{self.k_period}_{self.d_period}" 