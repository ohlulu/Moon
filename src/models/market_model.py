from dataclasses import dataclass
from typing import Dict, List, Optional, Union
from decimal import Decimal

@dataclass
class PrecisionModel:
    """交易精度設定"""
    amount: int  # 數量精度（小數點位數）
    price: int   # 價格精度（小數點位數）
    cost: int    # 成本精度（小數點位數）

@dataclass
class LimitModel:
    """交易限制"""
    amount: Dict[str, Decimal]  # 數量限制 {'min': 最小值, 'max': 最大值}
    price: Dict[str, Decimal]   # 價格限制 {'min': 最小值, 'max': 最大值}
    cost: Dict[str, Decimal]    # 成本限制 {'min': 最小值, 'max': 最大值}

@dataclass
class MarketModel:
    """交易市場資料模型"""
    
    # 基本資訊
    id: str                     # 市場 ID（例如：'BTCUSDT'）
    symbol: str                 # 交易對符號（例如：'BTC/USDT'）
    base: str                   # 基礎貨幣（例如：'BTC'）
    quote: str                  # 報價貨幣（例如：'USDT'）
    settle: Optional[str]       # 結算貨幣（僅用於合約）
    
    # 市場類型
    type: str                   # 市場類型（'spot' 現貨 或 'swap' 永續合約）
    spot: bool                  # 是否為現貨市場
    margin: bool                # 是否支援槓桿交易
    swap: bool                  # 是否為永續合約
    future: bool                # 是否為期貨合約
    
    # 交易狀態
    active: bool                # 市場是否活躍
    contract: bool              # 是否為合約市場
    linear: Optional[bool]      # 是否為線性合約（USDT結算）
    inverse: Optional[bool]     # 是否為反向合約（幣本位結算）
    
    # 合約特定資訊
    contractSize: Optional[Decimal]     # 合約規模
    expiry: Optional[int]               # 到期時間戳（針對交割合約）
    
    # 交易規則
    precision: PrecisionModel           # 交易精度設定
    limits: LimitModel                  # 交易限制
    
    # 費用相關
    percentage: bool                    # 費用是否以百分比計算
    taker: Decimal                      # taker 手續費率
    maker: Decimal                      # maker 手續費率
    
    # 額外資訊
    baseId: str                         # 基礎貨幣 ID
    quoteId: str                        # 報價貨幣 ID
    settleId: Optional[str]             # 結算貨幣 ID
    
    # 交易所特定
    exchange: str                       # 交易所名稱（例如：'binance'）
    
    @classmethod
    def from_ccxt(cls, ccxt_market: Dict) -> 'MarketModel':
        """從 CCXT 市場資料創建 MarketModel 實例"""
        precision = PrecisionModel(
            amount=ccxt_market['precision'].get('amount', 0),
            price=ccxt_market['precision'].get('price', 0),
            cost=ccxt_market['precision'].get('cost', 0)
        )
        
        limits = LimitModel(
            amount={k: Decimal(str(v)) for k, v in ccxt_market['limits']['amount'].items()},
            price={k: Decimal(str(v)) for k, v in ccxt_market['limits']['price'].items()},
            cost={k: Decimal(str(v)) for k, v in ccxt_market['limits']['cost'].items()}
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
            contractSize=Decimal(str(ccxt_market['contractSize'])) if ccxt_market.get('contractSize') else None,
            expiry=ccxt_market.get('expiry'),
            precision=precision,
            limits=limits,
            percentage=ccxt_market['percentage'],
            taker=Decimal(str(ccxt_market['taker'])),
            maker=Decimal(str(ccxt_market['maker'])),
            baseId=ccxt_market['baseId'],
            quoteId=ccxt_market['quoteId'],
            settleId=ccxt_market.get('settleId'),
            exchange=ccxt_market['exchange']
        )