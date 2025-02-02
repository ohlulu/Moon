from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from typing import Dict, Any, List
from dotenv import load_dotenv
import os
from src.utils.logging import setup_logging
from src.models.market_cap_model import MarketCapModel

load_dotenv()



class CoinMarketCapClient:
    class Error(Exception):
        """CoinMarketCap API 客戶端錯誤"""
    pass

    def __init__(self):
        self.logger = setup_logging(__name__)

        self.base_url = 'https://pro-api.coinmarketcap.com'
        self.session = Session()
        self.session.headers.update({
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': os.getenv('COINMARKETCAP_API_KEY'),
        })

    def fetch_market_caps(self, start: int = 1, limit: int = 5000, convert: str = 'USD') -> List[MarketCapModel]:
        """
        Fetch latest cryptocurrency listings with market data.
        
        Args:
            start: Start from which ranking (default 1)
            limit: Number of cryptocurrencies to return (default 5000)
            convert: Currency to convert prices to (default USD)
            
        Returns:
            List[MarketCapModel] containing cryptocurrency data
            
        Raises:
            CoinMarketCapClient.Error: If there is an error fetching data from the API
        """
        try:
            url = f'{self.base_url}/v1/cryptocurrency/listings/latest'
            parameters = {
                'start': str(start),
                'limit': str(limit),
                'convert': convert
            }
            
            self.logger.info(f"正在從 CoinMarketCap 獲取最新列表 (start={start}, limit={limit})")
            response = self.session.get(url, params=parameters)
            
            if response.status_code != 200:
                error_msg = f"API 請求失敗，狀態碼 {response.status_code}, 錯誤訊息: {response.text}"
                self.logger.error(error_msg)
                raise self.Error(error_msg)
            
            data = response.json()['data']
            self.logger.info(f"成功獲取 {len(data)} 個加密貨幣列表")
            return MarketCapModel.from_api_response(data)
            
        except (ConnectionError, Timeout) as e:
            error_msg = f"Network error while fetching data: {str(e)}"
            self.logger.error(error_msg)
            raise CoinMarketCapClient.Error(error_msg) from e
        except TooManyRedirects as e:
            error_msg = f"Too many redirects: {str(e)}"
            self.logger.error(error_msg)
            raise CoinMarketCapClient.Error(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(error_msg)
            raise CoinMarketCapClient.Error(error_msg) from e
