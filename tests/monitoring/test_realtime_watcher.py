"""
Test suite for RealTimeWatcher class.

Tests cover:
1. Initialization and configuration
2. Watchlist management (add/remove stocks)
3. Quote fetching (single and batch)
4. Quote updates and caching
5. Error handling (network failures, invalid codes)
6. Data validation and timestamps
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from src.monitoring.realtime_watcher import RealTimeWatcher


# ============================================================================
# 1. Initialization Tests (3 tests)
# ============================================================================

def test_init_with_empty_list():
    """Test initialization with empty stock list."""
    watcher = RealTimeWatcher(stock_list=[], update_interval=60)

    assert watcher.update_interval == 60
    assert len(watcher.watchlist) == 0
    assert watcher.quotes == {}


def test_init_with_stock_list():
    """Test initialization with stock list."""
    stock_list = [
        {'code': '600519', 'name': '贵州茅台'},
        {'code': '000858', 'name': '五粮液'}
    ]
    watcher = RealTimeWatcher(stock_list=stock_list, update_interval=30)

    assert watcher.update_interval == 30
    assert len(watcher.watchlist) == 2
    assert '600519' in watcher.watchlist
    assert '000858' in watcher.watchlist
    assert watcher.watchlist['600519'] == '贵州茅台'


def test_init_default_interval():
    """Test initialization uses default interval when not specified."""
    watcher = RealTimeWatcher(stock_list=[])

    assert watcher.update_interval == 60  # default


# ============================================================================
# 2. Watchlist Management Tests (5 tests)
# ============================================================================

def test_add_stock_to_watchlist():
    """Test adding a stock to watchlist."""
    watcher = RealTimeWatcher(stock_list=[])

    watcher.add_stock('600519', '贵州茅台')

    assert '600519' in watcher.watchlist
    assert watcher.watchlist['600519'] == '贵州茅台'
    assert len(watcher.watchlist) == 1


def test_add_duplicate_stock():
    """Test adding duplicate stock updates the name."""
    watcher = RealTimeWatcher(stock_list=[])

    watcher.add_stock('600519', '茅台')
    watcher.add_stock('600519', '贵州茅台')

    assert watcher.watchlist['600519'] == '贵州茅台'
    assert len(watcher.watchlist) == 1


def test_remove_stock_from_watchlist():
    """Test removing a stock from watchlist."""
    watcher = RealTimeWatcher(stock_list=[
        {'code': '600519', 'name': '贵州茅台'},
        {'code': '000858', 'name': '五粮液'}
    ])

    removed = watcher.remove_stock('600519')

    assert removed is True
    assert '600519' not in watcher.watchlist
    assert len(watcher.watchlist) == 1
    # Quote should also be removed
    if '600519' in watcher.quotes:
        pytest.fail("Quote should be removed with stock")


def test_remove_nonexistent_stock():
    """Test removing non-existent stock returns False."""
    watcher = RealTimeWatcher(stock_list=[])

    removed = watcher.remove_stock('999999')

    assert removed is False


def test_get_watchlist():
    """Test getting current watchlist."""
    stock_list = [
        {'code': '600519', 'name': '贵州茅台'},
        {'code': '000858', 'name': '五粮液'}
    ]
    watcher = RealTimeWatcher(stock_list=stock_list)

    watchlist = watcher.get_watchlist()

    assert len(watchlist) == 2
    assert '600519' in watchlist
    assert watchlist['600519'] == '贵州茅台'


# ============================================================================
# 3. Quote Fetching Tests (4 tests)
# ============================================================================

@patch('src.monitoring.realtime_watcher.AKShareProvider')
def test_get_latest_quote_success(mock_provider):
    """Test getting latest quote for a single stock."""
    # Setup mock
    mock_instance = Mock()
    mock_instance.get_realtime_quote.return_value = {
        'code': '600519',
        'name': '贵州茅台',
        'current_price': 1650.5,
        'open': 1645.0,
        'high': 1660.0,
        'low': 1640.0,
        'volume': 1234567,
        'amount': 2.03e9,
        'change_pct': 0.0234
    }
    mock_provider.return_value = mock_instance

    watcher = RealTimeWatcher(stock_list=[])
    watcher.add_stock('600519', '贵州茅台')

    quote = watcher.get_latest_quote('600519')

    assert quote is not None
    assert quote['code'] == '600519'
    assert quote['name'] == '贵州茅台'
    assert quote['current_price'] == 1650.5
    assert 'update_time' in quote


@patch('src.monitoring.realtime_watcher.AKShareProvider')
def test_get_latest_quote_not_in_watchlist(mock_provider):
    """Test getting quote for stock not in watchlist returns None."""
    watcher = RealTimeWatcher(stock_list=[])

    quote = watcher.get_latest_quote('999999')

    assert quote is None


@patch('src.monitoring.realtime_watcher.AKShareProvider')
def test_get_all_quotes_success(mock_provider):
    """Test getting quotes for all stocks in watchlist."""
    # Setup mock
    mock_instance = Mock()
    mock_instance.get_realtime_quotes.return_value = {
        '600519': {
            'code': '600519',
            'name': '贵州茅台',
            'current_price': 1650.5,
            'change_pct': 0.0234
        },
        '000858': {
            'code': '000858',
            'name': '五粮液',
            'current_price': 180.3,
            'change_pct': -0.0156
        }
    }
    mock_provider.return_value = mock_instance

    watcher = RealTimeWatcher(stock_list=[
        {'code': '600519', 'name': '贵州茅台'},
        {'code': '000858', 'name': '五粮液'}
    ])

    # Update quotes first
    watcher.update_quotes()

    quotes = watcher.get_all_quotes()

    assert len(quotes) == 2
    assert '600519' in quotes
    assert '000858' in quotes
    assert quotes['600519']['current_price'] == 1650.5


@patch('src.monitoring.realtime_watcher.AKShareProvider')
def test_get_all_quotes_empty_watchlist(mock_provider):
    """Test getting quotes with empty watchlist returns empty dict."""
    watcher = RealTimeWatcher(stock_list=[])

    quotes = watcher.get_all_quotes()

    assert quotes == {}


# ============================================================================
# 4. Update and Caching Tests (5 tests)
# ============================================================================

@patch('src.monitoring.realtime_watcher.AKShareProvider')
def test_update_quotes_refreshes_data(mock_provider):
    """Test update_quotes refreshes all quotes."""
    mock_instance = Mock()
    mock_instance.get_realtime_quotes.return_value = {
        '600519': {
            'code': '600519',
            'name': '贵州茅台',
            'current_price': 1650.5,
            'change_pct': 0.0234
        }
    }
    mock_provider.return_value = mock_instance

    watcher = RealTimeWatcher(stock_list=[{'code': '600519', 'name': '贵州茅台'}])

    # Initial state
    assert len(watcher.quotes) == 0

    # Update
    watcher.update_quotes()

    assert len(watcher.quotes) == 1
    assert '600519' in watcher.quotes


@patch('src.monitoring.realtime_watcher.AKShareProvider')
def test_quotes_have_update_timestamp(mock_provider):
    """Test quotes include update timestamp."""
    mock_instance = Mock()
    mock_instance.get_realtime_quotes.return_value = {
        '600519': {
            'code': '600519',
            'current_price': 1650.5
        }
    }
    mock_provider.return_value = mock_instance

    watcher = RealTimeWatcher(stock_list=[{'code': '600519', 'name': '贵州茅台'}])
    watcher.update_quotes()

    quote = watcher.get_latest_quote('600519')

    assert 'update_time' in quote
    assert isinstance(quote['update_time'], datetime)


@patch('src.monitoring.realtime_watcher.AKShareProvider')
def test_cache_returns_recent_data(mock_provider):
    """Test cached quotes are returned without API call."""
    mock_instance = Mock()
    mock_instance.get_realtime_quotes.return_value = {
        '600519': {'code': '600519', 'current_price': 1650.5}
    }
    mock_provider.return_value = mock_instance

    watcher = RealTimeWatcher(stock_list=[{'code': '600519', 'name': '贵州茅台'}])

    # First call - fetches from API
    watcher.update_quotes()
    assert mock_instance.get_realtime_quotes.call_count == 1

    # Second call immediately - uses cache
    quote = watcher.get_latest_quote('600519')
    assert quote is not None
    # Should still be 1 API call (cached)
    assert mock_instance.get_realtime_quotes.call_count == 1


@patch('src.monitoring.realtime_watcher.AKShareProvider')
def test_force_update_bypasses_cache(mock_provider):
    """Test force update bypasses cache."""
    mock_instance = Mock()
    mock_instance.get_realtime_quotes.return_value = {
        '600519': {'code': '600519', 'current_price': 1650.5}
    }
    mock_provider.return_value = mock_instance

    watcher = RealTimeWatcher(stock_list=[{'code': '600519', 'name': '贵州茅台'}])

    # First update
    watcher.update_quotes()
    assert mock_instance.get_realtime_quotes.call_count == 1

    # Force update
    watcher.update_quotes(force=True)
    assert mock_instance.get_realtime_quotes.call_count == 2


@patch('src.monitoring.realtime_watcher.AKShareProvider')
def test_stale_cache_auto_refreshes(mock_provider):
    """Test stale cache is automatically refreshed."""
    mock_instance = Mock()
    mock_instance.get_realtime_quote.return_value = {
        'code': '600519',
        'current_price': 1650.5
    }
    mock_provider.return_value = mock_instance

    watcher = RealTimeWatcher(stock_list=[{'code': '600519', 'name': '贵州茅台'}])

    # Manually set stale cache (2 minutes old)
    stale_time = datetime.now() - timedelta(minutes=2)
    watcher.quotes['600519'] = {
        'code': '600519',
        'current_price': 1600.0,
        'update_time': stale_time
    }

    # Get quote - should refresh because cache is stale
    quote = watcher.get_latest_quote('600519', max_age_seconds=60)

    assert quote['update_time'] > stale_time


# ============================================================================
# 5. Error Handling Tests (5 tests)
# ============================================================================

@patch('src.monitoring.realtime_watcher.AKShareProvider')
def test_handle_network_error_gracefully(mock_provider):
    """Test network errors are handled gracefully."""
    mock_instance = Mock()
    mock_instance.get_realtime_quotes.side_effect = Exception("Network error")
    mock_provider.return_value = mock_instance

    watcher = RealTimeWatcher(stock_list=[{'code': '600519', 'name': '贵州茅台'}])

    # Should not raise exception
    watcher.update_quotes()

    # Quotes should remain empty
    assert len(watcher.quotes) == 0


@patch('src.monitoring.realtime_watcher.AKShareProvider')
def test_invalid_stock_code_handling(mock_provider):
    """Test invalid stock codes are handled."""
    mock_instance = Mock()
    mock_instance.get_realtime_quote.return_value = None
    mock_provider.return_value = mock_instance

    watcher = RealTimeWatcher(stock_list=[])
    watcher.add_stock('INVALID', '无效股票')

    quote = watcher.get_latest_quote('INVALID')

    assert quote is None


@patch('src.monitoring.realtime_watcher.AKShareProvider')
def test_partial_failure_returns_available_quotes(mock_provider):
    """Test partial failures return available quotes."""
    mock_instance = Mock()
    # Return only one stock, simulating partial failure
    mock_instance.get_realtime_quotes.return_value = {
        '600519': {'code': '600519', 'current_price': 1650.5}
        # '000858' missing due to error
    }
    mock_provider.return_value = mock_instance

    watcher = RealTimeWatcher(stock_list=[
        {'code': '600519', 'name': '贵州茅台'},
        {'code': '000858', 'name': '五粮液'}
    ])
    watcher.update_quotes()

    quotes = watcher.get_all_quotes()

    assert '600519' in quotes
    # Should still work with partial data


@patch('src.monitoring.realtime_watcher.AKShareProvider')
def test_empty_response_handling(mock_provider):
    """Test empty API response is handled."""
    mock_instance = Mock()
    mock_instance.get_realtime_quotes.return_value = {}
    mock_provider.return_value = mock_instance

    watcher = RealTimeWatcher(stock_list=[{'code': '600519', 'name': '贵州茅台'}])
    watcher.update_quotes()

    quotes = watcher.get_all_quotes()

    assert quotes == {}


@patch('src.monitoring.realtime_watcher.AKShareProvider')
def test_malformed_data_handling(mock_provider):
    """Test malformed data is handled safely."""
    mock_instance = Mock()
    # Missing required fields
    mock_instance.get_realtime_quotes.return_value = {
        '600519': {'code': '600519'}  # Missing price data
    }
    mock_provider.return_value = mock_instance

    watcher = RealTimeWatcher(stock_list=[{'code': '600519', 'name': '贵州茅台'}])

    # Should handle gracefully
    watcher.update_quotes()

    # Should still store what we got
    quote = watcher.get_latest_quote('600519')
    assert quote is not None
    assert quote['code'] == '600519'


# ============================================================================
# 6. Data Validation Tests (3 tests)
# ============================================================================

@patch('src.monitoring.realtime_watcher.AKShareProvider')
def test_quote_has_required_fields(mock_provider):
    """Test quote contains all required fields."""
    mock_instance = Mock()
    mock_instance.get_realtime_quotes.return_value = {
        '600519': {
            'code': '600519',
            'name': '贵州茅台',
            'current_price': 1650.5,
            'open': 1645.0,
            'high': 1660.0,
            'low': 1640.0,
            'volume': 1234567,
            'amount': 2.03e9,
            'change_pct': 0.0234
        }
    }
    mock_provider.return_value = mock_instance

    watcher = RealTimeWatcher(stock_list=[{'code': '600519', 'name': '贵州茅台'}])
    watcher.update_quotes()

    quote = watcher.get_latest_quote('600519')

    required_fields = ['code', 'name', 'current_price', 'update_time']
    for field in required_fields:
        assert field in quote, f"Missing required field: {field}"


@patch('src.monitoring.realtime_watcher.AKShareProvider')
def test_price_is_numeric(mock_provider):
    """Test price fields are numeric."""
    mock_instance = Mock()
    mock_instance.get_realtime_quotes.return_value = {
        '600519': {
            'code': '600519',
            'current_price': 1650.5,
            'open': 1645.0,
            'high': 1660.0,
            'low': 1640.0
        }
    }
    mock_provider.return_value = mock_instance

    watcher = RealTimeWatcher(stock_list=[{'code': '600519', 'name': '贵州茅台'}])
    watcher.update_quotes()

    quote = watcher.get_latest_quote('600519')

    assert isinstance(quote['current_price'], (int, float))
    if 'open' in quote:
        assert isinstance(quote['open'], (int, float))


@patch('src.monitoring.realtime_watcher.AKShareProvider')
def test_timestamp_is_recent(mock_provider):
    """Test update timestamp is recent."""
    mock_instance = Mock()
    mock_instance.get_realtime_quotes.return_value = {
        '600519': {'code': '600519', 'current_price': 1650.5}
    }
    mock_provider.return_value = mock_instance

    watcher = RealTimeWatcher(stock_list=[{'code': '600519', 'name': '贵州茅台'}])
    watcher.update_quotes()

    quote = watcher.get_latest_quote('600519')

    # Timestamp should be within last 10 seconds
    time_diff = datetime.now() - quote['update_time']
    assert time_diff.total_seconds() < 10
