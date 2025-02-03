import pandas as pd
import talib
from src.services.indicators.indicator import Indicator

class Stochastic(Indicator):
    def __init__(self, k_period: int = 14, d_period: int = 3):
        self.k_period = k_period
        self.d_period = d_period
        
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        slowk, slowd = talib.STOCH(
            df['high'],
            df['low'],
            df['close'],
            fastk_period=self.k_period,
            slowk_period=self.d_period,
            slowk_matype=0,
            slowd_period=self.d_period,
            slowd_matype=0
        )
        df.loc[:, 'stoch_k'] = slowk
        df.loc[:, 'stoch_d'] = slowd
        return df
    
    def get_name(self) -> str:
        return f"Stochastic_{self.k_period}_{self.d_period}" 