from dataclasses import dataclass
from typing import List, Dict, Optional, Protocol
from abc import ABC, abstractmethod
import pandas as pd
from enum import Enum
import numpy as np

from src.services.indicators.indicator import Indicator
from src.services.indicators.rsi import RSI
from src.services.indicators.atr import ATR
from src.services.indicators.volume_profile import VolumeProfile
from src.services.indicators.macd import MACD
from src.services.indicators.bollinger_bands import BollingerBands
from src.services.leverage_calculator import LeverageCalculator

class Timeframe(str, Enum):
    """Trading timeframe"""
    HOUR_6 = '6h'
    DAY_1 = '1d'

@dataclass
class AnalysisResult:
    """Analysis result for both spot and swap"""
    symbol: str
    signal_type: float  # -1 to 1
    confidence: float  # 0-1
    entry_price: float
    stop_loss: float
    take_profit: float
    expected_return: float
    leverage: Optional[float] = None  # Only for swap
    description: Optional[str] = None

class MarketAnalyzer(ABC):
    """Base class for market analyzers"""
    
    def __init__(self, indicators: List[Indicator]):
        self.indicators = indicators
        self.timeframe_weights = {
            Timeframe.HOUR_6: 0.4,
            Timeframe.DAY_1: 0.6
        }
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all indicators"""
        # 計算所有指標
        for indicator in self.indicators:
            df = indicator.calculate(df)
            
        # 移除初始化期間的數據點（前 30 個），這些數據點可能包含 NA 值
        df = df.iloc[60:]
        
        # 確保沒有 NA 值
        if df.isnull().values.any():
            missing_columns = df.columns[df.isnull().any()].tolist()
            raise ValueError(f"數據中存在 NA 值，影響的列：{missing_columns}")
            
        return df
    
    def _calculate_confidence(self, df_6h: pd.DataFrame, df_1d: pd.DataFrame) -> float:
        """Calculate overall confidence score"""
        confidence_6h = self._calculate_timeframe_confidence(df_6h)
        confidence_1d = self._calculate_timeframe_confidence(df_1d)
        
        return (confidence_6h * self.timeframe_weights[Timeframe.HOUR_6] +
                confidence_1d * self.timeframe_weights[Timeframe.DAY_1])
    
    @abstractmethod
    def _calculate_timeframe_confidence(self, df: pd.DataFrame) -> float:
        """Calculate confidence score for a single timeframe"""
        pass
    
    @abstractmethod
    def _calculate_entry_points(self, df_6h: pd.DataFrame, df_1d: pd.DataFrame) -> Dict[str, float]:
        """Calculate entry, stop loss and take profit prices"""
        pass
    
    @abstractmethod
    def analyze(self, symbol: str, df_6h: pd.DataFrame, df_1d: pd.DataFrame) -> AnalysisResult:
        """Analyze market data and generate trading signal"""
        pass

class SpotAnalyzerV1(MarketAnalyzer):
    """Spot market analyzer version 1"""
    
    def __init__(self):
        indicators = [
            RSI(14),
            ATR(14),
            VolumeProfile(24),
            MACD(12, 26, 9)
        ]
        super().__init__(indicators)
    
    def _calculate_timeframe_confidence(self, df: pd.DataFrame) -> float:
        # 確保使用最新的數據
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame 必須使用時間戳記作為索引")
            
        latest = df.sort_index().iloc[-1]
        
        # 檢查必要的指標是否存在
        required_indicators = ['rsi', 'macd', 'macd_signal', 'poc_price']
        for indicator in required_indicators:
            if indicator not in latest.index:
                raise ValueError(f"缺少必要的指標: {indicator}")
            if pd.isna(latest[indicator]):
                raise ValueError(f"指標 {indicator} 的值為 NA")
        
        confidence = 0.0
        
        # RSI contribution (30%)
        rsi = latest['rsi']
        if pd.isna(rsi):
            raise ValueError("RSI 值為空")
            
        if 40 <= rsi <= 60:
            confidence += 0.3
        elif (30 <= rsi < 40) or (60 < rsi <= 70):
            confidence += 0.15
        
        # MACD contribution (30%)
        if pd.isna(latest['macd']) or pd.isna(latest['macd_signal']):
            raise ValueError("MACD 或 MACD Signal 值為空")
            
        if latest['macd'] > latest['macd_signal']:
            confidence += 0.3
        
        # Volume Profile contribution (40%)
        if pd.isna(latest['poc_price']):
            raise ValueError("POC 價格值為空")
            
        if latest['close'] > latest['poc_price']:
            confidence += 0.4
        
        return confidence
    
    def _calculate_entry_points(self, df_6h: pd.DataFrame, df_1d: pd.DataFrame) -> Dict[str, float]:
        # 確保使用時間戳記索引
        if not isinstance(df_6h.index, pd.DatetimeIndex):
            raise ValueError("DataFrame 必須使用時間戳記作為索引")
            
        if len(df_6h) == 0:
            raise ValueError("6小時數據為空")
            
        latest_6h = df_6h.sort_index().iloc[-1]
        
        # 檢查 ATR 是否存在且有效
        if 'atr' not in latest_6h.index or pd.isna(latest_6h['atr']):
            raise ValueError("ATR 值無效或不存在")
        
        # 檢查收盤價是否有效
        if pd.isna(latest_6h['close']):
            raise ValueError("收盤價無效")
            
        atr = latest_6h['atr']
        entry = latest_6h['close']
        
        # 確保 ATR 不為 0 或極小值
        if atr < 0.00001:
            raise ValueError("ATR 值過小")
            
        stop_loss = entry - (atr * 2)
        take_profit = entry + (atr * 3)
        
        # 確保所有價格都是正數
        if any(price <= 0 for price in [entry, stop_loss, take_profit]):
            raise ValueError("計算出的價格包含非正數")
            
        return {
            'entry': entry,
            'stop_loss': stop_loss,
            'take_profit': take_profit
        }
    
    def analyze(self, symbol: str, df_6h: pd.DataFrame, df_1d: pd.DataFrame) -> AnalysisResult:
        # 檢查數據框是否為空
        if len(df_6h) == 0 or len(df_1d) == 0:
            raise ValueError("數據框為空")
            
        # 確保使用時間戳記索引
        for df, timeframe in [(df_6h, '6h'), (df_1d, '1d')]:
            if not isinstance(df.index, pd.DatetimeIndex):
                raise ValueError(f"{timeframe} DataFrame 必須使用時間戳記作為索引")
            
        # Calculate indicators
        try:
            df_6h = self._calculate_indicators(df_6h)
            df_1d = self._calculate_indicators(df_1d)
        except Exception as e:
            raise ValueError(f"計算指標時出錯: {str(e)}")
        
        # Calculate confidence
        confidence = self._calculate_confidence(df_6h, df_1d)
        
        # Calculate entry points
        points = self._calculate_entry_points(df_6h, df_1d)
        
        # 計算預期報酬時檢查除數不為零
        denominator = points['entry'] - points['stop_loss']
        if abs(denominator) < 0.00001:
            raise ValueError("無法計算預期報酬：入場價與止損價過於接近")
            
        expected_return = (points['take_profit'] - points['entry']) / denominator
        
        # 確保所有計算結果都在合理範圍內
        if not (0 <= confidence <= 1):
            raise ValueError(f"信心度超出範圍: {confidence}")
            
        if expected_return <= 0:
            raise ValueError(f"預期報酬為負值: {expected_return}")
        
        return AnalysisResult(
            symbol=symbol,
            signal_type=confidence,
            confidence=confidence,
            entry_price=points['entry'],
            stop_loss=points['stop_loss'],
            take_profit=points['take_profit'],
            expected_return=expected_return
        )

class SwapAnalyzerV1(MarketAnalyzer):
    """Swap market analyzer version 1"""
    
    def __init__(self):
        indicators = [
            RSI(14),
            ATR(14),
            VolumeProfile(24),
            MACD(12, 26, 9),
            BollingerBands(20, 2)
        ]
        super().__init__(indicators)
        self.leverage_calculator = LeverageCalculator()
    
    def _calculate_timeframe_confidence(self, df: pd.DataFrame) -> float:
        latest = df.iloc[-1]
        confidence = 0.0
        
        # Initialize confidence components
        rsi_confidence = 0.0
        macd_confidence = 0.0
        volume_confidence = 0.0
        bb_confidence = 0.0
        
        # RSI contribution (20%)
        if not (pd.isna(latest['rsi']) or np.isinf(latest['rsi'])):
            rsi = latest['rsi']
            if 40 <= rsi <= 60:
                rsi_confidence = 0.2
            elif (30 <= rsi < 40) or (60 < rsi <= 70):
                rsi_confidence = 0.1
            elif (20 <= rsi < 30) or (70 < rsi <= 80):
                rsi_confidence = 0.05
        
        # MACD contribution (20%)
        if not (pd.isna(latest['macd']) or pd.isna(latest['macd_signal']) or 
               np.isinf(latest['macd']) or np.isinf(latest['macd_signal'])):
            macd_diff = latest['macd'] - latest['macd_signal']
            if abs(macd_diff) > 0:  # If there's any difference
                macd_confidence = 0.2 if latest['macd'] > latest['macd_signal'] else 0.1
        
        # Volume Profile contribution (30%)
        if not (pd.isna(latest['poc_price']) or np.isinf(latest['poc_price']) or 
               pd.isna(latest['close']) or np.isinf(latest['close'])):
            price_diff = abs(latest['close'] - latest['poc_price'])
            if price_diff > 0:
                if latest['close'] > latest['poc_price']:
                    volume_confidence = 0.3
                else:
                    volume_confidence = 0.15
        
        # Bollinger Bands contribution (30%)
        if not (pd.isna(latest['bb_middle']) or np.isinf(latest['bb_middle']) or
               pd.isna(latest['bb_upper']) or np.isinf(latest['bb_upper']) or
               pd.isna(latest['bb_lower']) or np.isinf(latest['bb_lower'])):
            
            bb_range = latest['bb_upper'] - latest['bb_lower']
            if bb_range > 0:  # Ensure bands aren't collapsed
                if latest['close'] > latest['bb_middle']:
                    if latest['close'] < latest['bb_upper']:
                        bb_confidence = 0.3
                    else:
                        bb_confidence = 0.15
                else:
                    if latest['close'] > latest['bb_lower']:
                        bb_confidence = 0.15
        
        # Calculate total confidence
        confidence = rsi_confidence + macd_confidence + volume_confidence + bb_confidence
        
        # Only return 0 if ALL components are 0
        if confidence < 0.2:  # Minimum threshold for confidence
            return 0.0
            
        return confidence
    
    def _calculate_entry_points(self, df_6h: pd.DataFrame, df_1d: pd.DataFrame) -> Dict[str, float]:
        """
        Dynamic entry point calculation for crypto markets
        Considers multiple indicators and market dynamics
        """
        latest_6h = df_6h.iloc[-1]
        latest_1d = df_1d.iloc[-1]
        
        # 1. 波動性分析 (使用 ATR)
        if (pd.isna(latest_6h['atr']) or np.isinf(latest_6h['atr']) or 
            pd.isna(latest_1d['atr']) or np.isinf(latest_1d['atr'])):
            raise ValueError("Invalid ATR values")
        
        # 結合 6h 和 1d 的 ATR，但加入更複雜的權重計算
        volatility_factor = (
            latest_6h['atr'] * 0.4 + 
            latest_1d['atr'] * 0.6
        )
        
        # 2. 趨勢強度分析 (結合 MACD 和 RSI)
        if (pd.isna(latest_6h['macd']) or pd.isna(latest_6h['macd_signal']) or 
            pd.isna(latest_6h['rsi'])):
            raise ValueError("Missing MACD or RSI indicators")
        
        # MACD 趨勢強度
        macd_trend_strength = (
            1 if latest_6h['macd'] > latest_6h['macd_signal'] else -1
        )
        
        # RSI 趨勢方向
        rsi_trend_direction = (
            1 if latest_6h['rsi'] > 50 else -1
        )
        
        # 3. 成交量分析 (使用成交量分佈指標)
        if pd.isna(latest_6h['poc_price']):
            raise ValueError("Missing Volume Profile indicator")
        
        # 計算與成交量集中點的關係
        volume_alignment = (
            1 if latest_6h['close'] > latest_6h['poc_price'] else -1
        )
        
        # 4. 布林帶分析
        if (pd.isna(latest_6h['bb_middle']) or pd.isna(latest_6h['bb_upper']) or 
            pd.isna(latest_6h['bb_lower'])):
            raise ValueError("Missing Bollinger Bands indicators")
        
        # 布林帶位置
        bb_band_width = latest_6h['bb_upper'] - latest_6h['bb_lower']
        if abs(bb_band_width) < 1e-8:  # 防止除零
            bb_position = 0
        else:
            bb_position = (latest_6h['close'] - latest_6h['bb_middle']) / bb_band_width
        
        # 5. 動態入場點計算
        entry = latest_6h['close']
        
        # 根據多個指標動態調整入場點
        entry_adjustment = (
            volatility_factor * 
            macd_trend_strength * 
            rsi_trend_direction * 
            volume_alignment * 
            (1 + bb_position)  # 布林帶位置影響
        )
        
        # 加入趨勢一致性檢查
        trend_consistency = macd_trend_strength * rsi_trend_direction
        if trend_consistency < 0:  # 指標方向矛盾時降低調整幅度
            entry_adjustment *= 0.5
        
        # 在計算 entry_adjustment 時加入波動率調整
        volatility_adjusted_factor = 1 / (1 + volatility_factor**2)  # 抑制高波動時過度調整
        entry_adjustment *= volatility_adjusted_factor
        
        # 計算止損和止盈
        stop_loss = entry - abs(entry_adjustment * 1.5)
        take_profit = entry + abs(entry_adjustment * 2.5)
        
        # 確保止損和止盈在合理範圍
        if stop_loss <= 0 or take_profit <= 0:
            raise ValueError("Invalid stop loss or take profit values")
        
        return {
            'entry': entry,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
        }
    
    def _calculate_leverage(self, df_6h: pd.DataFrame) -> float:
        """Calculate suggested leverage based on volatility and trend strength"""
        latest = df_6h.iloc[-1]
        
        # Validate values
        if (pd.isna(latest['atr']) or np.isinf(latest['atr']) or
            pd.isna(latest['close']) or np.isinf(latest['close']) or
            latest['close'] <= 0):
            return 2.0  # Return conservative leverage if values are invalid
            
        # Calculate volatility
        volatility = latest['atr'] / latest['close']
        
        # Calculate trend strength based on MACD and RSI
        trend_strength = 0.5  # Default value
        if not (pd.isna(latest['macd']) or pd.isna(latest['macd_signal']) or 
               pd.isna(latest['rsi'])):
            # MACD trend component (0-0.5)
            macd_strength = 0.5 if latest['macd'] > latest['macd_signal'] else 0.0
            
            # RSI trend component (0-0.5)
            rsi = latest['rsi']
            if rsi > 60:
                rsi_strength = 0.5
            elif rsi > 50:
                rsi_strength = 0.25
            else:
                rsi_strength = 0.0
                
            trend_strength = macd_strength + rsi_strength
        
        # Use LeverageCalculator to get suggested leverage
        leverage_info = self.leverage_calculator.calculate(volatility, trend_strength)
        return float(leverage_info.suggested_leverage)
    
    def _calculate_signal_type(self, df_6h: pd.DataFrame, df_1d: pd.DataFrame) -> float:
        latest_6h = df_6h.iloc[-1]
        latest_1d = df_1d.iloc[-1]

        # 改用連續數值計算
        signal_score = 0.0
        
        # 1. 多時間框架趨勢 (權重 30%)
        daily_trend = 1 if latest_1d['close'] > latest_1d['bb_middle'] else -1
        hourly_trend = 1 if latest_6h['close'] > latest_6h['bb_middle'] else -1
        signal_score += (daily_trend * 0.15) + (hourly_trend * 0.15)

        # 2. 波動率過濾 (權重 20%)
        bb_band_width = latest_6h['bb_upper'] - latest_6h['bb_lower']
        avg_band_width = df_6h['bb_upper'].iloc[-20:].mean() - df_6h['bb_lower'].iloc[-20:].mean()
        volatility_ratio = bb_band_width / (avg_band_width + 1e-8)  # 防止除零
        signal_score += np.clip(volatility_ratio - 0.5, -0.2, 0.2)  # 波動率貢獻在 ±0.2 之間

        # 3. 成交量驗證 (權重 15%)
        volume_ratio = latest_1d['volume'] / (df_1d['volume'].rolling(14).mean().iloc[-1] + 1e-8)
        volume_factor = np.clip((volume_ratio - 1) * 0.15, -0.15, 0.15)  # 成交量貢獻在 ±0.15 之間
        signal_score += volume_factor

        # 4. 市場結構分析 (權重 25%)
        swing_highs = df_6h['high'].rolling(5, center=True).max().dropna()
        swing_lows = df_6h['low'].rolling(5, center=True).min().dropna()
        recent_high = swing_highs.iloc[-3:].max()
        recent_low = swing_lows.iloc[-3:].min()
        
        bullish_break = (latest_6h['close'] - recent_high) / recent_high  # 突破幅度
        bearish_break = (recent_low - latest_6h['close']) / recent_low
        structure_score = np.clip(bullish_break * 0.25, -0.25, 0.25) if bullish_break > 0 else np.clip(-bearish_break * 0.25, -0.25, 0.25)
        signal_score += structure_score

        # 5. 趨勢強度過濾 (權重 10%)
        macd_diff = latest_6h['macd'] - latest_6h['macd_signal']
        rsi_diff = (latest_6h['rsi'] - 50) / 50  # 正規化到 -1~1
        trend_strength = (macd_diff * 0.05) + (rsi_diff * 0.05)  # 總權重 10%
        signal_score += trend_strength

        # 最終數值處理
        final_score = np.tanh(signal_score * 2)  # 用 tanh 壓縮到 -1~1 範圍
        final_score = np.clip(final_score, -1.0, 1.0)

        # 新增異常值檢查
        if pd.isnull([latest_6h['bb_middle'], latest_1d['bb_middle']]).any():
            raise ValueError("Bollinger Bands values contain NA")

        return final_score
    
    def analyze(self, symbol: str, df_6h: pd.DataFrame, df_1d: pd.DataFrame) -> AnalysisResult:
        try:
            # Calculate indicators
            df_6h = self._calculate_indicators(df_6h)
            df_1d = self._calculate_indicators(df_1d)
            
            # Validate dataframes
            if df_6h.isnull().values.any() or df_1d.isnull().values.any():
                raise ValueError("Data contains NA values")
                
            # Calculate confidence
            confidence = self._calculate_confidence(df_6h, df_1d)
            
            # If confidence is 0, skip further calculations
            if confidence == 0:
                raise ValueError("Insufficient confidence due to invalid data")
                
            # Calculate entry points
            points = self._calculate_entry_points(df_6h, df_1d)
            
            # Calculate leverage
            leverage = self._calculate_leverage(df_6h)
            
            # Calculate expected return (adjusted for leverage)
            denominator = points['entry'] - points['stop_loss']
            if abs(denominator) < 0.00001:
                raise ValueError("Entry and stop loss prices are too close")
                
            expected_return = ((points['take_profit'] - points['entry']) / points['entry']) * leverage
            
            # Validate expected return
            if pd.isna(expected_return) or np.isinf(expected_return):
                raise ValueError("Invalid expected return value")
                
            # Determine signal type based on position
            signal_type = self._calculate_signal_type(df_6h, df_1d)
            
            return AnalysisResult(
                symbol=symbol,
                signal_type=signal_type,
                confidence=confidence,
                entry_price=points['entry'],
                stop_loss=points['stop_loss'],
                take_profit=points['take_profit'],
                expected_return=expected_return,
                leverage=leverage
            )
        except Exception as e:
            raise ValueError(f"分析失敗: {str(e)}")

# class AnalyzerFactory:
#     """Factory for creating market analyzers"""
    
#     @staticmethod
#     def create_analyzer(analyzer_type: str) -> MarketAnalyzer:
#         if analyzer_type == 'spot_v1':
#             return SpotAnalyzerV1()
#         elif analyzer_type == 'swap_v1':
#             return SwapAnalyzerV1()
#         else:
#             raise ValueError(f"Unknown analyzer type: {analyzer_type}")

# # Usage example
# if __name__ == "__main__":
#     # Create analyzers
#     spot_analyzer = AnalyzerFactory.create_analyzer('spot_v1')
#     swap_analyzer = AnalyzerFactory.create_analyzer('swap_v1')
    
#     # Example data (you would need to provide actual DataFrames)
#     df_6h = pd.DataFrame()
#     df_1d = pd.DataFrame()
    
#     # Analyze
#     spot_result = spot_analyzer.analyze("BTC/USDT", df_6h, df_1d)
#     swap_result = swap_analyzer.analyze("BTC/USDT", df_6h, df_1d)
    
#     print(f"Spot Analysis Result: {spot_result}")
#     print(f"Swap Analysis Result: {swap_result}")
