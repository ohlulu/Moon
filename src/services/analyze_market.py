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

class Timeframe(str, Enum):
    """Trading timeframe"""
    HOUR_6 = '6h'
    DAY_1 = '1d'

@dataclass
class AnalysisResult:
    """Analysis result for both spot and swap"""
    symbol: str
    signal_type: str  # 'spot' or 'swap_buy' or 'swap_sell'
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
        for indicator in self.indicators:
            df = indicator.calculate(df)
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
            signal_type='spot',
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
    
    def _calculate_timeframe_confidence(self, df: pd.DataFrame) -> float:
        latest = df.iloc[-1]
        confidence = 0.0
        
        # Check for NA or infinite values
        if pd.isna(latest['rsi']) or np.isinf(latest['rsi']):
            return 0.0
            
        # RSI contribution (20%)
        rsi = latest['rsi']
        if 40 <= rsi <= 60:
            confidence += 0.2
        elif (30 <= rsi < 40) or (60 < rsi <= 70):
            confidence += 0.1
        
        # MACD contribution (20%)
        if not (pd.isna(latest['macd']) or pd.isna(latest['macd_signal']) or 
               np.isinf(latest['macd']) or np.isinf(latest['macd_signal'])):
            if latest['macd'] > latest['macd_signal']:
                confidence += 0.2
        
        # Volume Profile contribution (30%)
        if not (pd.isna(latest['poc_price']) or np.isinf(latest['poc_price']) or 
               pd.isna(latest['close']) or np.isinf(latest['close'])):
            if latest['close'] > latest['poc_price']:
                confidence += 0.3
        
        # Bollinger Bands contribution (30%)
        if not (pd.isna(latest['bb_middle']) or np.isinf(latest['bb_middle']) or
               pd.isna(latest['bb_upper']) or np.isinf(latest['bb_upper'])):
            if latest['close'] > latest['bb_middle']:
                if latest['close'] < latest['bb_upper']:
                    confidence += 0.3
        
        return confidence
    
    def _calculate_entry_points(self, df_6h: pd.DataFrame, df_1d: pd.DataFrame) -> Dict[str, float]:
        latest_6h = df_6h.iloc[-1]
        
        # Validate ATR and close values
        if (pd.isna(latest_6h['atr']) or np.isinf(latest_6h['atr']) or
            pd.isna(latest_6h['close']) or np.isinf(latest_6h['close'])):
            raise ValueError("Invalid ATR or close price values")
            
        atr = latest_6h['atr']
        entry = latest_6h['close']
        
        # Ensure values are reasonable
        if atr <= 0 or entry <= 0:
            raise ValueError("ATR or entry price must be positive")
            
        stop_loss = entry - (atr * 1.5)
        take_profit = entry + (atr * 2.5)
        
        # Validate calculated values
        if stop_loss <= 0 or take_profit <= 0:
            raise ValueError("Invalid stop loss or take profit values")
            
        return {
            'entry': entry,
            'stop_loss': stop_loss,
            'take_profit': take_profit
        }
    
    def _calculate_leverage(self, df_6h: pd.DataFrame) -> float:
        """Calculate suggested leverage based on volatility"""
        latest = df_6h.iloc[-1]
        
        # Validate values
        if (pd.isna(latest['atr']) or np.isinf(latest['atr']) or
            pd.isna(latest['close']) or np.isinf(latest['close']) or
            latest['close'] <= 0):
            return 2.0  # Return conservative leverage if values are invalid
            
        atr_percent = latest['atr'] / latest['close']
        
        if atr_percent < 0.01:  # Low volatility
            return 5.0
        elif atr_percent < 0.02:  # Medium volatility
            return 3.0
        else:  # High volatility
            return 2.0
    
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
                
            expected_return = ((points['take_profit'] - points['entry']) / denominator) * leverage
            
            # Validate expected return
            if pd.isna(expected_return) or np.isinf(expected_return):
                raise ValueError("Invalid expected return value")
                
            # Determine signal type based on position
            latest_6h = df_6h.iloc[-1]
            signal_type = 'swap_buy' if latest_6h['close'] > latest_6h['bb_middle'] else 'swap_sell'
            
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
