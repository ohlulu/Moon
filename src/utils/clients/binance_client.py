import os
import ccxt
from dotenv import load_dotenv
from pprint import pprint
from typing import Dict, List, Union
from src.utils.logging import setup_logging
from src.models.market_model import MarketModel
from datetime import datetime
from enum import Enum, auto

class MarketType(str, Enum):
    SPOT = 'spot'
    SWAP = 'swap'

class Timeframe(str, Enum):
    # Hours
    HOUR_4 = '4h'
    HOUR_6 = '6h'
    HOUR_8 = '8h'
    HOUR_12 = '12h'
    
    # Days
    DAY_1 = '1d'

class BinanceClient:
    # 定義穩定幣列表
    STABLECOINS = {
        # USD Stablecoins - Major
        'USD',
        'USDT',     # Tether
        'USDC',     # USD Coin
        'BUSD',     # Binance USD
        'DAI',      # Dai
        'TUSD',     # TrueUSD
        'USDP',     # Pax Dollar (formerly PAX)
        'USDD',     # USDD
        'UST',      # TerraUSD Classic
        
        # USD Stablecoins - Others
        'GUSD',     # Gemini Dollar
        'LUSD',     # Liquity USD
        'FRAX',     # Frax
        'SUSD',     # Synthetix USD
        'CUSD',     # Celo Dollar
        'USDN',     # Neutrino USD
        'MUSD',     # mStable USD
        'HUSD',     # HUSD
        'OUSD',     # Origin Dollar
        'USDX',     # USDX
        'USDK',     # USDK
        'DOLA',     # Dola USD
        'YUSD',     # YUSD Stablecoin
        'ZUSD',     # ZUSD
        'USDH',     # USDH
        'USDB',     # USD Balance
        'USDS',     # Stably USD
        'USDJ',     # JUST Stablecoin
        'USDL',     # USDL
        'RSV',      # Reserve
        'USDEX',    # USDEX
        'USDF',     # USD Freedom
        'DUSD',     # Decentralized USD
        
        # EUR Stablecoins
        'EURS',     # STASIS EURO
        'EURT',     # Tether EURt
        'JEUR',     # Jarvis Synthetic Euro
        'SEUR',     # Stasis SEuro
        'CEUR',     # Celo Euro
        'EUROC',    # Euro Coin
        
        # GBP Stablecoins
        'GBPT',     # Tether GBPt
        'GBPP',     # Poundtoken
        'TGBP',     # TrueGBP
        
        # Other Fiat Stablecoins
        'CADC',     # CAD Coin
        'XIDR',     # XIDR (Indonesian Rupiah)
        'BIDR',     # BIDR (Binance IDR)
        'AUDT',     # AUD Tether
        'CNHT',     # CNH Tether
        'XSGD',     # XSGD (Singapore Dollar)
        'NZDS',     # NZD Stablecoin
        'TRYB',     # BiLira
        'BRZC',     # Brazilian Digital Token
        'JPYC',     # JPY Coin
        'THBT',     # Thai Baht Digital
        'MXNT',     # Mexican Peso Tether
        
        # Commodity-Backed Stablecoins
        'XAUT',     # Tether Gold
        'PAXG',     # PAX Gold
        'DGLD',     # Digital Gold
        
        # Algorithmic Stablecoins
        'AMPL',     # Ampleforth
        'BAC',      # Basis Cash
        'FEI',      # Fei USD
        'FLOAT',    # Float Protocol
        'RAI',      # Rai Reflex Index
        'USDV',     # USD Velocity
        'VOLT',     # Voltage Protocol
        
        # Yield-Bearing Stablecoins
        'ALUSD',    # Alchemix USD
        'YUSD',     # yUSD
        'SUSD',     # Synth sUSD
        'MUSD',     # mStable USD
        'OUSD',     # Origin USD
        
        # Deprecated but might still exist in some pairs
        'SAI',      # Single Collateral DAI (old)
        'USDT_OLD', # Old USDT contract
        'sUSD',     # Synthetix USD (old format)
        'BUSD_OLD'  # Old BUSD contract
    }

    def __init__(self):
        load_dotenv()
        auth_config = {
            'apiKey': os.getenv('BINANCE_API_KEY'),
            'secret': os.getenv('BINANCE_SECRET_KEY'),
            'enableRateLimit': True,
        }
        self.logger = setup_logging(__name__)
        self.spot_client = ccxt.binance(auth_config)
        self.swap_client = ccxt.binanceusdm(auth_config)

    def fetch_markets(self, market_types: List[MarketType] = [MarketType.SPOT, MarketType.SWAP]) -> List[MarketModel]:
        """獲取指定市場類型的非穩定幣交易對資訊
        
        Args:
            market_types: 可以是單個市場類型或市場類型列表
                - MarketType.SPOT: 現貨市場
                - MarketType.SWAP: 永續合約
        
        Returns:
            List[MarketModel]: 市場資訊列表，已去除重複項
        """
        if isinstance(market_types, MarketType):
            market_types = [market_types]
            
        all_markets = {}  # 使用字典來儲存市場資料，以 symbol 為 key
        
        for market_type in market_types:
            try:
                exchange_class = self.spot_client if market_type == MarketType.SPOT else self.swap_client
                self.logger.info(f"正在獲取 {market_type.value} 市場資料...")
                markets = exchange_class.load_markets()
                self.logger.info(f"已獲取到 {len(markets)} 個原始市場")
                
                for symbol, market in markets.items():
                    # 跳過穩定幣交易對
                    if market['base'] in self.STABLECOINS:
                        continue
                    if market['quote'] not in ['USDT']:  
                        continue
                    
                    # 根據市場類型過濾
                    if market_type == MarketType.SPOT:
                        # 只獲取純現貨市場，排除保證金交易
                        if market.get('margin', False):
                            continue
                    else:  # swap
                        if not market.get(market_type.value, True):
                            continue
                    
                    try:
                        market['exchange'] = 'binance'
                        market_model = MarketModel.from_ccxt(market)
                        # 使用 symbol 作為 key 來儲存，自動去除重複項
                        all_markets[market_model.symbol] = market_model
                    except Exception as e:
                        self.logger.warning(f"無法處理市場 {symbol}: {str(e)}")
                        continue
                
            except Exception as e:
                self.logger.error(f"獲取 {market_type.value} 市場時發生錯誤: {str(e)}")
                continue
                
        # 將字典值轉換為列表
        unique_markets = list(all_markets.values())
        self.logger.info(f"過濾後剩下 {len(unique_markets)} 個唯一市場")
        return unique_markets

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: Timeframe = Timeframe.HOUR_4,
        limit: int = 300,
        market_type: MarketType = MarketType.SPOT
    ) -> List[List[float]]:
        """獲取指定交易對的 OHLCV (Open, High, Low, Close, Volume) 數據

        Args:
            symbol: 交易對符號，例如 "BTC/USDT"
            timeframe: 時間間隔，例如 Timeframe.MIN_1, Timeframe.HOUR_1 等
            limit: 返回的數據點數量，最大值通常為 1000
            market_type: 市場類型，MarketType.SPOT 或 MarketType.SWAP

        Returns:
            List[List[float]]: OHLCV 數據列表，每個元素包含 [timestamp, open, high, low, close, volume]

        Raises:
            ValueError: 如果參數無效
            Exception: 如果在獲取數據時發生錯誤
        """
        try:
            # 選擇正確的交易所實例
            exchange_class = self.spot_client if market_type == MarketType.SPOT else self.swap_client

            
            # 獲取 OHLCV 數據
            ohlcv = exchange_class.fetch_ohlcv(symbol, timeframe.value, limit=limit)
            
            return ohlcv

        except ccxt.BadSymbol as e:
            self.logger.error(f"無效的交易對符號 {symbol}: {str(e)}")
            raise ValueError(f"無效的交易對符號: {symbol}")
        
        except ccxt.BadRequest as e:
            self.logger.error(f"請求參數無效: {str(e)}")
            raise ValueError(f"請求參數無效: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"獲取 OHLCV 數據時發生錯誤: {str(e)}")
            raise


if __name__ == "__main__":
    client = BinanceClient()
    ohlcv = client.fetch_ohlcv('BTC/USDT', Timeframe.HOUR_4, 3, MarketType.SWAP)
    print(ohlcv)
