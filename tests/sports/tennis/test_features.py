"""
Tests for Tennis Feature Extractor.
"""

import pytest
from sports_prediction.sports.tennis.features import TennisFeatureExtractor


class TestTennisFeatureExtractor:
    @pytest.fixture
    def extractor(self):
        return TennisFeatureExtractor()
    
    @pytest.fixture
    def sample_player1_stats(self):
        return {
            'team': {
                'playerTeamInfo': {
                    'currentRanking': 1,
                    'birthDateTimestamp': 1052092800,  # ~2003
                    'turnedPro': '2018',
                    'prizeTotal': 50000000,
                    'height': 1.83,
                    'weight': 74
                }
            }
        }
    
    @pytest.fixture
    def sample_player2_stats(self):
        return {
            'team': {
                'playerTeamInfo': {
                    'currentRanking': 7,
                    'birthDateTimestamp': 548640000,  # ~1987
                    'turnedPro': '2003',
                    'prizeTotal': 160000000,
                    'height': 1.88,
                    'weight': 82
                }
            }
        }
    
    def test_extract_match_features(self, extractor, sample_player1_stats, sample_player2_stats):
        """Test basic feature extraction."""
        features = extractor.extract_match_features(
            player1_stats=sample_player1_stats,
            player2_stats=sample_player2_stats,
            surface="hard",
            tournament_name="Australian Open"
        )
        
        # Check that all expected features are present
        feature_names = extractor.get_feature_names()
        assert len(features) == len(feature_names)
        
        for name in feature_names:
            assert name in features, f"Missing feature: {name}"
            assert isinstance(features[name], (int, float)), f"Feature {name} is not numeric"
    
    def test_ranking_features(self, extractor, sample_player1_stats, sample_player2_stats):
        """Test ranking feature extraction."""
        features = extractor.extract_match_features(
            sample_player1_stats, sample_player2_stats
        )
        
        assert features['p1_ranking'] == 1.0
        assert features['p2_ranking'] == 7.0
        assert features['ranking_diff'] == -6.0  # P1 has better rank (lower number)
        assert features['p1_is_higher_ranked'] == 1.0
    
    def test_age_features(self, extractor, sample_player1_stats, sample_player2_stats):
        """Test age calculation."""
        features = extractor.extract_match_features(
            sample_player1_stats, sample_player2_stats
        )
        
        # Player 1 (~22 years old), Player 2 (~38 years old)
        assert 20 <= features['p1_age'] <= 25
        assert 35 <= features['p2_age'] <= 40
        assert features['age_diff'] < 0  # P1 is younger
    
    def test_surface_encoding(self, extractor, sample_player1_stats, sample_player2_stats):
        """Test surface one-hot encoding."""
        # Hard court
        features_hard = extractor.extract_match_features(
            sample_player1_stats, sample_player2_stats, surface="hard"
        )
        assert features_hard['surface_hard'] == 1.0
        assert features_hard['surface_clay'] == 0.0
        assert features_hard['surface_grass'] == 0.0
        
        # Clay court
        features_clay = extractor.extract_match_features(
            sample_player1_stats, sample_player2_stats, surface="clay"
        )
        assert features_clay['surface_hard'] == 0.0
        assert features_clay['surface_clay'] == 1.0
        assert features_clay['surface_grass'] == 0.0
    
    def test_grand_slam_detection(self, extractor, sample_player1_stats, sample_player2_stats):
        """Test Grand Slam tournament detection."""
        # Grand Slam
        features_gs = extractor.extract_match_features(
            sample_player1_stats, sample_player2_stats,
            tournament_name="Australian Open 2026"
        )
        assert features_gs['is_grand_slam'] == 1.0
        
        # Regular tournament
        features_regular = extractor.extract_match_features(
            sample_player1_stats, sample_player2_stats,
            tournament_name="ATP Masters 1000"
        )
        assert features_regular['is_grand_slam'] == 0.0
    
    def test_prize_money_features(self, extractor, sample_player1_stats, sample_player2_stats):
        """Test prize money (log scale) features."""
        features = extractor.extract_match_features(
            sample_player1_stats, sample_player2_stats
        )
        
        # Both should have positive log prize money
        assert features['p1_prize_log'] > 0
        assert features['p2_prize_log'] > 0
        
        # P2 has more prize money, so should have higher log prize
        assert features['p2_prize_log'] > features['p1_prize_log']
        assert features['prize_diff_log'] < 0
    
    def test_physical_features(self, extractor, sample_player1_stats, sample_player2_stats):
        """Test physical attribute features."""
        features = extractor.extract_match_features(
            sample_player1_stats, sample_player2_stats
        )
        
        assert features['p1_height'] == 1.83
        assert features['p2_height'] == 1.88
        assert abs(features['height_diff'] - (-0.05)) < 0.001  # P1 is shorter (allow float precision)
        
        assert features['p1_weight'] == 74.0
        assert features['p2_weight'] == 82.0
    
    def test_feature_names_consistency(self, extractor):
        """Test that feature names list matches actual extraction."""
        sample_p1 = {'team': {'playerTeamInfo': {}}}
        sample_p2 = {'team': {'playerTeamInfo': {}}}
        
        features = extractor.extract_match_features(sample_p1, sample_p2)
        feature_names = extractor.get_feature_names()
        
        # All names should be in features
        for name in feature_names:
            assert name in features
        
        # All features should be in names
        for key in features.keys():
            assert key in feature_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
