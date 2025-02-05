import pandas as pd
import talib
from src.services.indicators.indicator import Indicator

class ATR(Indicator):
    def __init__(self, period: int = 14):
        self.period = period
        
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.loc[:, 'atr'] = talib.ATR(
            df['high'],
            df['low'],
            df['close'],
            timeperiod=self.period
        )
        return df
    
    def get_name(self) -> str:
        return f"ATR_{self.period}" 