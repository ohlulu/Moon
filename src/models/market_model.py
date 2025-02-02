from typing import Dict, Optional, Union
from decimal import Decimal
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field, field_validator
from enum import Enum
from datetime import datetime

class MarketModel(BaseModel):
    """交易市場數據模型"""
    
    class MarketType(str, Enum):
        """市場類型枚舉"""
        SPOT = 'spot'      # 現貨市場
        SWAP = 'swap'      # 永續合約
        FUTURE = 'future'  # 期貨合約
        MARGIN = 'margin'  # 槓桿交易
    
    class PrecisionModel(BaseModel):
        """交易精度設置"""
        amount: Optional[Decimal] = Field(description="數量精度（小數位數）")
        price: Optional[Decimal] = Field(description="價格精度（小數位數）")
        cost: Optional[Decimal] = Field(description="成本精度（小數位數）")
        
        class Config:
            frozen = True
    
    class LimitModel(BaseModel):
        """交易限制"""
        amount: Dict[str, Optional[Decimal]] = Field(description="數量限制 {'min': 最小值, 'max': 最大值}")
        price: Dict[str, Optional[Decimal]] = Field(description="價格限制 {'min': 最小值, 'max': 最大值}")
        cost: Dict[str, Optional[Decimal]] = Field(description="成本限制 {'min': 最小值, 'max': 最大值}")
        
        class Config:
            frozen = True

    # 基本信息
    id: str = Field(description="市場ID（例如：'BTCUSDT'）")
    symbol: str = Field(description="交易對符號（例如：'BTC/USDT'）")
    base: str = Field(description="基礎貨幣（例如：'BTC'）")
    quote: str = Field(description="報價貨幣（例如：'USDT'）")
    settle: Optional[str] = Field(default=None, description="結算貨幣（僅用於合約）")
    
    # 市場類型
    type: MarketType = Field(description="市場類型")
    spot: bool = Field(description="是否為現貨市場")
    margin: bool = Field(description="是否支持槓桿交易")
    swap: bool = Field(description="是否為永續合約")
    future: bool = Field(description="是否為期貨合約")
    
    # 交易狀態
    active: bool = Field(description="市場是否活躍")
    contract: bool = Field(description="是否為合約市場")
    linear: Optional[bool] = Field(default=None, description="是否為線性合約（USDT結算）")
    inverse: Optional[bool] = Field(default=None, description="是否為反向合約（幣本位結算）")
    
    # 合約特定
    contractSize: Optional[Decimal] = Field(default=None, description="合約規模")
    expiry: Optional[int] = Field(default=None, description="到期時間戳")
    
    # 交易規則
    precision: PrecisionModel = Field(description="交易精度設置")
    limits: LimitModel = Field(description="交易限制")
    
    # 手續費相關
    percentage: bool = Field(description="手續費是否按百分比計算")
    taker: Decimal = Field(description="吃單手續費率")
    maker: Decimal = Field(description="掛單手續費率")
    
    # 額外信息
    baseId: str = Field(description="基礎貨幣ID")
    quoteId: str = Field(description="報價貨幣ID")
    settleId: Optional[str] = Field(default=None, description="結算貨幣ID")
    exchange: str = Field(description="交易所名稱")
    
    class Config:
        frozen = True
        
    @field_validator('taker', 'maker', mode='before')
    def convert_to_decimal(cls, v):
        return Decimal(str(v))
    
    @classmethod
    def from_ccxt(cls, ccxt_market: Dict) -> 'MarketModel':
        """Create MarketModel instance from CCXT market data"""
        def to_decimal_or_none(value: Union[str, int, float, None]) -> Optional[Decimal]:
            return None if value is None else Decimal(str(value))
        
        precision = cls.PrecisionModel(
            amount=ccxt_market['precision'].get('amount', 0),
            price=ccxt_market['precision'].get('price', 0),
            cost=ccxt_market['precision'].get('cost', 0)
        )
        
        limits = cls.LimitModel(
            amount={k: to_decimal_or_none(v) for k, v in ccxt_market['limits']['amount'].items()},
            price={k: to_decimal_or_none(v) for k, v in ccxt_market['limits']['price'].items()},
            cost={k: to_decimal_or_none(v) for k, v in ccxt_market['limits']['cost'].items()}
        )
        
        return cls(
            id=ccxt_market['id'],
            symbol=ccxt_market['symbol'],
            base=ccxt_market['base'],
            quote=ccxt_market['quote'],
            settle=ccxt_market.get('settle'),
            type=ccxt_market['type'],
            spot=ccxt_market['spot'],
            margin=ccxt_market['margin'],
            swap=ccxt_market['swap'],
            future=ccxt_market['future'],
            active=ccxt_market['active'],
            contract=ccxt_market['contract'],
            linear=ccxt_market.get('linear'),
            inverse=ccxt_market.get('inverse'),
            contractSize=to_decimal_or_none(ccxt_market.get('contractSize')),
            expiry=ccxt_market.get('expiry'),
            precision=precision,
            limits=limits,
            percentage=ccxt_market['percentage'],
            taker=ccxt_market['taker'],
            maker=ccxt_market['maker'],
            baseId=ccxt_market['baseId'],
            quoteId=ccxt_market['quoteId'],
            settleId=ccxt_market.get('settleId'),
            exchange=ccxt_market['exchange']
        )
    
    @staticmethod
    def to_dataframe(markets: list['MarketModel']) -> pd.DataFrame:
        """Convert list of MarketModel to DataFrame"""
        return pd.DataFrame([market.dict() for market in markets])
    
    @staticmethod
    def to_numpy(markets: list['MarketModel']) -> np.ndarray:
        """Convert list of MarketModel to structured numpy array"""
        dtype = [
            ('id', 'U20'),
            ('symbol', 'U20'),
            ('type', 'U10'),
            ('taker', 'f8'),
            ('maker', 'f8'),
            ('active', 'bool'),
            ('contract', 'bool')
        ]
        
        data = [(
            market.id,
            market.symbol,
            market.type,
            float(market.taker),
            float(market.maker),
            market.active,
            market.contract
        ) for market in markets]
        
        return np.array(data, dtype=dtype)
    
    def get_min_amount(self) -> Optional[Decimal]:
        """Get minimum trading amount"""
        return self.limits.amount.get('min')
    
    def get_max_amount(self) -> Optional[Decimal]:
        """Get maximum trading amount"""
        return self.limits.amount.get('max')
    
    def is_tradable(self) -> bool:
        """Check if market is tradable"""
        return self.active and self.get_min_amount() is not None
    
    def calculate_fee(self, amount: Decimal, price: Decimal, side: str) -> Decimal:
        """Calculate trading fee"""
        fee_rate = self.taker if side == 'taker' else self.maker
        return amount * price * fee_rate if self.percentage else fee_rate