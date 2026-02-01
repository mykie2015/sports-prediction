import pytest
from unittest.mock import MagicMock
from src.sports_prediction.sports.tennis.fetcher import TennisAPIFetcher
from src.sports_prediction.data.api_client import APIClient
from src.sports_prediction.core.database import DatabaseManager

class TestTennisAPIFetcher:
    @pytest.fixture
    def mock_api_client(self):
        client = MagicMock(spec=APIClient)
        # Setup get method
        client.get.return_value = {}
        return client

    @pytest.fixture
    def mock_db_manager(self):
        manager = MagicMock(spec=DatabaseManager)
        # Mock context manager for get_connection
        manager.get_connection.return_value.__enter__.return_value = MagicMock()
        return manager

    @pytest.fixture
    def fetcher(self, mock_api_client, mock_db_manager):
        return TennisAPIFetcher(api_client=mock_api_client, db_manager=mock_db_manager)

    def test_fetch_player_stats_api_call(self, fetcher, mock_api_client, mock_db_manager):
        """Test API call when cache is empty."""
        # Setup mock to return None from cache (simulating cache miss)
        # Note: fetcher checks cache via SQL queries now, so we need to mock the cursor
        conn = mock_db_manager.get_connection.return_value.__enter__.return_value
        cursor = conn.cursor.return_value
        cursor.fetchone.return_value = None  # Cache miss
        
        mock_api_client.get.return_value = {"player": "data"}
        
        fetcher.fetch_player_stats(player_id=1)
        
        mock_api_client.get.assert_called_with("/players", params={"id": 1})
        # Verify cache save method was called
        mock_db_manager.save_sports_data.assert_called_once()
        args = mock_db_manager.save_sports_data.call_args[0]
        assert args[0].sport == "tennis"
        assert args[0].data_type == "player_stats"
        assert args[0].entity_id == "1"

    def test_fetch_h2h_api_call(self, fetcher, mock_api_client, mock_db_manager):
        """Test H2H fetching logic."""
        conn = mock_db_manager.get_connection.return_value.__enter__.return_value
        cursor = conn.cursor.return_value
        cursor.fetchone.return_value = None  # Cache miss
        
        mock_api_client.get.return_value = {"h2h": "data"}
        
        fetcher.fetch_head_to_head(player1_id=1, player2_id=2)
        
        # Verify params (sorted IDs)
        mock_api_client.get.assert_called_with("/headtohead", params={"h2h": "1-2"})
        
        mock_db_manager.save_sports_data.assert_called_once()
        args = mock_db_manager.save_sports_data.call_args[0]
        assert args[0].data_type == "h2h"
        assert args[0].entity_id == "1-2"

    def test_fetch_matches_api_call(self, fetcher, mock_api_client, mock_db_manager):
        """Test Matches fetching logic."""
        conn = mock_db_manager.get_connection.return_value.__enter__.return_value
        cursor = conn.cursor.return_value
        cursor.fetchone.return_value = None  # Cache miss

        mock_api_client.get.return_value = {"matches": []}
        
        fetcher.fetch_matches(player_id=1)
        
        mock_api_client.get.assert_called_with("/matches", params={"id": 1})
        
        mock_db_manager.save_sports_data.assert_called_once()
        args = mock_db_manager.save_sports_data.call_args[0]
        assert args[0].data_type == "player_matches"

