#!/usr/bin/env python3
"""
Tests for the StockMarketClient.

These tests verify that the StockMarketClient works correctly with the Alpha Vantage API.
All tests are fully mocked to avoid making actual API calls.
"""

import unittest
import os
import sys
from unittest.mock import patch, Mock, MagicMock
import requests

# Patch the logger before any imports that might use it
patcher = patch('utils.logger.get_logger', return_value=MagicMock())
patcher.start()

# Add the parent directory to the path so we can import our client
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clients.alpha_vantage.client import StockMarketClient
from clients.alpha_vantage.client import InvalidArgsError, APIError, RateLimitError, ConnectionError

class TestStockMarketClient(unittest.TestCase):
    """Test cases for StockMarketClient."""
    
    def setUp(self):
        """Set up test fixtures."""
        # For testing, we'll use a mock API key
        self.api_key = "test_api_key"
        self.client = StockMarketClient(self.api_key)
    
    def test_init_with_api_key(self):
        """Test client initialization with API key."""
        client = StockMarketClient("test_api_key")
        self.assertEqual(client.api_key, "test_api_key")
        self.assertEqual(client.base_url, "https://www.alphavantage.co/query")
        self.assertEqual(client.timeout, 30)
        self.assertEqual(client.max_retries, 3)
    
    def test_init_with_custom_parameters(self):
        """Test client initialization with custom parameters."""
        client = StockMarketClient(
            api_key="custom_key",
            base_url="https://custom.url",
            timeout=60,
            max_retries=5
        )
        self.assertEqual(client.api_key, "custom_key")
        self.assertEqual(client.base_url, "https://custom.url")
        self.assertEqual(client.timeout, 60)
        self.assertEqual(client.max_retries, 5)
    
    def test_init_without_api_key(self):
        """Test client initialization without API key raises error."""
        with self.assertRaises(InvalidArgsError):
            StockMarketClient()
    
    @patch('requests.get')
    def test_get_quote_success(self, mock_get):
        """Test successful quote retrieval."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            'Global Quote': {
                '01. symbol': 'AAPL',
                '05. price': '150.00',
                '09. change': '2.50',
                '10. change percent': '1.69%'
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.client.get_quote("AAPL")
        
        self.assertEqual(result['01. symbol'], 'AAPL')
        self.assertEqual(result['05. price'], '150.00')
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_get_quote_rate_limit(self, mock_get):
        """Test quote retrieval with rate limit."""
        # Mock rate limit response
        mock_response = Mock()
        mock_response.json.return_value = {
            'Note': 'Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute and 500 calls per day.'
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with self.assertRaises(RateLimitError):
            self.client.get_quote("AAPL")
    
    @patch('requests.get')
    def test_get_quote_api_error(self, mock_get):
        """Test quote retrieval with API error."""
        # Mock API error response
        mock_response = Mock()
        mock_response.json.return_value = {
            'Error Message': 'Invalid API call. Please retry or visit the documentation (https://www.alphavantage.co/documentation/) for TIME_SERIES_DAILY.'
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with self.assertRaises(APIError):
            self.client.get_quote("INVALID")
    
    @patch('requests.get')
    def test_get_quote_connection_error(self, mock_get):
        """Test quote retrieval with connection error."""
        # Mock connection error
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with self.assertRaises(ConnectionError):
            self.client.get_quote("AAPL")
    
    @patch('requests.get')
    def test_get_quote_timeout_error(self, mock_get):
        """Test quote retrieval with timeout error."""
        # Mock timeout error
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")
        
        with self.assertRaises(ConnectionError):
            self.client.get_quote("AAPL")
    
    @patch('requests.get')
    def test_search_stocks_success(self, mock_get):
        """Test successful stock search."""
        # Mock successful search response
        mock_response = Mock()
        mock_response.json.return_value = {
            'bestMatches': [
                {
                    '1. symbol': 'TSLA',
                    '2. name': 'Tesla Inc',
                    '3. type': 'Equity',
                    '4. region': 'United States'
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.client.search_stocks("Tesla")
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['1. symbol'], 'TSLA')
        self.assertEqual(result[0]['2. name'], 'Tesla Inc')
    
    @patch('requests.get')
    def test_get_company_overview_success(self, mock_get):
        """Test successful company overview retrieval."""
        # Mock successful overview response
        mock_response = Mock()
        mock_response.json.return_value = {
            'Symbol': 'MSFT',
            'Name': 'Microsoft Corporation',
            'Sector': 'Technology',
            'Industry': 'Software—Infrastructure',
            'MarketCapitalization': '2500000000000'
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.client.get_company_overview("MSFT")
        
        self.assertEqual(result['Symbol'], 'MSFT')
        self.assertEqual(result['Name'], 'Microsoft Corporation')
        self.assertEqual(result['Sector'], 'Technology')
    
    @patch('requests.get')
    def test_get_daily_data_success(self, mock_get):
        """Test successful daily data retrieval."""
        # Mock successful daily data response
        mock_response = Mock()
        mock_response.json.return_value = {
            'Time Series (Daily)': {
                '2023-01-01': {
                    '1. open': '150.00',
                    '2. high': '155.00',
                    '3. low': '148.00',
                    '4. close': '152.00',
                    '5. volume': '1000000'
                }
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.client.get_daily_data("AAPL")
        
        self.assertIn('Time Series (Daily)', result)
        self.assertIn('2023-01-01', result['Time Series (Daily)'])
    
    @patch('requests.get')
    def test_get_intraday_data_success(self, mock_get):
        """Test successful intraday data retrieval."""
        # Mock successful intraday data response
        mock_response = Mock()
        mock_response.json.return_value = {
            'Time Series (5min)': {
                '2023-01-01 09:30:00': {
                    '1. open': '150.00',
                    '2. high': '151.00',
                    '3. low': '149.00',
                    '4. close': '150.50',
                    '5. volume': '100000'
                }
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.client.get_intraday_data("AAPL", interval="5min")
        
        self.assertIn('Time Series (5min)', result)
        self.assertIn('2023-01-01 09:30:00', result['Time Series (5min)'])
    
    def test_invalid_symbol(self):
        """Test quote retrieval with invalid symbol."""
        with self.assertRaises(InvalidArgsError):
            self.client.get_quote("")
        
        with self.assertRaises(InvalidArgsError):
            self.client.get_quote(None)  # type: ignore
    
    def test_invalid_outputsize(self):
        """Test daily data retrieval with invalid outputsize."""
        with self.assertRaises(InvalidArgsError):
            self.client.get_daily_data("AAPL", outputsize="invalid")
    
    def test_invalid_interval(self):
        """Test intraday data retrieval with invalid interval."""
        with self.assertRaises(InvalidArgsError):
            self.client.get_intraday_data("AAPL", interval="invalid")
    
    def test_invalid_keywords(self):
        """Test stock search with invalid keywords."""
        with self.assertRaises(InvalidArgsError):
            self.client.search_stocks("")
        
        with self.assertRaises(InvalidArgsError):
            self.client.search_stocks(None)  # type: ignore

if __name__ == '__main__':
    unittest.main() 