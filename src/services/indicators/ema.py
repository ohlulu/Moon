import pandas as pd
import talib
from src.services.indicators.indicator import Indicator

class EMA(Indicator):
    def __init__(self, period: int = 20):
        self.period = period
        
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        df[f'ema_{self.period}'] = talib.EMA(df['close'], timeperiod=self.period)
        return df
    
    def get_name(self) -> str:
        return f"EMA_{self.period}" 