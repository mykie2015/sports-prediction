"""
Tennis Feature Extractor - Convert API data to ML features.

This module extracts numerical features from raw API data for ML models.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class TennisFeatureExtractor:
    """
    Extracts ML features from tennis player data.
    
    Features extracted:
    - Ranking features (current ranking, ranking difference)
    - Age and experience features
    - Head-to-head statistics
    - Recent form (win rate in last N matches)
    - Surface-specific performance
    - Tournament-specific performance
    - Physical attributes
    """
    
    def extract_match_features(
        self,
        player1_stats: Dict[str, Any],
        player2_stats: Dict[str, Any],
        h2h_data: Optional[Dict[str, Any]] = None,
        surface: str = "hard",
        tournament_name: str = ""
    ) -> Dict[str, float]:
        """
        Extract all features for a match prediction.
        
        Args:
            player1_stats: Player 1 data from API
            player2_stats: Player 2 data from API
            h2h_data: Head-to-head data (optional)
            surface: Court surface (hard/clay/grass)
            tournament_name: Tournament name for context
            
        Returns:
            Dictionary of feature_name -> feature_value
        """
        features = {}
        
        # Extract player info
        p1_info = player1_stats.get('team', {}).get('playerTeamInfo', {})
        p2_info = player2_stats.get('team', {}).get('playerTeamInfo', {})
        
        p1_team = player1_stats.get('team', {})
        p2_team = player2_stats.get('team', {})
        
        # 1. Ranking Features
        features.update(self._extract_ranking_features(p1_info, p2_info))
        
        # 2. Age & Experience Features
        features.update(self._extract_age_features(p1_info, p2_info))
        
        # 3. Prize Money (proxy for career success)
        features.update(self._extract_prize_features(p1_info, p2_info))
        
        # 4. Physical Features
        features.update(self._extract_physical_features(p1_info, p2_info))
        
        # 5. Head-to-Head Features (if available)
        if h2h_data:
            features.update(self._extract_h2h_features(h2h_data, player1_stats, player2_stats))
        else:
            # Default H2H features if no data
            features.update({
                'h2h_total_matches': 0.0,
                'h2h_p1_wins': 0.0,
                'h2h_p2_wins': 0.0,
                'h2h_p1_win_rate': 0.5,  # Neutral
            })
        
        # 6. Surface encoding
        features.update(self._encode_surface(surface))
        
        # 7. Tournament importance (Grand Slam indicator)
        features['is_grand_slam'] = 1.0 if any(
            gs in tournament_name.lower() 
            for gs in ['australian open', 'french open', 'wimbledon', 'us open', 'roland garros']
        ) else 0.0
        
        return features
    
    def _extract_ranking_features(self, p1_info: Dict, p2_info: Dict) -> Dict[str, float]:
        """Extract ranking-related features."""
        p1_rank = p1_info.get('currentRanking', 100)
        p2_rank = p2_info.get('currentRanking', 100)
        
        return {
            'p1_ranking': float(p1_rank),
            'p2_ranking': float(p2_rank),
            'ranking_diff': float(p1_rank - p2_rank),
            'ranking_ratio': float(p1_rank) / float(p2_rank) if p2_rank > 0 else 1.0,
            'p1_is_higher_ranked': 1.0 if p1_rank < p2_rank else 0.0,
        }
    
    def _extract_age_features(self, p1_info: Dict, p2_info: Dict) -> Dict[str, float]:
        """Extract age and experience features."""
        p1_age = self._calculate_age(p1_info.get('birthDateTimestamp', 0))
        p2_age = self._calculate_age(p2_info.get('birthDateTimestamp', 0))
        
        # Professional experience (years since turning pro)
        current_year = datetime.now(timezone.utc).year
        p1_pro_year = int(p1_info.get('turnedPro', current_year))
        p2_pro_year = int(p2_info.get('turnedPro', current_year))
        
        p1_experience = current_year - p1_pro_year
        p2_experience = current_year - p2_pro_year
        
        return {
            'p1_age': float(p1_age),
            'p2_age': float(p2_age),
            'age_diff': float(p1_age - p2_age),
            'p1_experience_years': float(p1_experience),
            'p2_experience_years': float(p2_experience),
            'experience_diff': float(p1_experience - p2_experience),
        }
    
    def _extract_prize_features(self, p1_info: Dict, p2_info: Dict) -> Dict[str, float]:
        """Extract prize money features (career success indicator)."""
        p1_total = p1_info.get('prizeTotal', 0)
        p2_total = p2_info.get('prizeTotal', 0)
        
        # Use log scale for prize money (reduces skew)
        import math
        p1_log_prize = math.log1p(p1_total)  # log(1 + x) to handle zeros
        p2_log_prize = math.log1p(p2_total)
        
        return {
            'p1_prize_log': p1_log_prize,
            'p2_prize_log': p2_log_prize,
            'prize_diff_log': p1_log_prize - p2_log_prize,
        }
    
    def _extract_physical_features(self, p1_info: Dict, p2_info: Dict) -> Dict[str, float]:
        """Extract physical attributes."""
        p1_height = p1_info.get('height', 1.80)  # Default 1.80m
        p2_height = p2_info.get('height', 1.80)
        
        p1_weight = p1_info.get('weight', 75.0)  # Default 75kg
        p2_weight = p2_info.get('weight', 75.0)
        
        return {
            'p1_height': float(p1_height),
            'p2_height': float(p2_height),
            'height_diff': float(p1_height - p2_height),
            'p1_weight': float(p1_weight),
            'p2_weight': float(p2_weight),
        }
    
    def _extract_h2h_features(
        self, 
        h2h_data: Dict[str, Any], 
        player1_stats: Dict, 
        player2_stats: Dict
    ) -> Dict[str, float]:
        """Extract head-to-head features."""
        # This would parse actual H2H data from API
        # For now, return placeholder features
        # TODO: Implement actual H2H parsing when we have real H2H data structure
        
        return {
            'h2h_total_matches': 0.0,
            'h2h_p1_wins': 0.0,
            'h2h_p2_wins': 0.0,
            'h2h_p1_win_rate': 0.5,
        }
    
    def _encode_surface(self, surface: str) -> Dict[str, float]:
        """One-hot encode court surface."""
        surface_lower = surface.lower()
        
        return {
            'surface_hard': 1.0 if 'hard' in surface_lower else 0.0,
            'surface_clay': 1.0 if 'clay' in surface_lower else 0.0,
            'surface_grass': 1.0 if 'grass' in surface_lower else 0.0,
        }
    
    def _calculate_age(self, birth_timestamp: int) -> int:
        """Calculate age from birth timestamp."""
        if not birth_timestamp:
            return 25  # Default age
        
        birth_date = datetime.fromtimestamp(birth_timestamp, tz=timezone.utc)
        today = datetime.now(timezone.utc)
        age = today.year - birth_date.year
        
        # Adjust if birthday hasn't occurred this year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
        
        return age
    
    def get_feature_names(self) -> List[str]:
        """Return list of all feature names in order."""
        return [
            # Ranking (5 features)
            'p1_ranking', 'p2_ranking', 'ranking_diff', 'ranking_ratio', 'p1_is_higher_ranked',
            
            # Age & Experience (6 features)
            'p1_age', 'p2_age', 'age_diff',
            'p1_experience_years', 'p2_experience_years', 'experience_diff',
            
            # Prize Money (3 features)
            'p1_prize_log', 'p2_prize_log', 'prize_diff_log',
            
            # Physical (5 features)
            'p1_height', 'p2_height', 'height_diff', 'p1_weight', 'p2_weight',
            
            # H2H (4 features)
            'h2h_total_matches', 'h2h_p1_wins', 'h2h_p2_wins', 'h2h_p1_win_rate',
            
            # Surface (3 features)
            'surface_hard', 'surface_clay', 'surface_grass',
            
            # Tournament (1 feature)
            'is_grand_slam',
        ]
