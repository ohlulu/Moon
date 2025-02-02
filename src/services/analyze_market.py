from dataclasses import dataclass
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from enum import Enum

from src.services.indicators.ema import EMA
from src.services.indicators.macd import MACD
from src.services.indicators.rsi import RSI
from src.services.indicators.stochastic import Stochastic
from src.services.indicators.bollinger_bands import BollingerBands
from src.services.indicators.atr import ATR
from src.services.indicators.obv import OBV
from src.services.indicators.volume_profile import VolumeProfile
from src.services.leverage_calculator import LeverageCalculator, LeverageInfo

class Timeframe(str, Enum):
    """交易時間週期"""
    MINUTE_1 = '1m'
    MINUTE_5 = '5m'
    MINUTE_15 = '15m'
    MINUTE_30 = '30m'
    HOUR_1 = '1h'
    HOUR_4 = '4h'
    DAY_1 = '1d'
    WEEK_1 = '1w'

@dataclass
class TimeframeAnalysis:
    """單一時間週期分析結果"""
    timeframe: Timeframe
    confidence: float
    indicators_values: Dict
    signal_reasons: List[str]

@dataclass
class TradeSignal:
    """交易信號結果"""
    symbol: str                 # 交易對
    signal_type: str            # 信號類型：'spot_buy', 'spot_sell', 'swap_long', 'swap_short'
    confidence: float           # 綜合信心指數：0-1
    entry_price: float          # 建議入場價
    stop_loss: float            # 建議止損價
    take_profit: float          # 建議獲利價
    timeframe_analysis: Dict[Timeframe, TimeframeAnalysis]  # 各時間週期分析結果
    description: str            # 信號描述
    leverage_info: Optional[LeverageInfo] = None  # 槓桿資訊（僅用於合約交易）

