import pandas as pd
import talib
from src.services.indicators.indicator import Indicator

class RSI(Indicator):
    def __init__(self, period: int = 14):
        self.period = period
        
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        df['rsi'] = talib.RSI(df['close'], timeperiod=self.period)
        return df
    
    def get_name(self) -> str:
        return f"RSI_{self.period}" 