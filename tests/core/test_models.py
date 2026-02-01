import unittest
from datetime import datetime, timezone
from src.sports_prediction.core.models import Competitor, Match, Prediction, Result, SportsData

class TestModels(unittest.TestCase):
    def test_competitor_creation(self):
        """Test creating a Competitor instance."""
        comp = Competitor(name="Roger Federer", sport="Tennis", metadata={"rank": 1})
        self.assertEqual(comp.name, "Roger Federer")
        self.assertEqual(comp.sport, "Tennis")
        self.assertEqual(comp.metadata["rank"], 1)

    def test_match_creation(self):
        """Test creating a Match instance."""
        c1 = Competitor(name="Nadal", sport="Tennis")
        c2 = Competitor(name="Djokovic", sport="Tennis")
        now = datetime.now(timezone.utc)
        
        match = Match(
            sport="Tennis",
            event_name="Roland Garros Final",
            event_date=now,
            competitor1=c1,
            competitor2=c2
        )
        
        self.assertEqual(match.sport, "Tennis")
        self.assertEqual(match.competitor1.name, "Nadal")

    def test_prediction_creation(self):
        """Test creating a Prediction instance."""
        c1 = Competitor(name="Lakers", sport="Basketball")
        c2 = Competitor(name="Celtics", sport="Basketball")
        now = datetime.now(timezone.utc)
        
        match = Match(
            sport="Basketball",
            event_name="NBA Finals",
            event_date=now,
            competitor1=c1,
            competitor2=c2
        )
        
        pred = Prediction(
            match=match,
            predicted_winner=c1,
            confidence=0.85,
            probability_c1=0.6,
            probability_c2=0.4,
            reasoning="Strong defense",
            factor_scores={"defense": 0.9},
            created_at=now
        )
        
        self.assertEqual(pred.match.event_name, "NBA Finals")
        self.assertEqual(pred.predicted_winner, c1)
        self.assertEqual(pred.confidence, 0.85)

    def test_result_creation(self):
        """Test creating a Result instance."""
        now = datetime.now(timezone.utc)
        result = Result(
            prediction_id=1,
            actual_winner="Lakers",
            score="100-98",
            fetched_from="NBA API",
            fetched_at=now,
            is_correct=True
        )
        self.assertEqual(result.actual_winner, "Lakers")
        self.assertTrue(result.is_correct)

    def test_sports_data_creation(self):
        """Test creating a SportsData instance."""
        now = datetime.now(timezone.utc)
        data = SportsData(
            sport="Tennis",
            data_type="rankings",
            entity_id="atp_rankings",
            data={"top_10": []},
            source="ATP",
            fetched_at=now
        )
        self.assertEqual(data.sport, "Tennis")
        self.assertEqual(data.data_type, "rankings")

if __name__ == '__main__':
    unittest.main()
