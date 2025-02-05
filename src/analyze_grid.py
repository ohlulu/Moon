import pandas as pd
from tqdm import tqdm
from typing import List
from datetime import datetime
from src.utils.db.file_store import FileStore
from src.utils.helpers import filter_by_market_cap_rank
from src.utils.clients.binance_client import BinanceClient, Timeframe as BinanceTimeframe
from src.services.grid_analyzer import GridAnalyzer

def analyze_grid() -> pd.DataFrame:
    """分析合約市場並返回前 10 個最有信心的交易機會"""
    
    # 1. 初始化所需的服務
    file_store = FileStore()
    binance_client = BinanceClient()
    grid_analyzer = GridAnalyzer()
    
    # 2. 獲取市場數據
    markets = file_store.find_all_swap()
    market_caps = file_store.find_all_market_caps()
    
    # 3. 根據市值排名過濾市場
    filtered_markets = filter_by_market_cap_rank(markets, market_caps, max_rank=500)
    
    # 4. 分析每個市場
    results = []
    for market in tqdm(
        filtered_markets,
        desc="Analyzing Grid Markets",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]",
        colour="blue",
    ):
        try:
            ohlcv_1d = binance_client.fetch_ohlcv(
                market.symbol,
                BinanceTimeframe.DAY_1,
                limit=300,  # 增加數據點以確保有足夠的歷史數據
            )

            df_1d = pd.DataFrame(
                ohlcv_1d,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
                
        except Exception as e:
            print(f"fetch_ohlcv: {market.symbol} 時發生錯誤: {str(e)}")
            continue

        try:
            result = grid_analyzer.analyze(df_1d.iloc[-250:])
            result['symbol'] = market.symbol
            results.append(result)
            
        except Exception as e:
            print(f"分析 {market.symbol} 時發生錯誤: {str(e)}")
            continue
    
    # 5. 根據信心度排序並返回前 10 個結果
    sorted_results = sorted(
        results,
        key=lambda x: x['composite_score'],
        reverse=True
    )
    
    return sorted_results[:10]

if __name__ == "__main__":
    results = analyze_grid()
    
    # 將結果轉換為 DataFrame
    df = pd.DataFrame([
        {
            'datetime': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'symbol': r['symbol'].split(':')[0],
            'composite_score': r['composite_score'],
            'volatility_score': r['volatility_score'],
            'trend_score': r['trend_score'],
            'volume_score': r['volume_score'],
            'upper_price': r['upper_price'],
            'lower_price': r['lower_price'],
            'grid_number': r['grid_number']
        }
        for r in results
    ])
    
    # 設定欄位順序
    columns = [
        'datetime', 'symbol', 'composite_score', 
        'upper_price', 'lower_price', 'grid_number',
        'trend_score', 'volume_score', 'volatility_score', 
    ]
    df = df[columns]
    
    # 輸出 CSV 格式
    print(df.to_csv(index=False))
