import pandas as pd
import numpy as np
from src.services.indicators.indicator import Indicator

class VolumeProfile(Indicator):
    def __init__(self, n_bins: int = 24):
        self.n_bins = n_bins
        
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Volume Profile
        
        Args:
            df: DataFrame with 'high', 'low', 'close', 'volume' columns
            
        Returns:
            DataFrame with additional volume profile related columns
        """
        # Calculate VWAP first
        df['vwap'] = (df['high'] + df['low'] + df['close']) / 3 * df['volume']
        df['vwap'] = df['vwap'].cumsum() / df['volume'].cumsum()
        
        # Calculate price range for the period
        price_high = df['high'].max()
        price_low = df['low'].min()
        price_range = price_high - price_low
        
        # Create price bins
        bin_size = price_range / self.n_bins
        df['price_bin'] = ((df['close'] - price_low) / bin_size).astype(int)
        
        # Calculate volume profile
        volume_profile = df.groupby('price_bin')['volume'].sum()
        
        # Find Point of Control (POC) - price level with highest volume
        poc_bin = volume_profile.idxmax()
        df['poc_price'] = price_low + (poc_bin + 0.5) * bin_size
        
        # Calculate Value Area
        total_volume = volume_profile.sum()
        volume_sum = 0
        value_area_bins = [poc_bin]
        
        # Expand value area until it contains 70% of total volume
        while volume_sum < 0.7 * total_volume:
            volumes_above = volume_profile[poc_bin + len(value_area_bins)]
            volumes_below = volume_profile[poc_bin - len(value_area_bins)]
            
            if volumes_above > volumes_below:
                value_area_bins.append(poc_bin + len(value_area_bins))
                volume_sum += volumes_above
            else:
                value_area_bins.append(poc_bin - len(value_area_bins))
                volume_sum += volumes_below
        
        # Calculate Value Area High and Low
        df['va_high'] = price_low + (max(value_area_bins) + 1) * bin_size
        df['va_low'] = price_low + min(value_area_bins) * bin_size
        
        return df
    
    def get_name(self) -> str:
        return f"VolumeProfile_{self.n_bins}" 