import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

from sports_prediction.core.database import DatabaseManager
from sports_prediction.core.models import SportsData
from sports_prediction.data.api_client import APIClient

logger = logging.getLogger(__name__)

class TennisAPIFetcher:
    """
    Fetcher for Tennis data using API-SPORTS.
    Handles fetching and caching of player stats, H2H, and match results.
    """

    def __init__(self, api_client: APIClient, db_manager: DatabaseManager):
        self.api_client = api_client
        self.db_manager = db_manager

    def _get_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate a unique cache key based on parameters."""
        # Create a deterministic string from kwargs
        params_str = "_".join(f"{k}_{v}" for k, v in sorted(kwargs.items()))
        return f"tennis:{prefix}:{params_str}"

    def _get_from_cache(self, entity_id: str, data_type: str) -> Optional[Dict[str, Any]]:
        """Retrieve valid data from cache if it exists and hasn't expired."""
        try:
            # In our schema, we filter by entity_id and data_type
            # Since get_sports_data takes an ID, we need to query by attributes
            # We'll use a direct SQL query here for efficiency since DatabaseManager doesn't expose search
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM sports_data 
                    WHERE sport = 'tennis' AND data_type = ? AND entity_id = ?
                    ORDER BY fetched_at DESC LIMIT 1
                    """,
                    (data_type, entity_id)
                )
                row = cursor.fetchone()
                
                if row:
                    expires_at_str = row['expires_at']
                    if expires_at_str:
                        expires_at = datetime.fromisoformat(expires_at_str)
                        # Ensure timezone awareness compatibility
                        if expires_at.tzinfo is None:
                            expires_at = expires_at.replace(tzinfo=timezone.utc)
                            
                        now = datetime.now(timezone.utc)
                        if now > expires_at:
                            logger.info(f"Cache expired for {data_type}:{entity_id}")
                            return None
                    
                    logger.info(f"Cache hit for {data_type}:{entity_id}")
                    return json.loads(row['data'])
                
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
            
        return None

    def _save_to_cache(self, entity_id: str, data_type: str, data: Dict[str, Any], ttl: Optional[timedelta] = None):
        """Save data to cache using SportsData model."""
        try:
            now = datetime.now(timezone.utc)
            expires_at = (now + ttl) if ttl else None
            
            sports_data = SportsData(
                sport="tennis",
                data_type=data_type,
                entity_id=entity_id,
                data=data,
                source="api-sports",
                fetched_at=now,
                expires_at=expires_at
            )
            
            # First, delete existing cache entry to avoid duplicates
            with self.db_manager.get_connection() as conn:
                conn.execute(
                    "DELETE FROM sports_data WHERE sport = 'tennis' AND data_type = ? AND entity_id = ?",
                    (data_type, entity_id)
                )
                conn.commit()
                
            self.db_manager.save_sports_data(sports_data)
            
        except Exception as e:
            logger.error(f"Cache write error: {e}")

    def fetch_player_stats(self, player_id: int) -> Dict[str, Any]:
        """
        Fetch player statistics (rankings, profile).
        Cache duration: 24 hours.
        """
        entity_id = str(player_id)
        data_type = "player_stats"
        
        cached = self._get_from_cache(entity_id, data_type)
        if cached:
            return cached
            
        # API call
        data = self.api_client.get("/players", params={"id": player_id})
        
        # Save to cache
        self._save_to_cache(entity_id, data_type, data, ttl=timedelta(hours=24))
        return data

    def fetch_head_to_head(self, player1_id: int, player2_id: int) -> Dict[str, Any]:
        """
        Fetch Head-to-Head records between two players.
        Cache duration: 7 days.
        """
        # Ensure consistent ordering for key
        p1, p2 = sorted([player1_id, player2_id])
        h2h_param = f"{p1}-{p2}"
        data_type = "h2h"
        
        cached = self._get_from_cache(h2h_param, data_type)
        if cached:
            return cached
        
        data = self.api_client.get("/headtohead", params={"h2h": h2h_param})
        
        self._save_to_cache(h2h_param, data_type, data, ttl=timedelta(days=7))
        return data

    def fetch_matches(self, player_id: int) -> Dict[str, Any]:
        """
        Fetch matches for a player.
        Cache duration: 1 hour (to allow updates).
        """
        entity_id = str(player_id)
        data_type = "player_matches"
        
        cached = self._get_from_cache(entity_id, data_type)
        if cached:
            return cached
        
        data = self.api_client.get("/matches", params={"id": player_id})
        
        self._save_to_cache(entity_id, data_type, data, ttl=timedelta(hours=1))
        return data
