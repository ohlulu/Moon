from typing import Dict, Any, List
import pandas as pd
import numpy as np
from datetime import datetime
from .base import BaseAnalyzer

class TechnicalAnalyzer(BaseAnalyzer):
    """Analyzer for technical market analysis."""
    
    def __init__(self, timeframe: str = '1d'):
        """Initialize technical analyzer."""
        super().__init__(timeframe)
        self._trend_threshold = 0.6  # Minimum strength for trend confirmation
        self._volatility_threshold = 0.2  # High volatility threshold
    
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform technical analysis."""
        try:
            indicators = data['indicators']
            signals = data['signals']
            historical_data = data.get('historical_data', [])
            
            # Analyze trend
            trend_analysis = self._analyze_trend(signals)
            
            # Analyze momentum
            momentum_analysis = self._analyze_momentum(indicators)
            
            # Analyze volatility
            volatility_analysis = self._analyze_volatility(indicators, historical_data)
            
            # Analyze support/resistance
            support_resistance = self._analyze_support_resistance(historical_data)
            
            # Generate summary
            summary = self._generate_summary(
                trend_analysis,
                momentum_analysis,
                volatility_analysis,
                support_resistance
            )
            
            return {
                'timestamp': datetime.utcnow(),
                'timeframe': self.timeframe,
                'trend': trend_analysis,
                'momentum': momentum_analysis,
                'volatility': volatility_analysis,
                'support_resistance': support_resistance,
                'summary': summary
            }
            
        except Exception as e:
            raise ValueError(f"Error in technical analysis: {str(e)}")
    
    def _analyze_trend(self, signals: Dict[str, str]) -> Dict[str, Any]:
        """Analyze market trend based on indicator signals."""
        # Count signals
        buy_signals = sum(1 for signal in signals.values() if signal == 'BUY')
        sell_signals = sum(1 for signal in signals.values() if signal == 'SELL')
        total_signals = len(signals)
        
        # Calculate trend strength
        if total_signals == 0:
            return {'direction': 'NEUTRAL', 'strength': 0, 'confidence': 0}
        
        strength = abs(buy_signals - sell_signals) / total_signals
        
        # Determine trend direction
        if buy_signals > sell_signals and strength >= self._trend_threshold:
            direction = 'BULLISH'
        elif sell_signals > buy_signals and strength >= self._trend_threshold:
            direction = 'BEARISH'
        else:
            direction = 'NEUTRAL'
        
        # Calculate confidence
        confidence = strength if direction != 'NEUTRAL' else 0
        
        return {
            'direction': direction,
            'strength': strength,
            'confidence': confidence,
            'signals': {
                'buy': buy_signals,
                'sell': sell_signals,
                'neutral': total_signals - buy_signals - sell_signals
            }
        }
    
    def _analyze_momentum(self, indicators: Dict[str, Dict]) -> Dict[str, Any]:
        """Analyze market momentum."""
        momentum_score = 0
        count = 0
        
        # Check RSI
        if 'rsi' in indicators:
            rsi = indicators['rsi']['value']
            if rsi > 70:
                momentum_score -= 1
            elif rsi < 30:
                momentum_score += 1
            count += 1
        
        # Check MACD
        if 'macd' in indicators:
            macd = indicators['macd']
            if macd['macd_line'] > macd['signal_line']:
                momentum_score += 1
            else:
                momentum_score -= 1
            count += 1
        
        # Calculate momentum strength
        if count == 0:
            return {'strength': 0, 'direction': 'NEUTRAL'}
        
        strength = abs(momentum_score) / count
        direction = 'BULLISH' if momentum_score > 0 else 'BEARISH' if momentum_score < 0 else 'NEUTRAL'
        
        return {
            'strength': strength,
            'direction': direction
        }
    
    def _analyze_volatility(
        self,
        indicators: Dict[str, Dict],
        historical_data: List[Dict]
    ) -> Dict[str, Any]:
        """Analyze market volatility."""
        # Get volatility from indicators if available
        if 'bollinger' in indicators:
            bb = indicators['bollinger']
            bandwidth = bb.get('bandwidth', 0)
            
            return {
                'level': 'HIGH' if bandwidth > self._volatility_threshold else 'LOW',
                'value': bandwidth,
                'trend': self._analyze_volatility_trend(historical_data)
            }
        
        # Calculate historical volatility if no indicators available
        if historical_data:
            df = pd.DataFrame(historical_data)
            returns = df['close'].pct_change()
            volatility = returns.std() * np.sqrt(252)  # Annualized
            
            return {
                'level': 'HIGH' if volatility > self._volatility_threshold else 'LOW',
                'value': volatility,
                'trend': self._analyze_volatility_trend(historical_data)
            }
        
        return {
            'level': 'UNKNOWN',
            'value': 0,
            'trend': 'NEUTRAL'
        }
    
    def _analyze_volatility_trend(self, historical_data: List[Dict]) -> str:
        """Analyze volatility trend."""
        if len(historical_data) < 10:
            return 'NEUTRAL'
        
        df = pd.DataFrame(historical_data)
        returns = df['close'].pct_change()
        
        # Calculate rolling volatility
        window = min(20, len(historical_data) // 2)
        vol = returns.rolling(window=window).std()
        
        if vol.iloc[-1] > vol.mean() * 1.2:
            return 'INCREASING'
        elif vol.iloc[-1] < vol.mean() * 0.8:
            return 'DECREASING'
        return 'STABLE'
    
    def _analyze_support_resistance(self, historical_data: List[Dict]) -> Dict[str, Any]:
        """Analyze support and resistance levels."""
        if not historical_data:
            return {'support': [], 'resistance': []}
        
        df = pd.DataFrame(historical_data)
        price = df['close'].iloc[-1]
        
        # Find potential levels using local min/max
        highs = df['high'].rolling(window=20, center=True).max()
        lows = df['low'].rolling(window=20, center=True).min()
        
        # Get nearby levels
        support_levels = sorted([
            level for level in lows.unique()
            if level < price and level > price * 0.9
        ])[-3:]
        
        resistance_levels = sorted([
            level for level in highs.unique()
            if level > price and level < price * 1.1
        ])[:3]
        
        return {
            'support': support_levels,
            'resistance': resistance_levels,
            'current_price': price
        }
    
    def _generate_summary(
        self,
        trend: Dict[str, Any],
        momentum: Dict[str, Any],
        volatility: Dict[str, Any],
        support_resistance: Dict[str, Any]
    ) -> str:
        """Generate analysis summary."""
        summary = []
        
        # Trend summary
        if trend['direction'] != 'NEUTRAL':
            summary.append(
                f"Market shows a {trend['direction'].lower()} trend "
                f"with {trend['strength']:.1%} strength"
            )
        else:
            summary.append("Market shows no clear trend")
        
        # Momentum summary
        if momentum['direction'] != 'NEUTRAL':
            summary.append(
                f"Momentum is {momentum['direction'].lower()} "
                f"with {momentum['strength']:.1%} strength"
            )
        
        # Volatility summary
        summary.append(
            f"Volatility is {volatility['level'].lower()} "
            f"and {volatility['trend'].lower()}"
        )
        
        # Support/Resistance summary
        price = support_resistance['current_price']
        if support_resistance['support']:
            nearest_support = max(support_resistance['support'])
            summary.append(f"Nearest support at {nearest_support:.2f}")
        if support_resistance['resistance']:
            nearest_resistance = min(support_resistance['resistance'])
            summary.append(f"Nearest resistance at {nearest_resistance:.2f}")
        
        return " | ".join(summary)
    
    def get_analysis_requirements(self) -> List[str]:
        """Get required data for analysis."""
        return ['indicators', 'signals', 'historical_data']
    
    @property
    def description(self) -> str:
        """Get analyzer description."""
        return (
            "Technical market analyzer that evaluates market conditions using "
            "technical indicators, trend analysis, momentum, volatility, and "
            "support/resistance levels."
        ) 