import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

from src.services.indicators.atr import ATR
from src.services.indicators.rsi import RSI
from src.services.indicators.bollinger_bands import BollingerBands
from src.services.indicators.obv import OBV

class GridAnalyzer:
    def __init__(
        self,
        atr_period: int = 14,
        rsi_period: int = 14,
        bb_period: int = 20,
        bb_std: float = 2.0
    ):
        self.atr = ATR(period=atr_period)
        self.rsi = RSI(period=rsi_period)
        self.bb = BollingerBands(period=bb_period, num_std=bb_std)
        self.obv = OBV()
        
    def analyze(self, df_1d: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze the suitability of grid trading for a given symbol
        
        Parameters:
        -----------
        df_1d : pd.DataFrame
            DataFrame containing OHLCV data
            
        Returns:
        --------
        pd.DataFrame
            DataFrame containing analysis results with scores for each metric
        """
        # Calculate all indicators
        df_1d = self.atr.calculate(df_1d)
        df_1d = self.rsi.calculate(df_1d)
        df_1d = self.bb.calculate(df_1d)
        df_1d = self.obv.calculate(df_1d)
        
        # Calculate scores
        volatility_score = self._calculate_volatility_score(df_1d)
        trend_score = self._calculate_trend_score(df_1d)
        volume_score = self._calculate_volume_score(df_1d)
        composite_score = (volatility_score * 0.6 + trend_score * 0.2 + volume_score * 0.2)
        upper_price, lower_price, grid_number = self.get_grid_parameters(df_1d)

        return {
            'composite_score': composite_score,
            'volatility_score': volatility_score,
            'trend_score': trend_score,
            'volume_score': volume_score,
            'upper_price': upper_price,
            'lower_price': lower_price,
            'grid_number': grid_number
        }
    
    def _calculate_volatility_score(self, df_1d: pd.DataFrame) -> float:
        """Calculate volatility score based on ATR"""
        # Get the last 30 periods of normalized ATR
        df_1d.loc[:, 'norm_atr'] = df_1d['atr'] / df_1d['close']
        recent_norm_atr = df_1d['norm_atr'].tail(30)
        
        # Calculate mean and stability of ATR
        mean_norm_atr = recent_norm_atr.mean()
        # Prevent division by zero
        if mean_norm_atr == 0:
            return 0
        
        atr_stability = 1 - recent_norm_atr.std() / mean_norm_atr
        
        # Score between 0 and 1
        # Higher score means more suitable volatility for grid trading
        return min(max((mean_norm_atr * 100 * atr_stability), 0), 1)
    
    def _calculate_trend_score(self, df_1d: pd.DataFrame) -> float:
        """Calculate trend score based on RSI and Bollinger Bands"""
        recent_rsi = df_1d['rsi'].tail(30)
        
        # Check if RSI is between 35-65 most of the time
        rsi_range_score = len(recent_rsi[(recent_rsi >= 35) & (recent_rsi <= 65)]) / len(recent_rsi)
        
        # Calculate Bollinger Bands width
        df_1d['bb_width'] = (df_1d['bb_upper'] - df_1d['bb_lower']) / df_1d['bb_middle'].replace(0, float('inf'))
        recent_bb_width = df_1d['bb_width'].tail(30)
        
        # Calculate BB width stability
        bb_width_mean = recent_bb_width.mean()
        if bb_width_mean == 0:
            bb_width_stability = 0
        else:
            bb_width_stability = 1 - recent_bb_width.std() / bb_width_mean
        
        # Combine scores
        return (rsi_range_score + bb_width_stability) / 2
    
    def _calculate_volume_score(self, df_1d: pd.DataFrame) -> float:
        """Calculate volume score based on OBV trend and stability"""
        recent_obv = df_1d['obv'].tail(30)
        
        # Calculate OBV trend
        obv_trend = np.corrcoef(recent_obv.index, recent_obv.values, ddof=1)[0, 1]
        
        # Calculate OBV stability
        obv_mean = abs(recent_obv.mean())
        if obv_mean == 0:
            obv_stability = 0
        else:
            obv_stability = 1 - recent_obv.std() / obv_mean
        
        # Combine scores
        return (abs(obv_trend) + obv_stability) / 2
    
    def get_grid_parameters(self, df_1d: pd.DataFrame) -> Tuple[float, float, int]:
        """
        Calculate adaptive grid parameters based on market conditions and efficiency
        
        Parameters:
        -----------
        df_1d : pd.DataFrame
            DataFrame containing OHLCV data with calculated indicators
            
        Returns:
        --------
        Tuple[float, float, int]
            upper_price, lower_price, grid_number
        """
        current_price = df_1d['close'].iloc[-1]
        
        # Calculate price efficiency ratio
        price_changes = abs(df_1d['close'].diff(20))
        price_paths = df_1d['high'].rolling(20).max() - df_1d['low'].rolling(20).min()
        # Add small epsilon to prevent division by zero
        price_paths = price_paths.replace(0, float('inf'))
        efficiency_ratio = (price_changes / price_paths).fillna(0).tail(20).mean()
        
        # Calculate trend strength
        rsi_deviation = abs(df_1d['rsi'].tail(20).mean() - 50) / 50
        trend_strength = rsi_deviation * efficiency_ratio
        
        # Calculate adaptive price range with minimum volatility threshold
        recent_volatility = max(df_1d['atr'].tail(20).mean() / current_price, 0.01)  # Minimum 1% volatility
        price_range = current_price * recent_volatility * (1 + trend_strength) * 2
        
        # Ensure minimum price range of 2% of current price
        price_range = max(price_range, current_price * 0.02)
        
        # In trend market, adjust price range based on trend direction
        if trend_strength > 0.3:
            if df_1d['rsi'].iloc[-1] > 50:  # Uptrend
                upper_price = current_price * (1 + price_range * 0.6)
                lower_price = current_price * (1 - price_range * 0.4)
            else:  # Downtrend
                upper_price = current_price * (1 + price_range * 0.4)
                lower_price = current_price * (1 - price_range * 0.6)
        else:
            # Ranging market uses symmetric range
            upper_price = current_price * (1 + price_range/2)
            lower_price = current_price * (1 - price_range/2)
        
        # Calculate grid number based on volatility and market efficiency
        volatility_factor = min(recent_volatility * 100, 1)
        base_grid_number = int(20 * (1 + volatility_factor))
        
        # Adjust grid number based on price efficiency
        if efficiency_ratio > 0.7:  # Strong trend
            grid_modifier = 1.3
        elif efficiency_ratio < 0.3:  # Strong ranging
            grid_modifier = 0.7
        else:  # Mixed market
            grid_modifier = 1.0
            
        grid_number = max(int(base_grid_number * grid_modifier), 4)  # Ensure minimum 4 grids
        
        # Ensure grid size is larger than minimum price movement
        min_price_movement = max(df_1d['close'].diff().abs().mean(), current_price * 0.001)  # At least 0.1% of price
        min_grid_size = min_price_movement * 3
        price_range = upper_price - lower_price
        max_grids_by_range = max(int(price_range / min_grid_size), 4)  # Ensure minimum 4 grids
        grid_number = min(grid_number, max_grids_by_range)
        
        return upper_price, lower_price, grid_number