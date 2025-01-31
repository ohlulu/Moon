import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator, ROCIndicator
from ta.volatility import BollingerBands
from ta.volume import VolumeWeightedAveragePrice

logger = logging.getLogger(__name__)

class TechnicalIndicatorCalculator:
    """Calculator for various technical indicators."""
    
    def __init__(self, historical_data: List[Dict]):
        """Initialize calculator with historical data."""
        # Convert historical data to DataFrame
        self.df = pd.DataFrame(historical_data)
        self.df.set_index('timestamp', inplace=True)
        self.df.sort_index(inplace=True)
        
        # Initialize indicators
        self._initialize_indicators()
    
    def _initialize_indicators(self):
        """Initialize all technical indicators."""
        # Moving Averages
        self.simple_moving_average_20 = SMAIndicator(close=self.df['close'], window=20)
        self.simple_moving_average_50 = SMAIndicator(close=self.df['close'], window=50)
        self.simple_moving_average_200 = SMAIndicator(close=self.df['close'], window=200)
        self.exponential_moving_average_12 = EMAIndicator(close=self.df['close'], window=12)
        self.exponential_moving_average_26 = EMAIndicator(close=self.df['close'], window=26)
        
        # MACD
        self.macd = MACD(
            close=self.df['close'],
            window_slow=26,
            window_fast=12,
            window_sign=9
        )
        
        # RSI
        self.rsi = RSIIndicator(close=self.df['close'], window=14)
        
        # Bollinger Bands
        self.bollinger = BollingerBands(close=self.df['close'], window=20, window_dev=2)
        
        # Rate of Change
        self.rate_of_change = ROCIndicator(close=self.df['close'], window=12)
        
        # Volume Weighted Average Price
        self.volume_weighted_average_price = VolumeWeightedAveragePrice(
            high=self.df['high'],
            low=self.df['low'],
            close=self.df['close'],
            volume=self.df['volume'],
            window=14
        )
    
    def calculate_all_indicators(self) -> Dict:
        """Calculate all technical indicators."""
        try:
            # Get latest values
            latest_idx = self.df.index[-1]
            
            # Calculate moving averages
            moving_averages = {
                'simple_moving_average_20': self.simple_moving_average_20.sma_indicator().iloc[-1],
                'simple_moving_average_50': self.simple_moving_average_50.sma_indicator().iloc[-1],
                'simple_moving_average_200': self.simple_moving_average_200.sma_indicator().iloc[-1],
                'exponential_moving_average_12': self.exponential_moving_average_12.ema_indicator().iloc[-1],
                'exponential_moving_average_26': self.exponential_moving_average_26.ema_indicator().iloc[-1]
            }
            
            # Calculate MACD
            macd_data = {
                'macd_line': self.macd.macd().iloc[-1],
                'signal_line': self.macd.macd_signal().iloc[-1],
                'histogram': self.macd.macd_diff().iloc[-1]
            }
            
            # Calculate RSI
            rsi_value = self.rsi.rsi().iloc[-1]
            
            # Calculate Bollinger Bands
            bollinger_bands = {
                'upper': self.bollinger.bollinger_hband().iloc[-1],
                'middle': self.bollinger.bollinger_mavg().iloc[-1],
                'lower': self.bollinger.bollinger_lband().iloc[-1]
            }
            
            # Calculate volatility
            volatility = self.calculate_volatility()
            
            # Calculate momentum
            momentum = self.rate_of_change.roc().iloc[-1]
            
            # Calculate trend strength
            trend_strength = self.calculate_trend_strength()
            
            # Generate trading signals
            signals = self.generate_trading_signals(
                rsi_value,
                macd_data,
                bollinger_bands,
                moving_averages
            )
            
            return {
                'timestamp': latest_idx,
                'moving_averages': moving_averages,
                'macd': macd_data,
                'rsi': {
                    'value': rsi_value,
                    'overbought': 70,
                    'oversold': 30
                },
                'bollinger_bands': bollinger_bands,
                'volatility': volatility,
                'momentum': momentum,
                'trend_strength': trend_strength,
                'trading_signals': signals
            }
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            raise
    
    def calculate_volatility(self) -> float:
        """Calculate price volatility."""
        try:
            # Calculate daily returns
            returns = self.df['close'].pct_change()
            
            # Calculate annualized volatility
            volatility = returns.std() * np.sqrt(252)  # 252 trading days in a year
            
            return float(volatility)
            
        except Exception as e:
            logger.error(f"Error calculating volatility: {str(e)}")
            raise
    
    def calculate_trend_strength(self) -> float:
        """Calculate trend strength indicator."""
        try:
            # Use ADX (Average Directional Index) principle
            # Simplified version using moving average relationships
            simple_moving_average_20 = self.simple_moving_average_20.sma_indicator().iloc[-1]
            simple_moving_average_50 = self.simple_moving_average_50.sma_indicator().iloc[-1]
            simple_moving_average_200 = self.simple_moving_average_200.sma_indicator().iloc[-1]
            
            # Check if moving averages are aligned
            trend_alignment = 0
            if simple_moving_average_20 > simple_moving_average_50 > simple_moving_average_200:  # Strong uptrend
                trend_alignment = 1
            elif simple_moving_average_20 < simple_moving_average_50 < simple_moving_average_200:  # Strong downtrend
                trend_alignment = -1
            
            # Calculate price momentum
            momentum = self.rate_of_change.roc().iloc[-1]
            
            # Combine factors for trend strength (0 to 1)
            strength = abs(trend_alignment * momentum / 100)
            return min(max(strength, 0), 1)  # Normalize between 0 and 1
            
        except Exception as e:
            logger.error(f"Error calculating trend strength: {str(e)}")
            raise
    
    def generate_trading_signals(
        self,
        rsi: float,
        macd: Dict,
        bollinger: Dict,
        ma: Dict
    ) -> Dict:
        """Generate trading signals based on various indicators."""
        try:
            signals = {}
            
            # RSI Signal
            if rsi > 70:
                signals['rsi'] = 'SELL'
            elif rsi < 30:
                signals['rsi'] = 'BUY'
            else:
                signals['rsi'] = 'NEUTRAL'
            
            # MACD Signal
            if macd['macd_line'] > macd['signal_line']:
                signals['macd'] = 'BUY'
            else:
                signals['macd'] = 'SELL'
            
            # Bollinger Bands Signal
            current_price = self.df['close'].iloc[-1]
            if current_price > bollinger['upper']:
                signals['bollinger'] = 'SELL'
            elif current_price < bollinger['lower']:
                signals['bollinger'] = 'BUY'
            else:
                signals['bollinger'] = 'NEUTRAL'
            
            # Moving Average Signal
            if ma['simple_moving_average_20'] > ma['simple_moving_average_50']:
                signals['ma'] = 'BUY'
            else:
                signals['ma'] = 'SELL'
            
            # Overall Signal
            buy_signals = sum(1 for signal in signals.values() if signal == 'BUY')
            sell_signals = sum(1 for signal in signals.values() if signal == 'SELL')
            
            if buy_signals > sell_signals:
                signals['overall'] = 'BUY'
            elif sell_signals > buy_signals:
                signals['overall'] = 'SELL'
            else:
                signals['overall'] = 'NEUTRAL'
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generating trading signals: {str(e)}")
            raise 