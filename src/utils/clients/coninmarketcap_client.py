from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import os

load_dotenv()

class CoinMarketCapClient:
    def __init__(self):
        self.base_url = 'https://pro-api.coinmarketcap.com'
        self.session = Session()
        self.session.headers.update({
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': os.getenv('COINMARKETCAP_API_KEY'),
        })

    def get_latest_listings(self, start: int = 1, limit: int = 5000, convert: str = 'USD') -> Optional[Dict[str, Any]]:
        """
        Fetch latest cryptocurrency listings with market data.
        
        Args:
            start: Start from which ranking (default 1)
            limit: Number of cryptocurrencies to return (default 5000)
            convert: Currency to convert prices to (default USD)
            
        Returns:
            Dictionary containing cryptocurrency data or None if request fails
        """
        try:
            url = f'{self.base_url}/v1/cryptocurrency/listings/latest'
            parameters = {
                'start': str(start),
                'limit': str(limit),
                'convert': convert
            }
            
            response = self.session.get(url, params=parameters)
            data = json.loads(response.text)
            return data
            
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            print(f'Error fetching data: {e}')
            return None 
        
if __name__ == '__main__':
    client = CoinMarketCapClient()
    data = client.get_latest_listings()
    print(data['data'][0])