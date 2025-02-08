import pandas as pd
import talib
from src.services.indicators.indicator import Indicator

class Ichimoku(Indicator):
    def __init__(self, tenkan_period: int =9, kijun_period: int =26, senkou_b_period: int =52):
        self.tenkan_period = tenkan_period
        self.kijun_period = kijun_period
        self.senkou_b_period = senkou_b_period
        
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        計算一目均衡表（Ichimoku Cloud）的各個組件
        
        Parameters:
        -----------
        df: DataFrame，需要包含 'high' 和 'low' 列
        tenkan_period: 轉換線週期，默認9
        kijun_period: 基準線週期，默認26
        senkou_b_period: 先行帶B週期，默認52
        
        Returns:
        --------
        DataFrame with Ichimoku components
        """
        # 計算轉換線 (Conversion Line，Tenkan-sen)
        high_tenkan = df['high'].rolling(window=self.tenkan_period).max()
        low_tenkan = df['low'].rolling(window=self.tenkan_period).min()
        df['tenkan_sen'] = (high_tenkan + low_tenkan) / 2
        
        # 計算基準線 (Base Line，Kijun-sen)
        high_kijun = df['high'].rolling(window=self.kijun_period).max()
        low_kijun = df['low'].rolling(window=self.kijun_period).min()
        df['kijun_sen'] = (high_kijun + low_kijun) / 2
        
        # 計算先行帶A (Leading Span A，Senkou Span A)
        # 轉換線和基準線的平均，向前移動26個週期
        df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(self.kijun_period)
        
        # 計算先行帶B (Leading Span B，Senkou Span B)
        # 52週期的最高價和最低價的平均，向前移動26個週期
        high_senkou = df['high'].rolling(window=self.senkou_b_period).max()
        low_senkou = df['low'].rolling(window=self.senkou_b_period).min()
        df['senkou_span_b'] = ((high_senkou + low_senkou) / 2).shift(self.kijun_period)
        
        # 計算延遲線 (Lagging Span，Chikou Span)
        # 當前收盤價向後移動26個週期
        df['chikou_span'] = df['close'].shift(-self.kijun_period)
        
        return df
    
    def get_name(self) -> str:
        return f"Ichimoku" 