class MarketAnalyzer:
    """市場分析器"""
    
    def __init__(self):
        # 初始化指標
        self._init_indicators()
        self.leverage_calculator = LeverageCalculator()
        
        # 時間週期權重配置
        self.timeframe_weights = {
            Timeframe.MINUTE_1: 0.05,
            Timeframe.MINUTE_5: 0.05,
            Timeframe.MINUTE_15: 0.10,
            Timeframe.MINUTE_30: 0.10,
            Timeframe.HOUR_1: 0.20,
            Timeframe.HOUR_4: 0.20,
            Timeframe.DAY_1: 0.20,
            Timeframe.WEEK_1: 0.10,
        }
        
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
        
    def analyze_spot(self, timeframe_data: Dict[Timeframe, pd.DataFrame], symbol: str) -> Optional[TradeSignal]:
        """分析現貨交易機會
        
        Args:
            timeframe_data: 不同時間週期的 OHLCV 數據，格式為 {Timeframe: DataFrame}
            symbol: 交易對名稱
            
        Returns:
            如果發現交易機會，返回 TradeSignal，否則返回 None
        """
        timeframe_analysis = {}
        total_confidence = 0
        weighted_entry_price = 0
        all_signal_reasons = []
        
        # 分析每個時間週期
        for timeframe, df in timeframe_data.items():
            weight = self.timeframe_weights.get(timeframe, 0.1)
            analysis = self._analyze_single_timeframe(df, timeframe)
            
            if analysis:
                timeframe_analysis[timeframe] = analysis
                total_confidence += analysis.confidence * weight
                weighted_entry_price += df.iloc[-1]['close'] * weight
                all_signal_reasons.extend([f"{timeframe.value}: {reason}" for reason in analysis.signal_reasons])
        
        # 如果總體信心指數足夠高
        if total_confidence >= 0.7:
            latest_price = timeframe_data[Timeframe.HOUR_1].iloc[-1]['close']  # 使用1小時線的最新價格
            atr = self._calculate_weighted_atr(timeframe_data)
            
            return TradeSignal(
                symbol=symbol,
                signal_type='spot_buy',
                confidence=total_confidence,
                entry_price=latest_price,
                stop_loss=latest_price - (atr * 2),
                take_profit=latest_price + (atr * 3),
                timeframe_analysis=timeframe_analysis,
                description='\n'.join(all_signal_reasons)
            )
        
        return None

    def _analyze_single_timeframe(self, df: pd.DataFrame, timeframe: Timeframe) -> Optional[TimeframeAnalysis]:
        """分析單一時間週期的數據
        
        Args:
            df: 包含 OHLCV 數據的 DataFrame
            timeframe: 時間週期
            
        Returns:
            TimeframeAnalysis 物件
        """
        df = self._calculate_indicators(df)
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        confidence = 0
        signal_reasons = []
        
        # 根據不同時間週期調整分析參數
        if timeframe in [Timeframe.MINUTE_1, Timeframe.MINUTE_5]:
            # 短時間週期更注重價格行為和成交量
            confidence += self._analyze_short_term(df, latest, prev, signal_reasons)
        elif timeframe in [Timeframe.HOUR_1, Timeframe.HOUR_4]:
            # 中期時間週期平衡考慮趨勢和動能
            confidence += self._analyze_medium_term(df, latest, prev, signal_reasons)
        else:
            # 長期時間週期更注重趨勢
            confidence += self._analyze_long_term(df, latest, prev, signal_reasons)
        
        if confidence > 0:
            return TimeframeAnalysis(
                timeframe=timeframe,
                confidence=confidence,
                indicators_values={
                    'rsi': latest['rsi'],
                    'macd': latest['macd'],
                    'bb_percent_b': latest['bb_percent_b'],
                    'volume_profile_poc': latest['poc_price']
                },
                signal_reasons=signal_reasons
            )
        
        return None

    def _analyze_short_term(self, df: pd.DataFrame, latest: pd.Series, prev: pd.Series, signal_reasons: List[str]) -> float:
        """分析短期時間週期"""
        confidence = 0
        
        # 價格動能（40%）
        if latest['rsi'] > prev['rsi'] and 40 <= latest['rsi'] <= 60:
            confidence += 0.2
            signal_reasons.append("RSI 顯示短期動能增強")
        
        if latest['macd'] > latest['macd_signal']:
            confidence += 0.2
            signal_reasons.append("MACD 短期趨勢向上")
        
        # 成交量分析（40%）
        volume_sma = df['volume'].rolling(20).mean().iloc[-1]
        if latest['volume'] > volume_sma * 1.5:
            confidence += 0.4
            signal_reasons.append("成交量明顯放大")
        
        # 價格位置（20%）
        if 0.3 <= latest['bb_percent_b'] <= 0.7:
            confidence += 0.2
            signal_reasons.append("價格在布林帶健康區間")
        
        return confidence

    def _analyze_medium_term(self, df: pd.DataFrame, latest: pd.Series, prev: pd.Series, signal_reasons: List[str]) -> float:
        """分析中期時間週期"""
        confidence = 0
        
        # 趨勢分析（40%）
        if latest['ema_20'] > latest['ema_50']:
            confidence += 0.2
            signal_reasons.append("中期趨勢向上（EMA20 > EMA50）")
            
        if latest['macd'] > 0 and latest['macd'] > latest['macd_signal']:
            confidence += 0.2
            signal_reasons.append("MACD 顯示中期上升動能")
        
        # 動能分析（30%）
        if 40 <= latest['rsi'] <= 60:
            confidence += 0.15
            signal_reasons.append("RSI 在健康區間")
            
        if latest['stoch_k'] > latest['stoch_d']:
            confidence += 0.15
            signal_reasons.append("Stochastic 顯示上升動能")
        
        # 波動性分析（30%）
        bb_width = (latest['bb_upper'] - latest['bb_lower']) / latest['bb_middle']
        if bb_width < df['bb_bandwidth'].rolling(20).mean().iloc[-1]:
            confidence += 0.3
            signal_reasons.append("布林帶收窄，可能準備突破")
        
        return confidence

    def _analyze_long_term(self, df: pd.DataFrame, latest: pd.Series, prev: pd.Series, signal_reasons: List[str]) -> float:
        """分析長期時間週期"""
        confidence = 0
        
        # 趨勢強度（50%）
        trend_strength = self._calculate_trend_strength(df)
        confidence += trend_strength * 0.5
        if trend_strength > 0.6:
            signal_reasons.append(f"強勁的長期趨勢（強度：{trend_strength:.1%}）")
        
        # 支撐位分析（30%）
        volume_profile = self.volume_profile.calculate(df)
        if latest['close'] > latest['poc_price']:
            confidence += 0.3
            signal_reasons.append("價格位於成交量分佈重心之上")
        
        # 波動性分析（20%）
        volatility = self._calculate_volatility(df)
        if volatility < 0.8:  # 相對低波動
            confidence += 0.2
            signal_reasons.append("長期波動性處於健康水平")
        
        return confidence

    def _calculate_weighted_atr(self, timeframe_data: Dict[Timeframe, pd.DataFrame]) -> float:
        """計算加權平均 ATR"""
        weighted_atr = 0
        total_weight = 0
        
        for timeframe, df in timeframe_data.items():
            if timeframe in self.timeframe_weights:
                weight = self.timeframe_weights[timeframe]
                df = self.atr.calculate(df)
                weighted_atr += df.iloc[-1]['atr'] * weight
                total_weight += weight
        
        return weighted_atr / total_weight if total_weight > 0 else 0

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
        
        # 1. 波動性評估（權重：40%）
        # 使用相對波動性評估，而不是固定閾值
        volatility = latest['atr'] / latest['close']
        volatility_rank = self._calculate_percentile(df['atr'] / df['close'], 20)  # 計算最近20根K線的波動性排名
        
        if volatility_rank < 0.7:  # 波動性不是特別高
            confidence += 0.2
            signal_reasons.append(f"波動率處於近期 {volatility_rank:.1%} 百分位")
            
        bb_width_rank = self._calculate_percentile(df['bb_bandwidth'], 20)
        if bb_width_rank < 0.3:  # 布林帶相對收窄
            confidence += 0.2
            signal_reasons.append(f"布林帶寬度處於近期 {bb_width_rank:.1%} 百分位")
        
        # 2. 趨勢評估（權重：30%）
        trend_strength = self._calculate_trend_strength(df)
        if trend_strength > 0:  # 使用相對趨勢強度
            confidence += min(0.3, trend_strength * 0.3)
            signal_reasons.append(f"趨勢強度：{trend_strength:.1%}")
        
        # 3. 價格行為評估（權重：30%）
        # 評估價格相對於近期高低點的位置
        price_position = (latest['close'] - df['low'].rolling(20).min().iloc[-1]) / \
                        (df['high'].rolling(20).max().iloc[-1] - df['low'].rolling(20).min().iloc[-1])
                        
        if 0.3 <= price_position <= 0.7:  # 價格在合理區間
            confidence += 0.15
            signal_reasons.append("價格處於近期合理區間")
            
        # 評估成交量的相對強度
        volume_sma = df['volume'].rolling(20).mean()
        volume_strength = latest['volume'] / volume_sma.iloc[-1]
        if volume_strength > 1:
            confidence += min(0.15, (volume_strength - 1) * 0.15)
            signal_reasons.append(f"成交量強度：{volume_strength:.1f}倍於平均")
        
        # 合約交易需要更高的信心指數
        if confidence >= 0.8:
            # 計算建議槓桿
            leverage_info = self.leverage_calculator.calculate(
                volatility=volatility,
                trend_strength=trend_strength,
                volume_stability=self._calculate_volume_stability(df)
            )
            
            # 使用 ATR 的相對值來設定止損和獲利價位
            atr_multiplier = 1 + (1 - confidence)  # 信心越高，倍數越小
            stop_loss = latest['close'] - (latest['atr'] * atr_multiplier)
            take_profit = latest['close'] + (latest['atr'] * atr_multiplier * 1.5)
            
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

    def _calculate_percentile(self, series: pd.Series, window: int) -> float:
        """計算數值在近期數據中的百分位數
        
        Args:
            series: 數據序列
            window: 回顧窗口大小
            
        Returns:
            百分位數（0-1）
        """
        recent_values = series.tail(window)
        current_value = series.iloc[-1]
        return (recent_values <= current_value).mean()
        
    def _calculate_volume_stability(self, df: pd.DataFrame) -> float:
        """計算成交量的穩定性
        
        Args:
            df: DataFrame 包含成交量數據
            
        Returns:
            穩定性指數（0-1）
        """
        volume = df['volume'].tail(20)
        normalized_std = volume.std() / volume.mean()
        return 1 / (1 + normalized_std)  # 使用 sigmoid-like 轉換

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

    def _calculate_volatility(self, df: pd.DataFrame) -> float:
        """計算波動性
        
        Returns:
            波動性指數（0-1）
        """
        # 實現波動性計算邏輯
        # 這裡可以根據需要實現不同的波動性計算方法
        return 0.5  # 暫時返回一個固定值

