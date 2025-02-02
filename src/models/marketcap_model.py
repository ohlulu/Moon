from typing import Dict, Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field
from datetime import datetime
import pandas as pd
import numpy as np

class MarketCapModel(BaseModel):
    """CoinMarketCap API 數據模型"""

    class Config:
        frozen = True
    
    class Quote(BaseModel):
        """報價數據模型"""
        price: Decimal = Field(description="當前價格")
        volume_24h: Decimal = Field(description="24小時交易量")
        percent_change_1h: Decimal = Field(description="1小時價格變化百分比")
        percent_change_24h: Decimal = Field(description="24小時價格變化百分比")
        percent_change_7d: Decimal = Field(description="7天價格變化百分比")
        market_cap: Decimal = Field(description="市值")
        last_updated: datetime = Field(description="最後更新時間")

    class Crypto(BaseModel):
        """加密貨幣數據模型"""
        id: int = Field(description="CoinMarketCap ID")
        name: str = Field(description="加密貨幣名稱")
        symbol: str = Field(description="加密貨幣符號")
        slug: str = Field(description="URL 友好的名稱")
        cmc_rank: Optional[int] = Field(description="CoinMarketCap 排名")
        num_market_pairs: int = Field(description="交易對數量")
        circulating_supply: Decimal = Field(description="流通供應量")
        total_supply: Decimal = Field(description="總供應量")
        max_supply: Optional[Decimal] = Field(description="最大供應量")
        last_updated: datetime = Field(description="最後更新時間")
        date_added: datetime = Field(description="首次添加時間")
        tags: List[str] = Field(description="標籤列表")
        platform: Optional[Dict] = Field(description="代幣平台信息")
        quote: Dict[str, 'MarketCapModel.Quote'] = Field(description="不同幣種的報價信息")

        class Config:
            frozen = True

    @classmethod
    def from_api_response(cls, response: List[Dict]) -> List['MarketCapModel.Crypto']:
        """從 API 響應創建模型實例"""
        return [cls.Crypto.model_validate(item) for item in response]
    
    @staticmethod
    def to_dataframe(cryptos: List['MarketCapModel.Crypto']) -> pd.DataFrame:
        """Convert list of Crypto models to DataFrame
        
        Args:
            cryptos: List of Crypto models
            
        Returns:
            pandas.DataFrame: DataFrame containing crypto data
        """
        data = []
        for crypto in cryptos:
            # Get USD quote (assuming USD is always present)
            usd_quote = crypto.quote.get('USD')
            if not usd_quote:
                continue
                
            row = {
                'id': crypto.id,
                'name': crypto.name,
                'symbol': crypto.symbol,
                'slug': crypto.slug,
                'cmc_rank': crypto.cmc_rank,
                'price': float(usd_quote.price),
                'volume_24h': float(usd_quote.volume_24h),
                'market_cap': float(usd_quote.market_cap),
                'percent_change_1h': float(usd_quote.percent_change_1h),
                'percent_change_24h': float(usd_quote.percent_change_24h),
                'percent_change_7d': float(usd_quote.percent_change_7d),
                'circulating_supply': float(crypto.circulating_supply),
                'total_supply': float(crypto.total_supply),
                'max_supply': float(crypto.max_supply) if crypto.max_supply else None,
                'last_updated': usd_quote.last_updated,
                'date_added': crypto.date_added
            }
            data.append(row)
        
        return pd.DataFrame(data)
    
    @staticmethod
    def to_numpy(cryptos: List['MarketCapModel.Crypto']) -> np.ndarray:
        """Convert list of Crypto models to structured numpy array
        
        Args:
            cryptos: List of Crypto models
            
        Returns:
            numpy.ndarray: Structured array containing crypto data
        """
        dtype = [
            ('id', 'i8'),
            ('symbol', 'U10'),
            ('name', 'U50'),
            ('cmc_rank', 'i4'),
            ('price', 'f8'),
            ('market_cap', 'f8'),
            ('volume_24h', 'f8'),
            ('percent_change_24h', 'f8')
        ]
        
        data = [(
            crypto.id,
            crypto.symbol,
            crypto.name,
            crypto.cmc_rank or 0,
            float(crypto.quote['USD'].price),
            float(crypto.quote['USD'].market_cap),
            float(crypto.quote['USD'].volume_24h),
            float(crypto.quote['USD'].percent_change_24h)
        ) for crypto in cryptos if 'USD' in crypto.quote]
        
        return np.array(data, dtype=dtype)