import pandas as pd
import talib
from src.services.indicators.indicator import Indicator

class MA(Indicator):
    def __init__(self, period: int = 20):
        self.period = period
        
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        df.loc[:, f'ma_{self.period}'] = talib.SMA(df['close'], timeperiod=self.period)
        return df
    
    def get_name(self) -> str:
        return f"MA_{self.period}" 