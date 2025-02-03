import pandas as pd
import talib
from src.services.indicators.indicator import Indicator

class OBV(Indicator):
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        df.loc[:, 'obv'] = talib.OBV(df['close'], df['volume'])
        
        # Add OBV EMA for signal line (optional but useful)
        df.loc[:, 'obv_ema'] = talib.EMA(df['obv'], timeperiod=20)
        
        return df
    
    def get_name(self) -> str:
        return "OBV" 