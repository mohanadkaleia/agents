"""
Stock Market Data Client using Alpha Vantage API.

This client provides methods to fetch various types of stock market data
using the Alpha Vantage API with proper error handling and logging.
"""

import requests

from typing import Dict, List, Optional, Any
from utils.logger import get_logger

logger = get_logger(__name__)

# Custom exception classes for the Alpha Vantage client
class AlphaVantageError(Exception):
    """Base exception class for all Alpha Vantage client errors."""
    pass


class InvalidArgsError(AlphaVantageError):
    """Raised when invalid arguments are provided."""
    pass


class APIError(AlphaVantageError):
    """Raised when there's an issue with Alpha Vantage API calls."""
    pass


class RateLimitError(APIError):
    """Raised when Alpha Vantage API rate limits are exceeded."""
    pass


class ConnectionError(APIError):
    """Raised when there's a connection issue with Alpha Vantage API."""
    pass


class DataNotFoundError(AlphaVantageError):
    """Raised when requested data is not found."""
    pass


class StockMarketClient:
    """
    A client for fetching stock market data using Alpha Vantage API.
    
    This client provides methods to fetch:
    - Real-time stock quotes
    - Historical daily data
    - Intraday data
    - Company information
    - Search for stocks
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, timeout: Optional[int] = None, max_retries: Optional[int] = None):
        """
        Initialize the StockMarketClient.
        
        Args:
            api_key (str, optional): Alpha Vantage API key. If not provided,
                                   will try to get from configuration.
                                   
        Raises:
            InvalidArgsError: If no API key is available
        """
        if not api_key:
            raise InvalidArgsError("missing api key")

        self.api_key = api_key
        self.base_url = base_url or 'https://www.alphavantage.co/query'
        self.timeout = timeout or 30
        self.max_retries = max_retries or 3
        
        logger.info("StockMarketClient initialized successfully")
    
    def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to the Alpha Vantage API.
        
        Args:
            params: Request parameters
            
        Returns:
            API response data
            
        Raises:
            ConnectionError: If there's a connection issue
            RateLimitError: If rate limit is exceeded
            APIError: If there's an API error
        """
        params['apikey'] = self.api_key
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Making API request: {params.get('function', 'unknown')}")
                response = requests.get(
                    self.base_url, 
                    params=params, 
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                
                # Check for API errors
                if 'Error Message' in data:
                    error_msg = data['Error Message']
                    logger.error(f"API Error: {error_msg}")
                    raise APIError(f"Alpha Vantage API Error: {error_msg}")
                
                # Check for rate limiting
                if 'Note' in data:
                    note = data['Note']
                    logger.warning(f"API Rate Limit: {note}")
                    raise RateLimitError(f"Alpha Vantage Rate Limit: {note}")
                
                return data
                
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{self.max_retries})")
                if attempt == self.max_retries - 1:
                    raise ConnectionError("Request timeout after all retries")
                    
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error: {e}")
                raise ConnectionError(f"Failed to connect to Alpha Vantage API: {e}")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error: {e}")
                raise APIError(f"Request failed: {e}")
        
        # This should never be reached, but mypy requires it
        raise APIError("Request failed after all retries")
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get real-time quote for a stock symbol.
        
        Args:
            symbol (str): Stock symbol (e.g., 'AAPL', 'MSFT')
            
        Returns:
            Dict containing quote information
            
        Raises:
            InvalidArgsError: If symbol is invalid
            APIError: If API request fails
        """
        if not symbol or not isinstance(symbol, str):
            raise InvalidArgsError("Symbol must be a non-empty string")
        
        symbol = symbol.upper().strip()
        logger.info(f"Fetching quote for symbol: {symbol}")
        
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol
        }
        
        try:
            data = self._make_request(params)
            quote_data = data.get('Global Quote', {})
            
            if not quote_data:
                logger.warning(f"No quote data found for symbol: {symbol}")
                return {}
            
            logger.info(f"Successfully fetched quote for {symbol}")
            return quote_data
            
        except Exception as e:
            logger.error(f"Failed to fetch quote for {symbol}: {e}")
            raise
    
    def get_daily_data(self, symbol: str, outputsize: str = 'compact') -> Dict[str, Any]:
        """
        Get daily historical data for a stock symbol.
        
        Args:
            symbol (str): Stock symbol (e.g., 'AAPL', 'MSFT')
            outputsize (str): 'compact' (last 100 data points) or 'full' (up to 20 years)
            
        Returns:
            Dict containing daily time series data
            
        Raises:
            InvalidArgsError: If arguments are invalid
            APIError: If API request fails
        """
        if not symbol or not isinstance(symbol, str):
            raise InvalidArgsError("Symbol must be a non-empty string")
        
        if outputsize not in ['compact', 'full']:
            raise InvalidArgsError("Output size must be 'compact' or 'full'")
        
        symbol = symbol.upper().strip()
        logger.info(f"Fetching daily data for symbol: {symbol}, outputsize: {outputsize}")
        
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'outputsize': outputsize
        }
        
        try:
            data = self._make_request(params)
            
            if not data.get('Time Series (Daily)'):
                logger.warning(f"No daily data found for symbol: {symbol}")
                return {}
            
            logger.info(f"Successfully fetched daily data for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch daily data for {symbol}: {e}")
            raise
    
    def get_intraday_data(self, symbol: str, interval: str = '5min', outputsize: str = 'compact') -> Dict[str, Any]:
        """
        Get intraday data for a stock symbol.
        
        Args:
            symbol (str): Stock symbol (e.g., 'AAPL', 'MSFT')
            interval (str): Time interval ('1min', '5min', '15min', '30min', '60min')
            outputsize (str): 'compact' (last 100 data points) or 'full'
            
        Returns:
            Dict containing intraday time series data
            
        Raises:
            InvalidArgsError: If arguments are invalid
            APIError: If API request fails
        """
        if not symbol or not isinstance(symbol, str):
            raise InvalidArgsError("Symbol must be a non-empty string")
        
        valid_intervals = ['1min', '5min', '15min', '30min', '60min']
        if interval not in valid_intervals:
            raise InvalidArgsError(f"Interval must be one of: {valid_intervals}")
        
        if outputsize not in ['compact', 'full']:
            raise InvalidArgsError("Output size must be 'compact' or 'full'")
        
        symbol = symbol.upper().strip()
        logger.info(f"Fetching intraday data for symbol: {symbol}, interval: {interval}")
        
        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': symbol,
            'interval': interval,
            'outputsize': outputsize
        }
        
        try:
            data = self._make_request(params)
            
            # Find the time series key
            time_series_key = None
            for key in data.keys():
                if 'Time Series' in key:
                    time_series_key = key
                    break
            
            if not time_series_key or not data.get(time_series_key):
                logger.warning(f"No intraday data found for symbol: {symbol}")
                return {}
            
            logger.info(f"Successfully fetched intraday data for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch intraday data for {symbol}: {e}")
            raise
    
    def search_stocks(self, keywords: str) -> List[Dict[str, Any]]:
        """
        Search for stocks by keywords.
        
        Args:
            keywords (str): Search keywords
            
        Returns:
            List of matching stocks
            
        Raises:
            InvalidArgsError: If keywords are invalid
            APIError: If API request fails
        """
        if not keywords or not isinstance(keywords, str):
            raise InvalidArgsError("Keywords must be a non-empty string")
        
        keywords = keywords.strip()
        logger.info(f"Searching stocks with keywords: {keywords}")
        
        params = {
            'function': 'SYMBOL_SEARCH',
            'keywords': keywords
        }
        
        try:
            data = self._make_request(params)
            matches = data.get('bestMatches', [])
            
            logger.info(f"Found {len(matches)} matches for keywords: {keywords}")
            return matches
            
        except Exception as e:
            logger.error(f"Failed to search stocks with keywords '{keywords}': {e}")
            raise
    
    def get_company_overview(self, symbol: str) -> Dict[str, Any]:
        """
        Get company overview information.
        
        Args:
            symbol (str): Stock symbol (e.g., 'AAPL', 'MSFT')
            
        Returns:
            Dict containing company overview data
            
        Raises:
            InvalidArgsError: If symbol is invalid
            APIError: If API request fails
        """
        if not symbol or not isinstance(symbol, str):
            raise InvalidArgsError("Symbol must be a non-empty string")
        
        symbol = symbol.upper().strip()
        logger.info(f"Fetching company overview for symbol: {symbol}")
        
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol
        }
        
        try:
            data = self._make_request(params)
            
            if not data or len(data) <= 1:  # Only has Symbol key or empty
                logger.warning(f"No company overview found for symbol: {symbol}")
                return {}
            
            logger.info(f"Successfully fetched company overview for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch company overview for {symbol}: {e}")
            raise
    
    def get_market_status(self) -> Dict[str, Any]:
        """
        Get current market status (open/closed).
        
        Returns:
            Dict containing market status information
            
        Raises:
            APIError: If API request fails
        """
        logger.info("Fetching market status")
        
        params = {
            'function': 'MARKET_STATUS'
        }
        
        try:
            data = self._make_request(params)
            
            if not data.get('markets'):
                logger.warning("No market status data found")
                return {}
            
            logger.info("Successfully fetched market status")
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch market status: {e}")
            raise
    
    def get_top_gainers_losers(self) -> Dict[str, Any]:
        """
        Get top gainers and losers for the day.
        
        Returns:
            Dict containing top gainers and losers
            
        Raises:
            APIError: If API request fails
        """
        logger.info("Fetching top gainers and losers")
        
        params = {
            'function': 'TOP_GAINERS_LOSERS'
        }
        
        try:
            data = self._make_request(params)
            
            if not data.get('top_gainers') and not data.get('top_losers'):
                logger.warning("No gainers/losers data found")
                return {}
            
            logger.info("Successfully fetched top gainers and losers")
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch top gainers/losers: {e}")
            raise 