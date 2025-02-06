import pandas as pd
from tqdm import tqdm
from typing import List
from datetime import datetime
from src.utils.db.file_store import FileStore
from src.utils.helpers import filter_by_market_cap_rank
from src.utils.clients.binance_client import BinanceClient, Timeframe as BinanceTimeframe
from src.services.analyze_market import SwapAnalyzerV1, AnalysisResult, Timeframe as AnalyzeTimeframe

def analyze_swap() -> List[AnalysisResult]:
    """分析合約市場並返回前 10 個最有信心的交易機會"""
    
    # 1. 初始化所需的服務
    file_store = FileStore()
    binance_client = BinanceClient()
    swap_analyzer = SwapAnalyzerV1()
    
    # 2. 獲取市場數據
    markets = file_store.find_all_swap()
    market_caps = file_store.find_all_market_caps()
    
    # 3. 根據市值排名過濾市場
    filtered_markets = filter_by_market_cap_rank(markets, market_caps, max_rank=200)
    
    # 4. 分析每個市場
    results = []
    for market in tqdm(
        filtered_markets,
        desc="Analyzing Futures Markets",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]",
        colour="blue",
    ):
        try:
            # 獲取 OHLCV 數據，增加獲取的數據點以確保有足夠的數據計算指標
            ohlcv_6h = binance_client.fetch_ohlcv(
                market.symbol,
                BinanceTimeframe.HOUR_6,
                limit=300,  # 增加數據點以確保有足夠的歷史數據
            )
            ohlcv_1d = binance_client.fetch_ohlcv(
                market.symbol,
                BinanceTimeframe.DAY_1,
                limit=300,  # 增加數據點以確保有足夠的歷史數據
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
                
                # 檢查是否有零交易量的情況
                if (df['volume'] == 0).any():
                    raise ValueError("數據中存在零交易量")
                
                # 檢查數據品質和數據點數量
                if len(df) < 100:  # 確保有足夠的數據點用於計算指標
                    raise ValueError(f"數據點不足 ({len(df)} < 100)")
                
        except Exception as e:
            continue
            
        # 如果通過所有檢查，才進行分析
        try:
            # 分析前 200 個數據點，但使用額外的數據點來避免 NA 值的影響
            result = swap_analyzer.analyze(
                market.symbol,
                df_6h.iloc[-200:],  # 使用最後 200 個數據點
                df_1d.iloc[-200:]   # 使用最後 200 個數據點
            )
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
    results = analyze_swap()
    
    # 將結果轉換為 DataFrame
    df = pd.DataFrame([
        {
            'datetime': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'symbol': r.symbol.split(':')[0],
            'signal_type': round(r.signal_type, 2),
            'confidence': round(r.confidence, 2),
            'entry_price': r.entry_price,
            'stop_loss': r.stop_loss,
            'take_profit': r.take_profit,
            'leverage': r.leverage if r.leverage else '',
        }
        for r in results
    ])
    
    # 設定欄位順序
    columns = [
        'datetime', 'symbol', 'signal_type', 'confidence', 
        'entry_price', 'stop_loss', 'take_profit', 'leverage'
    ]
    df = df[columns]
    
    # 輸出 CSV 格式
    print(df.to_csv(index=False))
