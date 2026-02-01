import unittest
import sqlite3
import json
from datetime import datetime, timezone
from src.sports_prediction.core.database import DatabaseManager
from src.sports_prediction.core.models import Competitor, Match, Prediction, Result, SportsData

class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        # Use in-memory database for testing
        self.db = DatabaseManager(":memory:")
        self.db.initialize_schema()

    def tearDown(self):
        self.db.close()

    def test_schema_creation(self):
        """Test that tables are created correctly."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = {row[0] for row in cursor.fetchall()}
            expected_tables = {'predictions', 'results', 'sports_data'}
            self.assertTrue(expected_tables.issubset(tables))

    def test_save_and_get_prediction(self):
        """Test saving and retrieving a prediction."""
        c1 = Competitor(name="Team A", sport="Football")
        c2 = Competitor(name="Team B", sport="Football")
        now = datetime.now(timezone.utc)
        
        match = Match(
            sport="Football",
            event_name="Super Bowl",
            event_date=now,
            competitor1=c1,
            competitor2=c2
        )
        
        pred = Prediction(
            match=match,
            predicted_winner=c1,
            confidence=0.9,
            probability_c1=0.7,
            probability_c2=0.3,
            reasoning="Stats",
            factor_scores={"offense": 0.8},
            created_at=now
        )
        
        pred_id = self.db.save_prediction(pred)
        self.assertIsNotNone(pred_id)
        
        fetched_pred = self.db.get_prediction(pred_id)
        self.assertEqual(fetched_pred.match.event_name, "Super Bowl")
        self.assertEqual(fetched_pred.predicted_winner.name, "Team A")
        self.assertEqual(fetched_pred.confidence, 0.9)
        # Check datetime handling - sqlite stores as string usually, ensure we get datetime back
        self.assertIsInstance(fetched_pred.created_at, datetime)

    def test_save_and_get_result(self):
        """Test saving and retrieving a result."""
        # Create a dummy prediction first to satisfy FK constraint
        c1 = Competitor(name="Team A", sport="Football")
        c2 = Competitor(name="Team B", sport="Football")
        now = datetime.now(timezone.utc)
        match = Match("Football", "Event", now, c1, c2)
        pred = Prediction(match, c1, 0.5, 0.5, 0.5, "reason", {}, now)
        pred_id = self.db.save_prediction(pred)

        result = Result(
            prediction_id=pred_id,
            actual_winner="Team A",
            score="21-17",
            fetched_from="NFL.com",
            fetched_at=now,
            is_correct=True
        )
        
        res_id = self.db.save_result(result)
        self.assertIsNotNone(res_id)
        
        fetched_res = self.db.get_result(res_id)
        self.assertEqual(fetched_res.actual_winner, "Team A")
        self.assertTrue(fetched_res.is_correct)

    def test_save_and_get_sports_data(self):
        """Test saving and retrieving sports data."""
        now = datetime.now(timezone.utc)
        data = SportsData(
            sport="Tennis",
            data_type="stats",
            entity_id="player_123",
            data={"aces": 10},
            source="Official",
            fetched_at=now
        )
        
        data_id = self.db.save_sports_data(data)
        self.assertIsNotNone(data_id)
        
        fetched_data = self.db.get_sports_data(data_id)
        self.assertEqual(fetched_data.data["aces"], 10)
        self.assertEqual(fetched_data.entity_id, "player_123")

    def test_update_and_delete_prediction(self):
        """Test updating and deleting a prediction."""
        c1 = Competitor(name="Team A", sport="Football")
        c2 = Competitor(name="Team B", sport="Football")
        now = datetime.now(timezone.utc)
        match = Match("Football", "Event", now, c1, c2)
        pred = Prediction(match, c1, 0.5, 0.5, 0.5, "reason", {}, now)
        pred_id = self.db.save_prediction(pred)
        
        # Update
        pred.id = pred_id
        pred.notes = "Updated notes"
        success = self.db.update_prediction(pred)
        self.assertTrue(success)
        
        updated_pred = self.db.get_prediction(pred_id)
        self.assertEqual(updated_pred.notes, "Updated notes")
        
        # Delete
        success = self.db.delete_prediction(pred_id)
        self.assertTrue(success)
        
        deleted_pred = self.db.get_prediction(pred_id)
        self.assertIsNone(deleted_pred)

    def test_context_manager(self):
        """Test using DatabaseManager as a context manager."""
        with DatabaseManager(":memory:") as db:
            db.initialize_schema()
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                self.assertEqual(result[0], 1)

if __name__ == '__main__':
    unittest.main()
