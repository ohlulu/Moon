import pandas as pd
import talib
from src.services.indicators.indicator import Indicator

class MACD(Indicator):
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        macd, signal, hist = talib.MACD(
            df['close'],
            fastperiod=self.fast_period,
            slowperiod=self.slow_period,
            signalperiod=self.signal_period
        )
        df.loc[:, 'macd'] = macd
        df.loc[:, 'macd_signal'] = signal
        df.loc[:, 'macd_hist'] = hist
        return df
    
    def get_name(self) -> str:
        return f"MACD_{self.fast_period}_{self.slow_period}_{self.signal_period}" 