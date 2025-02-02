from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
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
    HOUR_6 = '6h'
    DAY_1 = '1d'

@dataclass
class MarketStructure:
    """市場結構分析結果"""
    trend_direction: str        # 'uptrend', 'downtrend', 'sideways'
    trend_strength: float       # 趨勢強度 0-1
    key_levels: Dict[str, float] # 關鍵價格水平
    pattern_type: str          # 形態類型
    risk_reward_ratio: float   # 風險報酬比

@dataclass
class TradeSignal:
    """交易信號結果"""
    symbol: str                 # 交易對
    signal_type: str            # 信號類型：'spot' 或 'swap'
    confidence: float           # 綜合信心指數：0-1
    entry_price: float          # 建議入場價
    stop_loss: float            # 建議止損價
    take_profit: float          # 建議獲利價
    description: str            # 信號描述
    leverage_info: Optional[LeverageInfo] = None  # 槓桿資訊（僅用於合約交易）
    market_status: Dict[str, float] = None  # 市場狀態指標

class MarketAnalyzer:
    """市場分析器"""
    
    # Constants
    BASE_CONFIDENCE_THRESHOLD = 0.7
    HOUR_6_WEIGHT = 0.6
    DAY_1_WEIGHT = 0.4
    ATR_MULTIPLIER_6H = 18.974
    ATR_MULTIPLIER_1D = 24.495
    
    # Indicator parameters
    RSI_OVERBOUGHT = 70
    RSI_OVERSOLD = 30
    RSI_NEUTRAL_HIGH = 60
    RSI_NEUTRAL_LOW = 40
    
    def __init__(self):
        # 初始化指標
        self._init_indicators()
        self.leverage_calculator = LeverageCalculator()
    
    def _init_indicators(self):
        """初始化所有技術指標"""
        # 趨勢指標
        self.ema_20 = EMA(20)
        self.ema_50 = EMA(50)
        self.ema_200 = EMA(200)
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

    def _calculate_dynamic_weights(self, available_timeframes: List[Timeframe]) -> Dict[Timeframe, float]:
        """根據可用的時間週期動態計算權重"""
        if len(available_timeframes) == 2:
            return {
                Timeframe.HOUR_6: self.HOUR_6_WEIGHT,
                Timeframe.DAY_1: self.DAY_1_WEIGHT
            }
        elif len(available_timeframes) == 1:
            return {available_timeframes[0]: 1.0}
        
        raise ValueError("至少需要提供一個時間週期的數據")

    def _select_price_timeframe(self, available_timeframes: List[Timeframe]) -> Timeframe:
        """選擇用於確定價格的時間週期"""
        return Timeframe.HOUR_6 if Timeframe.HOUR_6 in available_timeframes else Timeframe.DAY_1

    def _get_timeframe_multiplier(self, timeframe: Timeframe) -> float:
        """獲取時間週期的乘數"""
        return {
            Timeframe.HOUR_6: self.ATR_MULTIPLIER_6H,
            Timeframe.DAY_1: self.ATR_MULTIPLIER_1D
        }[timeframe]

    def _calculate_confidence_threshold(self, available_timeframes: List[Timeframe]) -> float:
        """根據可用的時間週期計算信心指數閾值"""
        if len(available_timeframes) == 1:
            return self.BASE_CONFIDENCE_THRESHOLD + 0.1
        elif all(tf in available_timeframes for tf in [Timeframe.HOUR_6, Timeframe.DAY_1]):
            return self.BASE_CONFIDENCE_THRESHOLD - 0.05
            
        return self.BASE_CONFIDENCE_THRESHOLD

    def analyze_spot(self, symbol: str, timeframe_data: Dict[Timeframe, pd.DataFrame]) -> TradeSignal:
        """分析現貨交易機會"""
        available_timeframes = list(timeframe_data.keys())
        if not available_timeframes:
            raise ValueError("至少需要提供一個時間週期的數據")
            
        dynamic_weights = self._calculate_dynamic_weights(available_timeframes)
        
        total_confidence = 0
        all_signal_reasons = []
        market_structures = {}
        
        # 分析每個時間週期
        for timeframe, df in timeframe_data.items():
            weight = dynamic_weights[timeframe]
            df = self._calculate_indicators(df)
            
            # 分析市場結構
            market_structure = self._analyze_market_structure(df)
            if market_structure:
                market_structures[timeframe] = market_structure
                
                # 計算信心指數
                confidence = self._calculate_timeframe_confidence(df, timeframe)
                total_confidence += confidence * weight
                
                # 生成信號原因
                reasons = self._generate_signal_reasons(market_structure)
                all_signal_reasons.extend([f"{timeframe.value}: {reason}" for reason in reasons])
        
        # 選擇合適的時間週期來確定價格
        price_timeframe = self._select_price_timeframe(available_timeframes)
        latest_price = timeframe_data[price_timeframe].iloc[-1]['close']
        atr = self._calculate_weighted_atr(timeframe_data, dynamic_weights)
        
        # 計算市場狀態指標
        market_status = self._calculate_market_status(timeframe_data, dynamic_weights)
        
        # 決定信號類型
        signal_type = 'spot'
        
        return TradeSignal(
            symbol=symbol,
            signal_type=signal_type,
            confidence=total_confidence,
            entry_price=latest_price,
            stop_loss=latest_price - (atr * 2),
            take_profit=latest_price + (atr * 3),
            description='\n'.join(all_signal_reasons),
            market_status=market_status
        )

    def _calculate_timeframe_confidence(self, df: pd.DataFrame, timeframe: Timeframe) -> float:
        """計算單一時間週期的信心指數"""
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        if timeframe == Timeframe.HOUR_6:
            return self._analyze_medium_term(df, latest, prev)
        else:  # Timeframe.DAY_1
            return self._analyze_long_term(df, latest, prev)

    def _analyze_medium_term(self, df: pd.DataFrame, latest: pd.Series, prev: pd.Series) -> float:
        """分析中期（6小時）時間週期"""
        confidence = 0
        
        # 趨勢分析（40%）
        if latest['ema_20'] > latest['ema_50']:
            confidence += 0.2
            
        if latest['macd'] > 0 and latest['macd'] > latest['macd_signal']:
            confidence += 0.2
        
        # 動能分析（30%）
        if self.RSI_NEUTRAL_LOW <= latest['rsi'] <= self.RSI_NEUTRAL_HIGH:
            confidence += 0.15
            
        if latest['stoch_k'] > latest['stoch_d']:
            confidence += 0.15
        
        # 波動性分析（30%）
        bb_width = (latest['bb_upper'] - latest['bb_lower']) / latest['bb_middle']
        if bb_width < df['bb_bandwidth'].rolling(20).mean().iloc[-1]:
            confidence += 0.3
        
        return confidence

    def _analyze_long_term(self, df: pd.DataFrame, latest: pd.Series, prev: pd.Series) -> float:
        """分析長期（日線）時間週期"""
        confidence = 0
        
        # 趨勢強度（50%）
        trend_strength = self._calculate_trend_strength(df)
        confidence += trend_strength * 0.5
        
        # 支撐位分析（30%）
        if latest['close'] > latest['poc_price']:
            confidence += 0.3
        
        # 波動性分析（20%）
        volatility = self._calculate_volatility(df)
        if volatility < 0.8:  # 相對低波動
            confidence += 0.2
        
        return confidence

    def analyze_swap(self, symbol: str, timeframe_data: Dict[Timeframe, pd.DataFrame]) -> TradeSignal:
        """分析合約交易機會"""
        signal = self.analyze_spot(symbol, timeframe_data)
        
        # 計算建議槓桿
        market_status = signal.market_status
        leverage_info = self.leverage_calculator.calculate(
            volatility=market_status['volatility'],
            trend_strength=market_status['trend_strength'],
            volume_stability=market_status['volume_strength']
        )
        
        # 更新信號類型和槓桿信息
        signal.signal_type = 'swap'
        signal.leverage_info = leverage_info
        
        return signal

    def _calculate_weighted_atr(self, timeframe_data: Dict[Timeframe, pd.DataFrame], weights: Dict[Timeframe, float]) -> float:
        """計算加權平均 ATR
        
        Args:
            timeframe_data: 不同時間週期的數據
            weights: 各時間週期的權重
            
        Returns:
            加權平均 ATR
        """
        weighted_atr = 0
        total_weight = 0
        
        for timeframe, df in timeframe_data.items():
            if timeframe in weights:
                weight = weights[timeframe]
                df = self.atr.calculate(df)
                # 根據時間週期調整 ATR
                timeframe_multiplier = self._get_timeframe_multiplier(timeframe)
                weighted_atr += df.iloc[-1]['atr'] * weight * timeframe_multiplier
                total_weight += weight
        
        return weighted_atr / total_weight if total_weight > 0 else 0

    def _analyze_market_structure(self, df: pd.DataFrame) -> MarketStructure:
        """分析市場結構"""
        latest = df.iloc[-1]
        
        # 趨勢方向判斷
        trend_direction = self._determine_trend_direction(df)
        
        # 趨勢強度計算
        trend_strength = self._calculate_trend_strength(df)
        
        # 關鍵價格水平
        key_levels = {
            'support': min(latest['bb_lower'], latest['poc_price']),
            'resistance': max(latest['bb_upper'], df['high'].rolling(20).max().iloc[-1]),
            'ema_20': latest['ema_20'],
            'ema_50': latest['ema_50']
        }
        
        # 形態識別
        pattern_type = self._identify_pattern(df)
        
        # 風險報酬比計算
        risk_reward_ratio = self._calculate_risk_reward_ratio(df, key_levels)
        
        return MarketStructure(
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            key_levels=key_levels,
            pattern_type=pattern_type,
            risk_reward_ratio=risk_reward_ratio
        )

    def _determine_trend_direction(self, df: pd.DataFrame) -> str:
        """判斷趨勢方向"""
        latest = df.iloc[-1]
        
        if latest['ema_20'] > latest['ema_50']:
            return 'uptrend'
        elif latest['ema_20'] < latest['ema_50']:
            return 'downtrend'
        else:
            return 'sideways'

    def _identify_pattern(self, df: pd.DataFrame) -> str:
        """識別價格形態"""
        latest = df.iloc[-1]
        
        if latest['close'] > latest['bb_upper']:
            return 'overbought'
        elif latest['close'] < latest['bb_lower']:
            return 'oversold'
        elif latest['bb_bandwidth'] < df['bb_bandwidth'].rolling(20).mean().iloc[-1]:
            return 'consolidation'
        else:
            return 'neutral'

    def _calculate_risk_reward_ratio(self, df: pd.DataFrame, key_levels: Dict[str, float]) -> float:
        """計算風險報酬比"""
        latest = df.iloc[-1]
        atr = latest['atr']
        
        potential_loss = 2 * atr
        potential_gain = 3 * atr
        
        return potential_gain / potential_loss if potential_loss > 0 else 0

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

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算所有技術指標"""
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

    def _get_indicator_values(self, df: pd.DataFrame) -> Dict:
        """獲取指標值"""
        latest = df.iloc[-1]
        return {
            'rsi': latest['rsi'],
            'macd': latest['macd'],
            'bb_percent_b': (latest['close'] - latest['bb_lower']) / (latest['bb_upper'] - latest['bb_lower']),
            'volume_profile_poc': latest['poc_price']
        }

    def _generate_signal_reasons(self, structure: MarketStructure) -> List[str]:
        """生成信號原因"""
        reasons = []
        
        if structure.trend_direction == 'uptrend':
            reasons.append(f"趨勢向上（強度：{structure.trend_strength:.1%}）")
        elif structure.trend_direction == 'downtrend':
            reasons.append(f"趨勢向下（強度：{structure.trend_strength:.1%}）")
        
        reasons.append(f"形態：{structure.pattern_type}")
        reasons.append(f"風險報酬比：{structure.risk_reward_ratio:.2f}")
        
        return reasons

# 使用示例：
if __name__ == "__main__":
    # 假設我們有不同時間週期的數據
    timeframe_data = {
        Timeframe.HOUR_6: pd.DataFrame(),  # 6小時數據
        Timeframe.DAY_1: pd.DataFrame(),   # 日線數據
    }

    analyzer = MarketAnalyzer()
    
    # 分析現貨交易機會
    spot_signal = analyzer.analyze_spot("BTC/USDT", timeframe_data)
    print("現貨市場分析結果：")
    print(f"交易對：{spot_signal.symbol}")
    print(f"綜合信心指數：{spot_signal.confidence:.2%}")
    print(f"建議入場價：{spot_signal.entry_price}")
    print(f"止損價：{spot_signal.stop_loss}")
    print(f"獲利價：{spot_signal.take_profit}")
    
    print("\n市場狀態指標：")
    for key, value in spot_signal.market_status.items():
        print(f"{key}: {value:.2%}")
    
    # 分析合約交易機會
    swap_signal = analyzer.analyze_swap("BTC/USDT", timeframe_data)
    print("\n合約市場分析結果：")
    print(f"交易對：{swap_signal.symbol}")
    print(f"綜合信心指數：{swap_signal.confidence:.2%}")
    print(f"建議入場價：{swap_signal.entry_price}")
    print(f"止損價：{swap_signal.stop_loss}")
    print(f"獲利價：{swap_signal.take_profit}")
    print(f"建議槓桿倍數：{swap_signal.leverage_info.leverage}x")
    
    print("\n市場狀態指標：")
    for key, value in swap_signal.market_status.items():
        print(f"{key}: {value:.2%}")
