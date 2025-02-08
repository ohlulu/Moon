from dataclasses import dataclass
from typing import List, Dict, Optional
import pandas as pd
import talib
import numpy as np

from src.services.indicators.indicator import Indicator
from src.services.indicators.rsi import RSI
from src.services.indicators.atr import ATR
from src.services.indicators.volume_profile import VolumeProfile
from src.services.indicators.macd import MACD
from src.services.indicators.bollinger_bands import BollingerBands
from src.services.indicators.ichimoku import Ichimoku
from src.services.leverage_calculator import LeverageCalculator

class SwapAnalyzerV2:
    def __init__(self):
        self.indicators = [
            RSI(14),
            ATR(14),
            VolumeProfile(24),
            MACD(12, 26, 9),
            BollingerBands(20, 2),
            Ichimoku(9, 26, 52)
        ]

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        # 計算所有指標
        for indicator in self.indicators:
            df = indicator.calculate(df)
        
        """計算市場波動性指標，用於動態調整參數"""
        # 計算過去20天的波動率
        df.loc[:, 'returns'] = df['close'].pct_change()
        df.loc[:, 'volatility'] = df['returns'].rolling(window=20).std() * np.sqrt(365)
        
        # 計算過去7天的平均成交量相對於30天的變化
        df.loc[:, 'vol_ma7'] = df['volume'].rolling(window=7).mean()
        df.loc[:, 'vol_ma30'] = df['volume'].rolling(window=30).mean()
        df.loc[:, 'volume_ratio'] = df['vol_ma7'] / df['vol_ma30']
        
        return df

    def analyze_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """分析交易信號"""
        df.loc[:, 'signal'] = 0  # 1: 做多, -1: 做空, 0: 觀望
        df.loc[:, 'confidence'] = 0.0  # 信心水平 1-5
        df.loc[:, 'suggested_leverage'] = 0.0  # 修改為浮點數
        df.loc[:, 'stop_loss_pct'] = 0.0
        
        for i in range(len(df)):
            if i < 52:  # 跳過前面無法計算的數據
                continue
                
            # 獲取當前市場狀態
            current_vol = df['volatility'].iloc[i]
            volume_ratio = df['volume_ratio'].iloc[i]
            atr_pct = df['atr_pct'].iloc[i]
            
            # 根據波動性動態調整 RSI 閾值
            rsi_thresholds = self.get_dynamic_rsi_thresholds(current_vol)
            
            # 計算綜合信號
            signals = {
                'trend': self.analyze_trend(df, i),
                'momentum': self.analyze_momentum(df, i, rsi_thresholds),
                'volatility': self.analyze_volatility(df, i),
                'volume': self.analyze_volume(df, i)
            }
            
            # 根據市場狀態計算建議
            self.calculate_trading_advice(df, i, signals, current_vol, volume_ratio, atr_pct)
            
        return df

    def get_dynamic_rsi_thresholds(self, volatility: float) -> Dict[str, float]:
        """根據波動率動態調整 RSI 閾值"""
        # 高波動時期放寬 RSI 的超買超賣判斷
        base_oversold = 30
        base_overbought = 70
        
        if volatility > 1.0:  # 年化波動率超過100%
            return {
                'oversold': base_oversold - 10,
                'overbought': base_overbought + 10
            }
        elif volatility > 0.5:  # 年化波動率超過50%
            return {
                'oversold': base_oversold - 5,
                'overbought': base_overbought + 5
            }
        else:
            return {
                'oversold': base_oversold,
                'overbought': base_overbought
            }

    def analyze_trend(self, df: pd.DataFrame, index: int):
        """分析趨勢強度"""
        close = df['close'].iloc[index]
        
        # 價格相對於均線位置
        ma_short = talib.SMA(df['close'], timeperiod=10).iloc[index]
        ma_mid = talib.SMA(df['close'], timeperiod=30).iloc[index]
        ma_long = talib.SMA(df['close'], timeperiod=60).iloc[index]
        
        trend_score = 0
        
        # 多頭排列
        if close > ma_short > ma_mid > ma_long:
            trend_score = 2
        # 空頭排列
        elif close < ma_short < ma_mid < ma_long:
            trend_score = -2
        # 部分多頭
        elif close > ma_mid:
            trend_score = 1
        # 部分空頭
        elif close < ma_mid:
            trend_score = -1
            
        return trend_score

    def analyze_momentum(self, df: pd.DataFrame, index: int, rsi_thresholds):
        """分析動能"""
        momentum_score = 0
        
        # RSI
        rsi = df['rsi'].iloc[index]
        if rsi < rsi_thresholds['oversold']:
            momentum_score += 1
        elif rsi > rsi_thresholds['overbought']:
            momentum_score -= 1
            
        # MACD
        if df['macd'].iloc[index] > df['macd_signal'].iloc[index]:
            momentum_score += 1
        else:
            momentum_score -= 1
            
        return momentum_score

    def analyze_volatility(self, df: pd.DataFrame, index: int):
        """分析波動性"""
        bb_width = (df['bb_upper'].iloc[index] - df['bb_lower'].iloc[index]) / df['bb_middle'].iloc[index]
        atr_pct = df['atr_pct'].iloc[index]
        
        # 回傳波動性評分和建議的倉位大小
        if atr_pct > 5:  # 極高波動
            return {'score': 0, 'position_size': 0.3}
        elif atr_pct > 3:  # 高波動
            return {'score': 1, 'position_size': 0.5}
        else:  # 正常波動
            return {'score': 2, 'position_size': 1.0}

    def analyze_volume(self, df: pd.DataFrame, index: int):
        """分析成交量"""
        volume_ratio = df['volume_ratio'].iloc[index]
        
        if volume_ratio > 1.5:  # 成交量明顯放大
            return 2
        elif volume_ratio > 1.2:  # 成交量略微放大
            return 1
        elif volume_ratio < 0.8:  # 成交量萎縮
            return -1
        else:
            return 0

    def calculate_trading_advice(self, df: pd.DataFrame, index: int, signals, volatility, volume_ratio, atr_pct):
        """計算綜合建議"""
        # 計算綜合分數
        total_score = (
            signals['trend'] * 2 +  # 趨勢權重加倍
            signals['momentum'] +
            signals['volatility']['score'] +
            signals['volume']
        )
        
        # 根據波動性調整建議槓桿
        base_leverage = self.calculate_base_leverage(volatility)
        
        # 設置倉位和信號
        if total_score >= 4:  # 強烈做多信號
            df.loc[df.index[index], 'signal'] = 1
            df.loc[df.index[index], 'confidence'] = min(5, abs(total_score))
            df.loc[df.index[index], 'suggested_leverage'] = base_leverage
        elif total_score <= -4:  # 強烈做空信號
            df.loc[df.index[index], 'signal'] = -1
            df.loc[df.index[index], 'confidence'] = min(5, abs(total_score))
            df.loc[df.index[index], 'suggested_leverage'] = base_leverage
        
        # 設置動態止損
        df.loc[df.index[index], 'stop_loss_pct'] = self.calculate_stop_loss(atr_pct)

    def calculate_base_leverage(self, volatility):
        """根據波動率計算建議槓桿"""
        if volatility > 1.0:  # 極高波動
            return 1
        elif volatility > 0.7:  # 高波動
            return 2
        elif volatility > 0.4:  # 中等波動
            return 3
        else:  # 低波動
            return 4

    def calculate_stop_loss(self, atr_pct):
        """計算動態止損點"""
        # 根據ATR設置止損
        base_stop = atr_pct * 1.5  # 基礎止損為1.5倍ATR
        
        # 限制止損範圍
        return min(max(base_stop, 2), 10)  # 最小2%，最大10%

    def get_trading_advice(self, df: pd.DataFrame, index: int = -1):
        """獲取交易建議"""
        signal = df['signal'].iloc[index]
        confidence = df['confidence'].iloc[index]
        leverage = df['suggested_leverage'].iloc[index]
        stop_loss = df['stop_loss_pct'].iloc[index]
        
        advice = {}

        if signal == 1:
            advice.update({
                'action': '做多',
                'confidence': f'{confidence}/5',
                'leverage': f'{leverage}倍',
                'stop_loss_percentage': f'{stop_loss:.1f}%'
            })
        elif signal == -1:
            advice.update({
                'action': '做空',
                'confidence': f'{confidence}/5',
                'leverage': f'{leverage}倍',
                'stop_loss_percentage': f'{stop_loss:.1f}%'
            })
        else:
            advice.update({
                'action': '觀望',
                'reason': '無明確信號或波動過大'
            })
            
        return advice