def analyze_market(timeframe_data: Dict[Timeframe, pd.DataFrame], symbol: str, trade_type: str = 'spot') -> Optional[TradeSignal]:
    """市場分析入口函數
    
    Args:
        timeframe_data: 不同時間週期的 OHLCV 數據，格式為 {Timeframe: DataFrame}
        symbol: 交易對名稱
        trade_type: 交易類型，'spot' 或 'swap'
        
    Returns:
        如果發現交易機會，返回 TradeSignal，否則返回 None
    """
    analyzer = MarketAnalyzer()
    
    if trade_type == 'spot':
        return analyzer.analyze_spot(timeframe_data, symbol)
    elif trade_type == 'swap':
        return analyzer.analyze_swap(timeframe_data, symbol)
    else:
        raise ValueError(f"不支持的交易類型：{trade_type}")

# 使用示例：
if __name__ == "__main__":
    # 假設我們有不同時間週期的數據
    timeframe_data = {
        Timeframe.HOUR_1: pd.DataFrame(),  # 1小時數據
        Timeframe.HOUR_4: pd.DataFrame(),  # 4小時數據
        Timeframe.DAY_1: pd.DataFrame(),   # 日線數據
    }
    
    # 分析現貨交易機會
    spot_signal = analyze_market(timeframe_data, "BTC/USDT", "spot")
    if spot_signal:
        print("發現現貨交易機會：")
        print(f"交易對：{spot_signal.symbol}")
        print(f"綜合信心指數：{spot_signal.confidence}")
        print(f"建議入場價：{spot_signal.entry_price}")
        print(f"止損價：{spot_signal.stop_loss}")
        print(f"獲利價：{spot_signal.take_profit}")
        print("\n各時間週期分析：")
        for timeframe, analysis in spot_signal.timeframe_analysis.items():
            print(f"\n{timeframe.value} 時間週期：")
            print(f"信心指數：{analysis.confidence}")
            print("信號說明：")
            for reason in analysis.signal_reasons:
                print(f"- {reason}")
    
    # 分析合約交易機會
    swap_signal = analyze_market(timeframe_data, "BTC/USDT", "swap")
    if swap_signal:
        print("\n發現合約交易機會：")
        print(f"交易對：{swap_signal.symbol}")
        print(f"信心指數：{swap_signal.confidence}")
        print(f"建議入場價：{swap_signal.entry_price}")
        print(f"止損價：{swap_signal.stop_loss}")
        print(f"獲利價：{swap_signal.take_profit}")
        print(f"信號說明：\n{swap_signal.description}")
