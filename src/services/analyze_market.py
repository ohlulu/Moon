from dataclasses import dataclass
from typing import List, Dict, Optional, Protocol
from abc import ABC, abstractmethod
import pandas as pd
from enum import Enum

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
        latest = df.iloc[-1]
        confidence = 0.0
        
        # RSI contribution (30%)
        rsi = latest['rsi']
        if 40 <= rsi <= 60:
            confidence += 0.3
        elif (30 <= rsi < 40) or (60 < rsi <= 70):
            confidence += 0.15
        
        # MACD contribution (30%)
        if latest['macd'] > latest['macd_signal']:
            confidence += 0.3
        
        # Volume Profile contribution (40%)
        if latest['close'] > latest['poc_price']:
            confidence += 0.4
        
        return confidence
    
    def _calculate_entry_points(self, df_6h: pd.DataFrame, df_1d: pd.DataFrame) -> Dict[str, float]:
        latest_6h = df_6h.iloc[-1]
        atr = latest_6h['atr']
        entry = latest_6h['close']
        
        return {
            'entry': entry,
            'stop_loss': entry - (atr * 2),
            'take_profit': entry + (atr * 3)
        }
    
    def analyze(self, symbol: str, df_6h: pd.DataFrame, df_1d: pd.DataFrame) -> AnalysisResult:
        # Calculate indicators
        df_6h = self._calculate_indicators(df_6h)
        df_1d = self._calculate_indicators(df_1d)
        
        # Calculate confidence
        confidence = self._calculate_confidence(df_6h, df_1d)
        
        # Calculate entry points
        points = self._calculate_entry_points(df_6h, df_1d)
        
        # Calculate expected return
        expected_return = (points['take_profit'] - points['entry']) / (points['entry'] - points['stop_loss'])
        
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
        
        # RSI contribution (20%)
        rsi = latest['rsi']
        if 40 <= rsi <= 60:
            confidence += 0.2
        elif (30 <= rsi < 40) or (60 < rsi <= 70):
            confidence += 0.1
        
        # MACD contribution (20%)
        if latest['macd'] > latest['macd_signal']:
            confidence += 0.2
        
        # Volume Profile contribution (30%)
        if latest['close'] > latest['poc_price']:
            confidence += 0.3
        
        # Bollinger Bands contribution (30%)
        if latest['close'] > latest['bb_middle']:
            if latest['close'] < latest['bb_upper']:
                confidence += 0.3
        
        return confidence
    
    def _calculate_entry_points(self, df_6h: pd.DataFrame, df_1d: pd.DataFrame) -> Dict[str, float]:
        latest_6h = df_6h.iloc[-1]
        atr = latest_6h['atr']
        entry = latest_6h['close']
        
        return {
            'entry': entry,
            'stop_loss': entry - (atr * 1.5),  # More conservative for leverage
            'take_profit': entry + (atr * 2.5)
        }
    
    def _calculate_leverage(self, df_6h: pd.DataFrame) -> float:
        """Calculate suggested leverage based on volatility"""
        latest = df_6h.iloc[-1]
        atr_percent = latest['atr'] / latest['close']
        
        if atr_percent < 0.01:  # Low volatility
            return 5.0
        elif atr_percent < 0.02:  # Medium volatility
            return 3.0
        else:  # High volatility
            return 2.0
    
    def analyze(self, symbol: str, df_6h: pd.DataFrame, df_1d: pd.DataFrame) -> AnalysisResult:
        # Calculate indicators
        df_6h = self._calculate_indicators(df_6h)
        df_1d = self._calculate_indicators(df_1d)
        
        # Calculate confidence
        confidence = self._calculate_confidence(df_6h, df_1d)
        
        # Calculate entry points
        points = self._calculate_entry_points(df_6h, df_1d)
        
        # Calculate leverage
        leverage = self._calculate_leverage(df_6h)
        
        # Calculate expected return (adjusted for leverage)
        expected_return = ((points['take_profit'] - points['entry']) / 
                         (points['entry'] - points['stop_loss'])) * leverage
        
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

def analyze_market(market: MarketModel) -> Optional[Dict]:
    """分析市場並返回分析結果
    
    Args:
        market: 要分析的市場模型
        
    Returns:
        Optional[Dict]: 分析結果，如果分析失敗則返回 None
    """
    try:
        # 創建分析器
        analyzer = SpotAnalyzerV1()
        
        # 獲取市場數據
        df_6h = market.get_klines(Timeframe.HOUR_6)
        df_1d = market.get_klines(Timeframe.DAY_1)
        
        if df_6h is None or df_1d is None or len(df_6h) < 30 or len(df_1d) < 30:
            return None
            
        # 進行分析
        result = analyzer.analyze(market.symbol, df_6h, df_1d)
        
        return {
            'confidence': result.confidence,
            'entry_price': result.entry_price,
            'stop_loss': result.stop_loss,
            'take_profit': result.take_profit,
            'expected_return': result.expected_return,
            'description': result.description
        }
        
    except Exception as e:
        print(f"Error analyzing {market.symbol}: {str(e)}")
        return None
