import pandas as pd
from tqdm import tqdm
from typing import List
from src.utils.db.file_store import FileStore
from src.utils.helpers import filter_by_market_cap_rank
from src.utils.clients.binance_client import BinanceClient, Timeframe as BinanceTimeframe
from src.services.analyze_market import SpotAnalyzerV1, AnalysisResult, Timeframe as AnalyzeTimeframe

def analyze_spot() -> List[AnalysisResult]:
    """分析現貨市場並返回前 10 個最有信心的交易機會"""
    
    # 1. 初始化所需的服務
    file_store = FileStore()
    binance_client = BinanceClient()
    spot_analyzer = SpotAnalyzerV1()
    
    # 2. 獲取市場數據
    markets = file_store.find_all_spot()
    market_caps = file_store.find_all_market_caps()
    
    # 3. 根據市值排名過濾市場
    filtered_markets = filter_by_market_cap_rank(markets, market_caps, max_rank=50)
    
    # 4. 分析每個市場
    results = []
    for market in tqdm(
        filtered_markets,
        desc="Analyzing Markets",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]",
        colour="green",
    ):
        try:
            # 獲取 OHLCV 數據
            ohlcv_6h = binance_client.fetch_ohlcv(
                market.symbol,
                BinanceTimeframe.HOUR_6,
                limit=100,
            )
            ohlcv_1d = binance_client.fetch_ohlcv(
                market.symbol,
                BinanceTimeframe.DAY_1,
                limit=100,
            )
            
            # 轉換為 DataFrame 並正確處理時間戳記
            df_6h = pd.DataFrame(
                ohlcv_6h,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df_1d = pd.DataFrame(
                ohlcv_1d,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            # 確保數據類型正確
            for df in [df_6h, df_1d]:
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                # 確保所有價格和交易量列是 float 類型
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = df[col].astype(float)
                
                # 確保數據按時間排序
                df.sort_index(inplace=True)
                
                # 確保沒有缺失值
                if df.isnull().values.any():
                    raise ValueError(f"數據中存在缺失值")
                
                # 確保至少有足夠的數據點進行分析
                if len(df) < 30:  # 通常技術指標需要至少 30 個數據點
                    raise ValueError(f"數據點不足: {len(df)}")
        except Exception as e:
            continue

        # 如果通過所有檢查，才進行分析
        try:
            # 分析市場
            result = spot_analyzer.analyze(market.symbol, df_6h, df_1d)
            results.append(result)
            
        except Exception as e:
            print(f"分析 {market.symbol} 時發生錯誤: {str(e)}")
            continue
    
    # 5. 根據信心度排序並返回前 10 個結果
    sorted_results = sorted(
        results,
        key=lambda x: x.confidence * x.expected_return,
        reverse=True
    )
    
    return sorted_results[:10]

if __name__ == "__main__":
    results = analyze_spot()
    print("\n=== 分析完成 ===")
    print(f"共分析出 {len(results)} 個交易機會\n")
    for result in results:
        print(f"\n分析結果 - {result.symbol}:")
        print(f"信心度: {result.confidence:.2f}")
        print(f"預期報酬: {result.expected_return:.2f}")
        print(f"進場價: {result.entry_price:.2f}")
        print(f"止損價: {result.stop_loss:.2f}")
        print(f"目標價: {result.take_profit:.2f}")
