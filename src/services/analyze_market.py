from dataclasses import dataclass
from typing import List, Dict, Optional
import pandas as pd
import numpy as np

from src.services.indicators.ema import EMA
from src.services.indicators.macd import MACD
from src.services.indicators.rsi import RSI
from src.services.indicators.stochastic import Stochastic
from src.services.indicators.bollinger_bands import BollingerBands
from src.services.indicators.atr import ATR
from src.services.indicators.obv import OBV
from src.services.indicators.volume_profile import VolumeProfile
from src.services.leverage_calculator import LeverageCalculator, LeverageInfo

@dataclass
class TradeSignal:
    """交易信號結果"""
    symbol: str                 # 交易對
    signal_type: str            # 信號類型：'spot_buy', 'spot_sell', 'swap_long', 'swap_short'
    confidence: float           # 信心指數：0-1
    entry_price: float          # 建議入場價
    stop_loss: float            # 建議止損價
    take_profit: float          # 建議獲利價
    indicators_values: Dict     # 指標數值
    description: str            # 信號描述
    leverage_info: Optional[LeverageInfo] = None  # 槓桿資訊（僅用於合約交易）

class MarketAnalyzer:
    """市場分析器"""
    
    def __init__(self):
        # 初始化指標
        self._init_indicators()
        self.leverage_calculator = LeverageCalculator()
        
    def _init_indicators(self):
        """初始化所有技術指標"""
        # 趨勢指標
        self.ema_20 = EMA(20)
        self.ema_50 = EMA(50)
        self.macd = MACD(12, 26, 9)
        self.bb = BollingerBands(20, 2.0)
        
        # 動能指標
        self.rsi = RSI(14)
        self.stoch = Stochastic(14, 3)
        
        # 波動指標
        self.atr = ATR(14)
        
        # 成交量指標
        self.obv = OBV()
        self.volume_profile = VolumeProfile(24)
        
    def analyze_spot(self, df: pd.DataFrame, symbol: str) -> Optional[TradeSignal]:
        """分析現貨交易機會
        
        Args:
            df: 包含 OHLCV 數據的 DataFrame
            symbol: 交易對名稱
            
        Returns:
            如果發現交易機會，返回 TradeSignal，否則返回 None
        """
        # 計算所有指標
        df = self._calculate_indicators(df)
        
        # 最新的一根K線數據
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 計算信心指數
        confidence = 0
        signal_reasons = []
        
        # 1. 趨勢確認（權重：40%）
        if latest[f'ema_20'] > latest[f'ema_50']:
            confidence += 0.2
            signal_reasons.append("中期趨勢向上（EMA20 > EMA50）")
            
            if latest['macd'] > latest['macd_signal']:
                confidence += 0.2
                signal_reasons.append("MACD 顯示上升動能")
        
        # 2. 價格位置（權重：20%）
        if latest['close'] > latest['bb_middle']:
            confidence += 0.1
            signal_reasons.append("價格在布林帶中軌上方")
            
        if 0.3 <= latest['bb_percent_b'] <= 0.7:
            confidence += 0.1
            signal_reasons.append("價格在布林帶健康區間")
        
        # 3. 動能確認（權重：20%）
        if 30 <= latest['rsi'] <= 70:
            confidence += 0.1
            signal_reasons.append("RSI 在健康區間")
            
        if latest['stoch_k'] > latest['stoch_d']:
            confidence += 0.1
            signal_reasons.append("Stochastic 顯示上升動能")
        
        # 4. 成交量確認（權重：20%）
        if latest['obv'] > latest['obv_ema']:
            confidence += 0.2
            signal_reasons.append("OBV 顯示成交量支撐")
            
        # 如果信心指數大於 0.7，生成交易信號
        if confidence >= 0.7:
            # 使用 ATR 計算止損和獲利價位
            stop_loss = latest['close'] - (latest['atr'] * 2)
            take_profit = latest['close'] + (latest['atr'] * 3)
            
            return TradeSignal(
                symbol=symbol,
                signal_type='spot_buy',
                confidence=confidence,
                entry_price=latest['close'],
                stop_loss=stop_loss,
                take_profit=take_profit,
                indicators_values={
                    'rsi': latest['rsi'],
                    'macd': latest['macd'],
                    'bb_percent_b': latest['bb_percent_b'],
                    'volume_profile_poc': latest['poc_price']
                },
                description='\n'.join(signal_reasons)
            )
        
        return None
        
    def _calculate_trend_strength(self, df: pd.DataFrame) -> float:
        """計算趨勢強度
        
        綜合考慮以下因素：
        1. 均線排列（20%）
        2. MACD 狀態（20%）
        3. 價格位置（20%）
        4. 趨勢持續性（20%）
        5. 突破強度（20%）
        
        Returns:
            趨勢強度 0-1
        """
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        strength = 0.0
        
        # 1. 均線排列（考慮斜率）
        ema_20_slope = (latest['ema_20'] - df.iloc[-5]['ema_20']) / df.iloc[-5]['ema_20']
        ema_50_slope = (latest['ema_50'] - df.iloc[-5]['ema_50']) / df.iloc[-5]['ema_50']
        
        if latest['ema_20'] > latest['ema_50']:
            strength += 0.1
            if ema_20_slope > 0:
                strength += 0.05
                if ema_20_slope > ema_50_slope:
                    strength += 0.05
        
        # 2. MACD 狀態
        if latest['macd'] > 0:
            strength += 0.1
            if latest['macd'] > latest['macd_signal']:
                strength += 0.05
                if latest['macd'] > prev['macd']:  # MACD 上升
                    strength += 0.05
        
        # 3. 價格位置
        bb_position = (latest['close'] - latest['bb_lower']) / (latest['bb_upper'] - latest['bb_lower'])
        if bb_position > 0.5:  # 價格在布林帶上半部
            strength += 0.1
            if bb_position > 0.8:  # 接近上軌（強勢）
                strength += 0.1
        
        # 4. 趨勢持續性（考慮最近 10 根K線）
        recent_closes = df.iloc[-10:]['close']
        up_candles = sum(1 for i in range(1, len(recent_closes)) if recent_closes.iloc[i] > recent_closes.iloc[i-1])
        trend_consistency = up_candles / 9  # 9 是相鄰兩根K線的比較次數
        strength += trend_consistency * 0.2
        
        # 5. 突破強度
        if latest['close'] > latest['va_high']:  # 突破 Volume Profile 高點
            volume_ratio = latest['volume'] / df['volume'].rolling(20).mean().iloc[-1]
            strength += min(0.2, volume_ratio * 0.1)  # 成交量放大程度影響突破強度
        
        return min(1.0, strength)

    def analyze_swap(self, df: pd.DataFrame, symbol: str) -> Optional[TradeSignal]:
        """分析合約交易機會（槓桿4-6倍）
        
        Args:
            df: 包含 OHLCV 數據的 DataFrame
            symbol: 交易對名稱
            
        Returns:
            如果發現交易機會，返回 TradeSignal，否則返回 None
        """
        # 計算所有指標
        df = self._calculate_indicators(df)
        
        # 最新的一根K線數據
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 計算信心指數（合約交易需要更嚴格的條件）
        confidence = 0
        signal_reasons = []
        
        # 1. 波動性檢查（權重：40%）
        volatility = latest['atr'] / latest['close']  # 計算波動率
        atr_threshold = 0.002  # 0.2% 為合理波動
        if volatility <= atr_threshold:
            confidence += 0.2
            signal_reasons.append("波動率在合理範圍內")
            
        if latest['bb_bandwidth'] <= 0.05:  # 布林帶收窄
            confidence += 0.2
            signal_reasons.append("布林帶收窄，可能即將突破")
        
        # 2. 趨勢確認（權重：30%）
        trend_strength = self._calculate_trend_strength(df)
        if trend_strength > 0.6:  # 趨勢強度大於 60%
            confidence += 0.15
            signal_reasons.append(f"趨勢強度良好：{trend_strength:.1%}")
            
        if latest['macd'] > latest['macd_signal'] and latest['macd'] > 0:
            confidence += 0.15
            signal_reasons.append("MACD 顯示強勁上升動能")
        
        # 3. 價格行為（權重：30%）
        if latest['close'] > latest['va_high']:  # 突破 Volume Profile 高點
            confidence += 0.15
            signal_reasons.append("價格突破成交量分佈高點")
            
        if latest['close'] < latest['bb_upper'] and latest['close'] > latest['bb_middle']:
            confidence += 0.15
            signal_reasons.append("價格在布林帶上半軌，趨勢強勁")
        
        # 計算成交量穩定性
        volume_mean = df['volume'].rolling(window=20).mean().iloc[-1]
        volume_std = df['volume'].rolling(window=20).std().iloc[-1]
        volume_stability = 1 - min(1, volume_std / volume_mean)  # 標準差/平均值 的倒數
        
        # 合約交易需要更高的信心指數
        if confidence >= 0.8:
            # 計算建議槓桿
            leverage_info = self.leverage_calculator.calculate(
                volatility=volatility,
                trend_strength=trend_strength,
                volume_stability=volume_stability
            )
            
            # 使用 ATR 計算止損和獲利價位（合約需要更嚴格的風險控制）
            stop_loss = latest['close'] - (latest['atr'] * 1.5)
            take_profit = latest['close'] + (latest['atr'] * 2)
            
            return TradeSignal(
                symbol=symbol,
                signal_type='swap_long',
                confidence=confidence,
                entry_price=latest['close'],
                stop_loss=stop_loss,
                take_profit=take_profit,
                indicators_values={
                    'atr': latest['atr'],
                    'bb_bandwidth': latest['bb_bandwidth'],
                    'volume_profile_poc': latest['poc_price'],
                    'macd': latest['macd']
                },
                description='\n'.join(signal_reasons),
                leverage_info=leverage_info
            )
        
        return None
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算所有技術指標
        
        Args:
            df: 包含 OHLCV 數據的 DataFrame
            
        Returns:
            添加了所有技術指標的 DataFrame
        """
        df = self.ema_20.calculate(df)
        df = self.ema_50.calculate(df)
        df = self.macd.calculate(df)
        df = self.bb.calculate(df)
        df = self.rsi.calculate(df)
        df = self.stoch.calculate(df)
        df = self.atr.calculate(df)
        df = self.obv.calculate(df)
        df = self.volume_profile.calculate(df)
        return df

def analyze_market(df: pd.DataFrame, symbol: str, trade_type: str = 'spot') -> Optional[TradeSignal]:
    """市場分析入口函數
    
    Args:
        df: 包含 OHLCV 數據的 DataFrame
        symbol: 交易對名稱
        trade_type: 交易類型，'spot' 或 'swap'
        
    Returns:
        如果發現交易機會，返回 TradeSignal，否則返回 None
    """
    analyzer = MarketAnalyzer()
    
    if trade_type == 'spot':
        return analyzer.analyze_spot(df, symbol)
    elif trade_type == 'swap':
        return analyzer.analyze_swap(df, symbol)
    else:
        raise ValueError(f"不支持的交易類型：{trade_type}")

# 使用示例：
if __name__ == "__main__":
    # 假設我們有一個包含 OHLCV 數據的 DataFrame
    df = pd.DataFrame()  # 這裡需要填入實際的數據
    
    # 分析現貨交易機會
    spot_signal = analyze_market(df, "BTC/USDT", "spot")
    if spot_signal:
        print("發現現貨交易機會：")
        print(f"交易對：{spot_signal.symbol}")
        print(f"信心指數：{spot_signal.confidence}")
        print(f"建議入場價：{spot_signal.entry_price}")
        print(f"止損價：{spot_signal.stop_loss}")
        print(f"獲利價：{spot_signal.take_profit}")
        print(f"信號說明：\n{spot_signal.description}")
    
    # 分析合約交易機會
    swap_signal = analyze_market(df, "BTC/USDT", "swap")
    if swap_signal:
        print("\n發現合約交易機會：")
        print(f"交易對：{swap_signal.symbol}")
        print(f"信心指數：{swap_signal.confidence}")
        print(f"建議入場價：{swap_signal.entry_price}")
        print(f"止損價：{swap_signal.stop_loss}")
        print(f"獲利價：{swap_signal.take_profit}")
        print(f"信號說明：\n{swap_signal.description}")
