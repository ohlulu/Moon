import os
import ccxt
from dotenv import load_dotenv
from pprint import pprint
from typing import Dict, List, Literal, Union
from src.utils.logging import setup_logging

MARKET_TYPE = Literal['spot', 'swap']

class BinanceClient:
    # 定義穩定幣列表
    STABLECOINS = {
        # USD Stablecoins - Major
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
        self.logger = setup_logging(__name__)

    def _get_auth_config(self) -> Dict:
        """Return authentication configuration for Binance API
        
        Returns:
            Dict: Authentication configuration
            
        Raises:
            ValueError: If API credentials are not properly configured
        """
        api_key = os.getenv('BINANCE_API_KEY')
        secret_key = os.getenv('BINANCE_SECRET_KEY')
        
        if not api_key or not secret_key:
            raise ValueError(
                "Missing Binance API credentials. "
                "Please ensure BINANCE_API_KEY and BINANCE_SECRET_KEY "
                "are set in your environment variables."
            )
            
        return {
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
        }

    def fetch_markets(self, market_types: Union[MARKET_TYPE, List[MARKET_TYPE]] = ['spot', 'swap']) -> List[Dict]:
        """獲取指定市場類型的非穩定幣交易對資訊
        
        Args:
            market_types: 可以是單個市場類型字符串或市場類型列表
                - 'spot': 現貨市場
                - 'swap': 永續合約
        
        Returns:
            List[Dict]: 市場資訊列表
        """
        if isinstance(market_types, str):
            market_types = [market_types]
            
        all_markets = []
        
        for market_type in market_types:
            try:
                exchange_class = ccxt.binance if market_type == 'spot' else ccxt.binanceusdm
                client = exchange_class(self._get_auth_config())
                self.logger.info(f"正在獲取 {market_type} 市場資料...")
                markets = client.load_markets()
                self.logger.info(f"已獲取到 {len(markets)} 個原始市場")
                
                filtered_markets = []
                for symbol, market in markets.items():
                    if market['base'] in self.STABLECOINS:
                        continue
                        
                    market_without_info = market.copy()
                    market_without_info.pop('info', None)
                    all_markets.append(market_without_info)
                
            except Exception as e:
                self.logger.error(f"Error fetching {market_type} markets: {str(e)}")
                all_markets[market_type] = []
                
        return all_markets

if __name__ == '__main__':
    client = BinanceClient()
    data = client.fetch_markets()
    logger = setup_logging(__name__)
    logger.info(data[:10])