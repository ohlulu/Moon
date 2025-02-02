import pandas as pd
import numpy as np
from src.services.indicators.indicator import Indicator

class OBV(Indicator):
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate On Balance Volume
        
        Args:
            df: DataFrame with 'close' and 'volume' columns
            
        Returns:
            DataFrame with additional 'obv' column
        """
        # Calculate price changes
        price_change = df['close'].diff()
        
        # Create OBV
        obv = pd.Series(index=df.index, dtype=float)
        obv.iloc[0] = 0
        
        # Calculate OBV values
        for i in range(1, len(df)):
            if price_change.iloc[i] > 0:
                obv.iloc[i] = obv.iloc[i-1] + df['volume'].iloc[i]
            elif price_change.iloc[i] < 0:
                obv.iloc[i] = obv.iloc[i-1] - df['volume'].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        df['obv'] = obv
        
        # Add OBV EMA for signal line (optional but useful)
        df['obv_ema'] = df['obv'].ewm(span=20, adjust=False).mean()
        
        return df
    
    def get_name(self) -> str:
        return "OBV" 