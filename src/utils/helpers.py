from typing import List
from src.models.market_cap_model import MarketCapModel
from src.models.market_model import MarketModel

def filter_by_market_cap_rank(
    markets: List[MarketModel],
    market_cap_data: List[MarketCapModel.Crypto],
    max_rank: int = 500
) -> List[MarketModel]:
    """根據 CoinMarketCap 排名過濾市場
    
    Args:
        markets: 交易所的市場列表
        market_cap_data: CoinMarketCap API 返回的加密貨幣數據列表
        max_rank: 最大排名閾值（默認為500）
        
    Returns:
        List[MarketModel]: 符合排名要求的市場列表
    """
    # 創建排名查找字典
    rank_lookup = {
        crypto.symbol: crypto.cmc_rank 
        for crypto in market_cap_data 
        if crypto.cmc_rank is not None and crypto.cmc_rank <= max_rank
    }
    
    # 過濾市場
    return [
        market for market in markets
        if market.base in rank_lookup
    ]