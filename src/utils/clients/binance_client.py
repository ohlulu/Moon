import os
import ccxt
from dotenv import load_dotenv
from pprint import pprint
from typing import Dict, List

class BinanceClient:
    # 定義穩定幣列表
    STABLECOINS = {'USDT', 'USDC', 'BUSD', 'DAI', 'TUSD', 'UST', 'USDP', 'USDD'}

    def __init__(self):
        load_dotenv()
        
        self.client = ccxt.binance({
            'apiKey': os.getenv('BINANCE_API_KEY'),
            'secret': os.getenv('BINANCE_SECRET_KEY'),
            'enableRateLimit': True,
        })
    
    def get_non_stablecoin_markets(self) -> List[Dict]:
        """獲取所有非穩定幣交易對的市場資訊，移除 info 字段
        
        Returns:
            List[Dict]: 市場資訊列表，包含除了 info 以外的所有原始字段
        """
        # 獲取所有市場資訊
        markets = self.client.load_markets()
        
        # 過濾並整理市場資訊
        filtered_markets = []
        for symbol, market in markets.items():
            # 跳過計價貨幣是穩定幣的交易對
            if market['quote'] in self.STABLECOINS:
                continue
                
            # 複製原始市場資訊，但移除 info 字段
            market_without_info = market.copy()
            market_without_info.pop('info', None)
            filtered_markets.append(market_without_info)
        
        return filtered_markets

    def print_market_structure(self, market_info: Dict):
        """打印市場資訊的所有欄位"""
        print(f"\n{market_info['symbol']} 資訊:")
        print("-" * 30)
        for key, value in market_info.items():
            if isinstance(value, dict):
                print(f"\n{key}:")
                for sub_key, sub_value in value.items():
                    print(f"  {sub_key}: {sub_value}")
            else:
                print(f"{key}: {value}")

if __name__ == '__main__':
    # 測試客戶端
    client = BinanceClient()
    markets = client.get_non_stablecoin_markets()
    
    print(f"\n找到 {len(markets)} 個非穩定幣交易對")
    
    # 打印前 5 個交易對的資訊
    for market in markets[:5]:
        client.print_market_structure(market)
        print("\n" + "=" * 50)
