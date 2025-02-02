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
        # Create a copy of the DataFrame to avoid SettingWithCopyWarning
        result_df = df.copy()
        
        # Calculate VWAP first, handling zero volume
        typical_price = (result_df['high'] + result_df['low'] + result_df['close']) / 3
        volume_non_zero = result_df['volume'].replace(0, np.nan)
        vwap_temp = typical_price * volume_non_zero
        
        cumsum_volume = volume_non_zero.cumsum()
        cumsum_vwap = vwap_temp.cumsum()
        
        # Calculate VWAP, handling division by zero
        result_df.loc[:, 'vwap'] = cumsum_vwap / cumsum_volume
        
        # Fill NA values in VWAP with typical price
        result_df.loc[:, 'vwap'] = result_df['vwap'].fillna(typical_price)
        
        # Calculate price range for the period
        price_high = result_df['high'].max()
        price_low = result_df['low'].min()
        price_range = price_high - price_low
        
        # Ensure price range is not zero
        if price_range < 1e-10:  # 使用小數而不是完全相等
            price_range = 1e-10
        
        # Create price bins
        bin_size = price_range / self.n_bins
        result_df.loc[:, 'price_bin'] = ((result_df['close'] - price_low) / bin_size).astype(int)
        
        # Ensure price bins are within valid range
        result_df.loc[:, 'price_bin'] = result_df['price_bin'].clip(0, self.n_bins - 1)
        
        # Calculate volume profile
        volume_profile = result_df.groupby('price_bin')['volume'].sum()
        
        # Ensure we have at least one bin with volume
        if len(volume_profile) == 0 or volume_profile.max() == 0:
            # 如果沒有交易量，使用最中間的價格作為 POC
            poc_bin = self.n_bins // 2
            result_df.loc[:, 'poc_price'] = (price_high + price_low) / 2
        else:
            # Find Point of Control (POC) - price level with highest volume
            poc_bin = volume_profile.idxmax()
            result_df.loc[:, 'poc_price'] = price_low + (poc_bin + 0.5) * bin_size
        
        # Calculate Value Area
        total_volume = volume_profile.sum()
        if total_volume == 0:
            # 如果總交易量為零，使用整個價格範圍
            result_df.loc[:, 'va_high'] = price_high
            result_df.loc[:, 'va_low'] = price_low
            return result_df
            
        volume_sum = volume_profile.get(poc_bin, 0)
        value_area_bins = {poc_bin}
        
        above_bin = poc_bin
        below_bin = poc_bin
        
        # Expand value area until it contains 70% of total volume
        while volume_sum < 0.7 * total_volume:
            above_candidate = above_bin + 1
            below_candidate = below_bin - 1
            
            volume_above = volume_profile.get(above_candidate, 0)
            volume_below = volume_profile.get(below_candidate, 0)
            
            if volume_above > volume_below and above_candidate < self.n_bins:
                above_bin = above_candidate
                value_area_bins.add(above_bin)
                volume_sum += volume_above
            elif below_candidate >= 0:
                below_bin = below_candidate
                value_area_bins.add(below_bin)
                volume_sum += volume_below
            else:
                break
        
        # Calculate Value Area High and Low
        va_high_bin = max(value_area_bins)
        va_low_bin = min(value_area_bins)
        
        result_df.loc[:, 'va_high'] = price_low + (va_high_bin + 1) * bin_size
        result_df.loc[:, 'va_low'] = price_low + va_low_bin * bin_size
        
        return result_df
    
    def get_name(self) -> str:
        return f"VolumeProfile_{self.n_bins}" 