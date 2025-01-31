from typing import Dict, Any, List
import pandas as pd
import numpy as np
from datetime import datetime
from .base import BaseAnalyzer

class RiskAnalyzer(BaseAnalyzer):
    """Analyzer for comprehensive market risk assessment."""
    
    def __init__(self, timeframe: str = '1d'):
        """Initialize risk analyzer."""
        super().__init__(timeframe)
        # Risk thresholds
        self._volatility_risk_threshold = 0.2
        self._liquidity_risk_threshold = 1000000  # Min daily volume
        self._concentration_risk_threshold = 0.25  # Max single holder percentage
        self._correlation_risk_threshold = 0.7
        
    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform risk analysis."""
        try:
            market_data = data.get('market_data', {})
            historical_data = data.get('historical_data', [])
            order_book = data.get('order_book', {})
            holder_data = data.get('holder_data', {})
            correlation_data = data.get('correlation_data', {})
            
            # Analyze different risk components
            volatility_risk = self._analyze_volatility_risk(historical_data)
            liquidity_risk = self._analyze_liquidity_risk(order_book, market_data)
            market_risk = self._analyze_market_risk(market_data, historical_data)
            concentration_risk = self._analyze_concentration_risk(holder_data)
            correlation_risk = self._analyze_correlation_risk(correlation_data)
            
            # Calculate overall risk score
            overall_risk = self._calculate_overall_risk(
                volatility_risk,
                liquidity_risk,
                market_risk,
                concentration_risk,
                correlation_risk
            )
            
            # Generate summary
            summary = self._generate_summary(
                overall_risk,
                volatility_risk,
                liquidity_risk,
                market_risk,
                concentration_risk,
                correlation_risk
            )
            
            return {
                'timestamp': datetime.utcnow(),
                'timeframe': self.timeframe,
                'overall_risk': overall_risk,
                'components': {
                    'volatility_risk': volatility_risk,
                    'liquidity_risk': liquidity_risk,
                    'market_risk': market_risk,
                    'concentration_risk': concentration_risk,
                    'correlation_risk': correlation_risk
                },
                'summary': summary
            }
            
        except Exception as e:
            raise ValueError(f"Error in risk analysis: {str(e)}")
    
    def _analyze_volatility_risk(self, historical_data: List[Dict]) -> Dict[str, Any]:
        """Analyze volatility-based risk."""
        if not historical_data:
            return {'score': 0, 'level': 'UNKNOWN', 'factors': []}
        
        df = pd.DataFrame(historical_data)
        returns = df['close'].pct_change().dropna()
        
        # Calculate various volatility metrics
        daily_volatility = returns.std()
        annualized_volatility = daily_volatility * np.sqrt(252)
        
        # Calculate Value at Risk (VaR)
        value_at_risk_95 = returns.quantile(0.05)
        value_at_risk_99 = returns.quantile(0.01)
        
        # Determine risk level
        if annualized_volatility > self._volatility_risk_threshold:
            risk_level = 'HIGH'
            risk_score = min(1.0, annualized_volatility / self._volatility_risk_threshold)
        else:
            risk_level = 'LOW'
            risk_score = annualized_volatility / self._volatility_risk_threshold
        
        return {
            'score': risk_score,
            'level': risk_level,
            'metrics': {
                'daily_volatility': daily_volatility,
                'annualized_volatility': annualized_volatility,
                'value_at_risk_95': value_at_risk_95,
                'value_at_risk_99': value_at_risk_99
            }
        }
    
    def _analyze_liquidity_risk(
        self,
        order_book: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze liquidity-based risk."""
        daily_volume = market_data.get('volume_24h', 0)
        
        # Analyze order book depth
        bid_depth = sum(float(bid['amount']) for bid in order_book.get('bids', []))
        ask_depth = sum(float(ask['amount']) for ask in order_book.get('asks', []))
        total_depth = bid_depth + ask_depth
        
        # Calculate bid-ask spread
        best_bid = float(order_book.get('bids', [{'price': 0}])[0]['price'])
        best_ask = float(order_book.get('asks', [{'price': 0}])[0]['price'])
        spread = (best_ask - best_bid) / best_bid if best_bid > 0 else 0
        
        # Determine risk level
        if daily_volume < self._liquidity_risk_threshold:
            risk_level = 'HIGH'
            risk_score = min(1.0, self._liquidity_risk_threshold / daily_volume)
        else:
            risk_level = 'LOW'
            risk_score = daily_volume / self._liquidity_risk_threshold
            
        return {
            'score': risk_score,
            'level': risk_level,
            'metrics': {
                'daily_volume': daily_volume,
                'order_book_depth': total_depth,
                'bid_ask_spread': spread
            }
        }
    
    def _analyze_market_risk(
        self,
        market_data: Dict[str, Any],
        historical_data: List[Dict]
    ) -> Dict[str, Any]:
        """Analyze market-based risk."""
        # Calculate market cap and dominance
        market_cap = market_data.get('market_cap', 0)
        market_dominance = market_data.get('market_dominance', 0)
        
        # Calculate price momentum
        if historical_data:
            df = pd.DataFrame(historical_data)
            current_price = df['close'].iloc[-1]
            sma_50 = df['close'].rolling(window=50).mean().iloc[-1]
            price_momentum = (current_price - sma_50) / sma_50
        else:
            price_momentum = 0
        
        # Calculate risk score based on multiple factors
        risk_factors = []
        risk_score = 0
        
        if market_cap < 1000000:  # Small cap
            risk_factors.append('small_market_cap')
            risk_score += 0.3
            
        if market_dominance < 0.001:  # Low market dominance
            risk_factors.append('low_market_dominance')
            risk_score += 0.2
            
        if abs(price_momentum) > 0.2:  # High momentum
            risk_factors.append('high_price_momentum')
            risk_score += 0.2
        
        risk_level = 'HIGH' if risk_score > 0.5 else 'MEDIUM' if risk_score > 0.3 else 'LOW'
        
        return {
            'score': min(1.0, risk_score),
            'level': risk_level,
            'factors': risk_factors,
            'metrics': {
                'market_cap': market_cap,
                'market_dominance': market_dominance,
                'price_momentum': price_momentum
            }
        }
    
    def _analyze_concentration_risk(self, holder_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze holder concentration risk."""
        holders = holder_data.get('holders', [])
        total_supply = holder_data.get('total_supply', 0)
        
        if not holders or total_supply == 0:
            return {'score': 0, 'level': 'UNKNOWN', 'factors': []}
        
        # Calculate concentration metrics
        top_holder_share = holders[0]['amount'] / total_supply if holders else 0
        top_10_share = sum(h['amount'] for h in holders[:10]) / total_supply
        
        risk_factors = []
        risk_score = 0
        
        if top_holder_share > self._concentration_risk_threshold:
            risk_factors.append('high_top_holder_concentration')
            risk_score += 0.4
            
        if top_10_share > 0.5:  # More than 50% held by top 10
            risk_factors.append('high_top_10_concentration')
            risk_score += 0.3
        
        risk_level = 'HIGH' if risk_score > 0.5 else 'MEDIUM' if risk_score > 0.3 else 'LOW'
        
        return {
            'score': min(1.0, risk_score),
            'level': risk_level,
            'factors': risk_factors,
            'metrics': {
                'top_holder_share': top_holder_share,
                'top_10_share': top_10_share
            }
        }
    
    def _analyze_correlation_risk(self, correlation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze correlation-based risk."""
        correlations = correlation_data.get('correlations', {})
        
        if not correlations:
            return {'score': 0, 'level': 'UNKNOWN', 'factors': []}
        
        # Find highest correlations
        high_correlations = [
            (asset, corr)
            for asset, corr in correlations.items()
            if abs(corr) > self._correlation_risk_threshold
        ]
        
        risk_score = min(1.0, len(high_correlations) * 0.2)
        risk_level = 'HIGH' if risk_score > 0.5 else 'MEDIUM' if risk_score > 0.3 else 'LOW'
        
        return {
            'score': risk_score,
            'level': risk_level,
            'high_correlations': high_correlations,
            'metrics': {
                'avg_correlation': sum(correlations.values()) / len(correlations),
                'max_correlation': max(abs(c) for c in correlations.values())
            }
        }
    
    def _calculate_overall_risk(
        self,
        volatility_risk: Dict[str, Any],
        liquidity_risk: Dict[str, Any],
        market_risk: Dict[str, Any],
        concentration_risk: Dict[str, Any],
        correlation_risk: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate overall risk score."""
        # Weight for each risk component
        weights = {
            'volatility': 0.25,
            'liquidity': 0.25,
            'market': 0.2,
            'concentration': 0.2,
            'correlation': 0.1
        }
        
        # Calculate weighted risk score
        risk_score = (
            volatility_risk['score'] * weights['volatility'] +
            liquidity_risk['score'] * weights['liquidity'] +
            market_risk['score'] * weights['market'] +
            concentration_risk['score'] * weights['concentration'] +
            correlation_risk['score'] * weights['correlation']
        )
        
        # Determine overall risk level
        if risk_score > 0.7:
            risk_level = 'HIGH'
        elif risk_score > 0.4:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        return {
            'score': risk_score,
            'level': risk_level,
            'weights': weights
        }
    
    def _generate_summary(
        self,
        overall_risk: Dict[str, Any],
        volatility_risk: Dict[str, Any],
        liquidity_risk: Dict[str, Any],
        market_risk: Dict[str, Any],
        concentration_risk: Dict[str, Any],
        correlation_risk: Dict[str, Any]
    ) -> str:
        """Generate risk analysis summary."""
        summary = []
        
        # Overall risk summary
        summary.append(
            f"Overall risk level is {overall_risk['level'].lower()} "
            f"with a score of {overall_risk['score']:.2f}"
        )
        
        # Component summaries
        if volatility_risk['level'] != 'UNKNOWN':
            summary.append(
                f"Volatility risk is {volatility_risk['level'].lower()} "
                f"with {volatility_risk['metrics']['annualized_volatility']:.1%} "
                f"annualized volatility"
            )
            
        if liquidity_risk['level'] != 'UNKNOWN':
            summary.append(
                f"Liquidity risk is {liquidity_risk['level'].lower()} "
                f"with {liquidity_risk['metrics']['daily_volume']:,.0f} "
                f"daily volume"
            )
            
        if market_risk['factors']:
            summary.append(
                f"Market risk factors: {', '.join(market_risk['factors'])}"
            )
            
        if concentration_risk['level'] != 'UNKNOWN':
            summary.append(
                f"Concentration risk is {concentration_risk['level'].lower()} "
                f"with top holder share of {concentration_risk['metrics']['top_holder_share']:.1%}"
            )
            
        if correlation_risk['level'] != 'UNKNOWN':
            summary.append(
                f"Correlation risk is {correlation_risk['level'].lower()} "
                f"with max correlation of {correlation_risk['metrics']['max_correlation']:.2f}"
            )
        
        return " | ".join(summary)
    
    def get_analysis_requirements(self) -> List[str]:
        """Get required data for analysis."""
        return [
            'market_data',
            'historical_data',
            'order_book',
            'holder_data',
            'correlation_data'
        ]
    
    @property
    def description(self) -> str:
        """Get analyzer description."""
        return (
            "Risk analyzer that evaluates multiple risk dimensions including "
            "volatility risk, liquidity risk, market risk, concentration risk, "
            "and correlation risk to provide a comprehensive risk assessment."
        ) 