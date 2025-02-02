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
class TimeframeAnalysis:
    """單一時間週期分析結果"""
    timeframe: Timeframe
    market_structure: MarketStructure
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
    market_status: Dict[str, float] = None  # 市場狀態指標

class MarketAnalyzer:
    """市場分析器"""
    
    def __init__(self):
        # 初始化指標
        self._init_indicators()
        self.leverage_calculator = LeverageCalculator()
        
        # 基礎時間週期權重配置
        self.base_timeframe_weights = {
            Timeframe.HOUR_6: 0.6,  # 中期
            Timeframe.DAY_1: 0.4,   # 長期
        }
        
        # 時間週期分類
        self.timeframe_categories = {
            'medium': [Timeframe.HOUR_6],
            'long': [Timeframe.DAY_1]
        }
        
    def _init_indicators(self):
        """初始化所有技術指標"""
        # 趨勢指標
        self.ema_20 = EMA(20)
        self.ema_50 = EMA(50)
        self.ema_200 = EMA(200)  # 加入 200 均線用於確認大趨勢
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
        """根據可用的時間週期動態計算權重
        
        策略：
        1. 確保每個時間週期類別（超短期、短期、中期、長期）的總權重保持平衡
        2. 如果某個類別沒有時間週期，將權重分配給其他類別
        3. 同一類別內的時間週期平均分配權重
        
        Args:
            available_timeframes: 實際可用的時間週期列表
            
        Returns:
            動態計算後的權重字典
        """
        # 計算每個類別中可用的時間週期數量
        category_counts = {
            category: sum(1 for tf in tfs if tf in available_timeframes)
            for category, tfs in self.timeframe_categories.items()
        }
        
        # 計算基礎類別權重
        base_category_weights = {
            'ultra_short': 0.1,  # 超短期總權重
            'short': 0.2,        # 短期總權重
            'medium': 0.4,       # 中期總權重
            'long': 0.3          # 長期總權重
        }
        
        # 重新分配空類別的權重
        empty_categories = [cat for cat, count in category_counts.items() if count == 0]
        if empty_categories:
            extra_weight = sum(base_category_weights[cat] for cat in empty_categories)
            remaining_categories = [cat for cat, count in category_counts.items() if count > 0]
            
            if remaining_categories:
                weight_per_category = extra_weight / len(remaining_categories)
                for cat in remaining_categories:
                    base_category_weights[cat] += weight_per_category
        
        # 計算每個時間週期的權重
        dynamic_weights = {}
        for category, timeframes in self.timeframe_categories.items():
            category_count = category_counts[category]
            if category_count > 0:
                weight_per_timeframe = base_category_weights[category] / category_count
                for tf in timeframes:
                    if tf in available_timeframes:
                        dynamic_weights[tf] = weight_per_timeframe
        
        return dynamic_weights
        
    def analyze_spot(self, timeframe_data: Dict[Timeframe, pd.DataFrame], symbol: str) -> TradeSignal:
        """分析現貨交易機會
        
        Args:
            timeframe_data: 不同時間週期的 OHLCV 數據，格式為 {Timeframe: DataFrame}
            symbol: 交易對名稱
            
        Returns:
            TradeSignal 物件，包含完整的分析結果
        """
        # 動態計算權重
        available_timeframes = list(timeframe_data.keys())
        if not available_timeframes:
            raise ValueError("至少需要提供一個時間週期的數據")
            
        dynamic_weights = self._calculate_dynamic_weights(available_timeframes)
        
        timeframe_analysis = {}
        total_confidence = 0
        weighted_entry_price = 0
        all_signal_reasons = []
        market_status = {}
        
        # 分析每個時間週期
        for timeframe, df in timeframe_data.items():
            weight = dynamic_weights[timeframe]
            analysis = self._analyze_single_timeframe(df, timeframe)
            
            if analysis:
                timeframe_analysis[timeframe] = analysis
                total_confidence += analysis.confidence * weight
                weighted_entry_price += df.iloc[-1]['close'] * weight
                all_signal_reasons.extend([f"{timeframe.value}: {reason}" for reason in analysis.signal_reasons])
        
        # 選擇合適的時間週期來確定價格
        price_timeframe = self._select_price_timeframe(available_timeframes)
        latest_price = timeframe_data[price_timeframe].iloc[-1]['close']
        atr = self._calculate_weighted_atr(timeframe_data, dynamic_weights)
        
        # 計算市場狀態指標
        market_status = self._calculate_market_status(timeframe_data, dynamic_weights)
        
        return TradeSignal(
            symbol=symbol,
            signal_type='spot_buy',
            confidence=total_confidence,
            entry_price=latest_price,
            stop_loss=latest_price - (atr * 2),
            take_profit=latest_price + (atr * 3),
            timeframe_analysis=timeframe_analysis,
            description='\n'.join(all_signal_reasons),
            market_status=market_status
        )

    def _calculate_market_status(self, timeframe_data: Dict[Timeframe, pd.DataFrame], weights: Dict[Timeframe, float]) -> Dict[str, float]:
        """計算綜合市場狀態指標
        
        Args:
            timeframe_data: 不同時間週期的數據
            weights: 各時間週期的權重
            
        Returns:
            市場狀態指標字典，包含：
            - trend_strength: 趨勢強度（0-1）
            - volatility: 波動性（0-1）
            - volume_strength: 成交量強度（相對於20均線）
            - momentum: 動能強度（0-1）
            - support_resistance: 支撐壓力強度（0-1）
        """
        status = {
            'trend_strength': 0,
            'volatility': 0,
            'volume_strength': 0,
            'momentum': 0,
            'support_resistance': 0
        }
        
        total_weight = 0
        
        for timeframe, df in timeframe_data.items():
            if timeframe in weights:
                weight = weights[timeframe]
                df = self._calculate_indicators(df)
                latest = df.iloc[-1]
                
                # 趨勢強度
                trend_strength = self._calculate_trend_strength(df)
                status['trend_strength'] += trend_strength * weight
                
                # 波動性
                atr_volatility = latest['atr'] / latest['close']
                status['volatility'] += atr_volatility * weight
                
                # 成交量強度
                volume_sma = df['volume'].rolling(20).mean().iloc[-1]
                volume_strength = latest['volume'] / volume_sma
                status['volume_strength'] += volume_strength * weight
                
                # 動能強度
                momentum = (latest['rsi'] / 100 + 
                          (1 if latest['macd'] > latest['macd_signal'] else 0) +
                          (1 if latest['stoch_k'] > latest['stoch_d'] else 0)) / 3
                status['momentum'] += momentum * weight
                
                # 支撐壓力強度
                sr_strength = (latest['close'] - latest['bb_lower']) / (latest['bb_upper'] - latest['bb_lower'])
                status['support_resistance'] += sr_strength * weight
                
                total_weight += weight
        
        # 正規化結果
        if total_weight > 0:
            for key in status:
                status[key] = status[key] / total_weight
        
        return status

    def analyze_swap(self, timeframe_data: Dict[Timeframe, pd.DataFrame], symbol: str) -> TradeSignal:
        """分析合約交易機會
        
        Args:
            timeframe_data: 不同時間週期的 OHLCV 數據
            symbol: 交易對名稱
            
        Returns:
            TradeSignal 物件，包含完整的分析結果
        """
        # 使用與現貨相同的分析邏輯，但增加槓桿計算
        signal = self.analyze_spot(timeframe_data, symbol)
        
        # 計算建議槓桿
        market_status = signal.market_status
        leverage_info = self.leverage_calculator.calculate(
            volatility=market_status['volatility'],
            trend_strength=market_status['trend_strength'],
            volume_stability=market_status['volume_strength']
        )
        
        # 更新信號類型和槓桿信息
        signal.signal_type = 'swap_long'
        signal.leverage_info = leverage_info
        
        return signal

    def _calculate_confidence_threshold(self, available_timeframes: List[Timeframe]) -> float:
        """根據可用的時間週期計算信心指數閾值
        
        策略：
        1. 基礎閾值為 0.7
        2. 如果只有短期時間週期，提高閾值
        3. 如果有多個時間週期確認，可以適當降低閾值
        
        Args:
            available_timeframes: 可用的時間週期列表
            
        Returns:
            信心指數閾值
        """
        base_threshold = 0.7
        
        # 檢查時間週期分佈
        has_short_term = any(tf in self.timeframe_categories['ultra_short'] + self.timeframe_categories['short'] 
                           for tf in available_timeframes)
        has_medium_term = any(tf in self.timeframe_categories['medium'] for tf in available_timeframes)
        has_long_term = any(tf in self.timeframe_categories['long'] for tf in available_timeframes)
        
        # 調整閾值
        if len(available_timeframes) == 1:
            # 單一時間週期需要更高的確信度
            return base_threshold + 0.1
        elif has_short_term and not (has_medium_term or has_long_term):
            # 只有短期時間週期時提高閾值
            return base_threshold + 0.05
        elif has_long_term and has_medium_term and has_short_term:
            # 多個時間週期確認時可以稍微降低閾值
            return base_threshold - 0.05
            
        return base_threshold

    def _select_price_timeframe(self, available_timeframes: List[Timeframe]) -> Timeframe:
        """選擇用於確定價格的時間週期
        
        策略：優先選擇 6 小時線，其次是日線
        
        Args:
            available_timeframes: 可用的時間週期列表
            
        Returns:
            選擇的時間週期
        """
        # 優先順序：6H > 1D
        priority_order = [
            Timeframe.HOUR_6,
            Timeframe.DAY_1
        ]
        
        for tf in priority_order:
            if tf in available_timeframes:
                return tf
                
        # 如果沒有匹配的，返回第一個可用的時間週期
        return available_timeframes[0]

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

    def _get_timeframe_multiplier(self, timeframe: Timeframe) -> float:
        """獲取時間週期的乘數，用於調整不同時間週期的 ATR
        
        Args:
            timeframe: 時間週期
            
        Returns:
            調整乘數
        """
        # 基於時間週期的平方根來調整，這樣較大的時間週期會有較大的影響
        multipliers = {
            Timeframe.HOUR_6: 18.974,   # sqrt(360)
            Timeframe.DAY_1: 24.495,    # sqrt(600)
        }
        return multipliers.get(timeframe, 1.0)

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
        if timeframe == Timeframe.HOUR_6:
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

    def _analyze_market_structure(self, df: pd.DataFrame, timeframe: Timeframe) -> MarketStructure:
        """分析市場結構
        
        Args:
            df: OHLCV 數據
            timeframe: 時間週期
            
        Returns:
            MarketStructure 物件
        """
        df = self._calculate_indicators(df)
        latest = df.iloc[-1]
        
        # 1. 趨勢方向判斷
        ema_20 = latest['ema_20']
        ema_50 = latest['ema_50']
        ema_200 = latest['ema_200']
        
        if ema_20 > ema_50 > ema_200:
            trend_direction = 'uptrend'
        elif ema_20 < ema_50 < ema_200:
            trend_direction = 'downtrend'
        else:
            trend_direction = 'sideways'
        
        # 2. 趨勢強度計算
        trend_strength = self._calculate_trend_strength(df)
        
        # 3. 關鍵價格水平
        key_levels = self._identify_key_levels(df)
        
        # 4. 形態識別
        pattern_type = self._identify_pattern(df)
        
        # 5. 風險報酬比計算
        risk_reward_ratio = self._calculate_risk_reward_ratio(df, key_levels)
        
        return MarketStructure(
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            key_levels=key_levels,
            pattern_type=pattern_type,
            risk_reward_ratio=risk_reward_ratio
        )

    def _identify_key_levels(self, df: pd.DataFrame) -> Dict[str, float]:
        """識別關鍵價格水平"""
        latest = df.iloc[-1]
        
        # 計算支撐位和阻力位
        support = min(latest['bb_lower'], latest['poc_price'])
        resistance = max(latest['bb_upper'], df['high'].rolling(20).max().iloc[-1])
        
        # 計算重要的移動平均線
        moving_averages = {
            'ema_20': latest['ema_20'],
            'ema_50': latest['ema_50'],
            'ema_200': latest['ema_200']
        }
        
        return {
            'support': support,
            'resistance': resistance,
            'moving_averages': moving_averages,
            'volume_poc': latest['poc_price']
        }

    def _identify_pattern(self, df: pd.DataFrame) -> str:
        """識別價格形態"""
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 這裡可以實現更複雜的形態識別邏輯
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
        
        # 使用 ATR 的倍數來設定止損和目標價
        potential_loss = 2 * atr
        potential_gain = 3 * atr
        
        return potential_gain / potential_loss if potential_loss > 0 else 0

    def _combine_analysis(self, h6_structure: MarketStructure, d1_structure: MarketStructure) -> Dict[str, float]:
        """綜合分析兩個時間週期的結果"""
        return {
            'trend_strength': (h6_structure.trend_strength * 0.6 + d1_structure.trend_strength * 0.4),
            'volatility': self._calculate_volatility_score(h6_structure, d1_structure),
            'momentum': self._calculate_momentum_score(h6_structure, d1_structure),
            'support_resistance': self._calculate_sr_score(h6_structure, d1_structure),
            'risk_reward': (h6_structure.risk_reward_ratio * 0.6 + d1_structure.risk_reward_ratio * 0.4)
        }

    def _determine_signal_type(self, h6_structure: MarketStructure, d1_structure: MarketStructure) -> str:
        """根據市場結構決定信號類型"""
        # 如果兩個時間週期都是上升趨勢
        if (h6_structure.trend_direction == 'uptrend' and 
            d1_structure.trend_direction == 'uptrend'):
            return 'spot_buy'
        # 如果兩個時間週期都是下降趨勢
        elif (h6_structure.trend_direction == 'downtrend' and 
              d1_structure.trend_direction == 'downtrend'):
            return 'spot_sell'
        # 如果趨勢不一致，以日線為主
        else:
            return 'spot_buy' if d1_structure.trend_direction == 'uptrend' else 'spot_sell'

    def _calculate_trade_levels(self, entry_price: float, h6_levels: Dict[str, float], 
                              d1_levels: Dict[str, float]) -> Tuple[float, float]:
        """計算交易水平"""
        # 使用兩個時間週期的支撐位作為止損
        stop_loss = max(h6_levels['support'], d1_levels['support'])
        
        # 使用兩個時間週期的阻力位作為獲利目標
        take_profit = min(h6_levels['resistance'], d1_levels['resistance'])
        
        return stop_loss, take_profit

    def _get_indicator_values(self, df: pd.DataFrame) -> Dict:
        """獲取指標值"""
        latest = df.iloc[-1]
        return {
            'rsi': latest['rsi'],
            'macd': latest['macd'],
            'bb_percent_b': latest['bb_percent_b'],
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

def analyze_market(timeframe_data: Dict[Timeframe, pd.DataFrame], symbol: str, trade_type: str = 'spot') -> TradeSignal:
    """市場分析入口函數
    
    Args:
        timeframe_data: 不同時間週期的 OHLCV 數據，格式為 {Timeframe: DataFrame}
        symbol: 交易對名稱
        trade_type: 交易類型，'spot' 或 'swap'
        
    Returns:
        TradeSignal 物件，包含完整的分析結果
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
        Timeframe.HOUR_6: pd.DataFrame(),  # 6小時數據
        Timeframe.DAY_1: pd.DataFrame(),   # 日線數據
    }
    
    # 分析現貨交易機會
    spot_signal = analyze_market(timeframe_data, "BTC/USDT", "spot")
    print("現貨市場分析結果：")
    print(f"交易對：{spot_signal.symbol}")
    print(f"綜合信心指數：{spot_signal.confidence:.2%}")
    print(f"建議入場價：{spot_signal.entry_price}")
    print(f"止損價：{spot_signal.stop_loss}")
    print(f"獲利價：{spot_signal.take_profit}")
    
    print("\n市場狀態指標：")
    for key, value in spot_signal.market_status.items():
        print(f"{key}: {value:.2%}")
    
    print("\n各時間週期分析：")
    for timeframe, analysis in spot_signal.timeframe_analysis.items():
        print(f"\n{timeframe.value} 時間週期：")
        print(f"信心指數：{analysis.confidence:.2%}")
        print("信號說明：")
        for reason in analysis.signal_reasons:
            print(f"- {reason}")
    
    # 分析合約交易機會
    swap_signal = analyze_market(timeframe_data, "BTC/USDT", "swap")
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
