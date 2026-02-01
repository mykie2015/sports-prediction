import sqlite3
import json
import logging
from datetime import datetime
from dataclasses import asdict
from typing import Optional, ContextManager
from contextlib import contextmanager
from pathlib import Path

from sports_prediction.core.models import Competitor, Match, Prediction, Result, SportsData

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages SQLite database connections and operations.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def get_connection(self) -> sqlite3.Connection:
        """Returns a database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            # Enable foreign keys
            self._conn.execute("PRAGMA foreign_keys = ON;")
            # Return rows as sqlite3.Row for name access
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self):
        """Closes the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        self.get_connection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def initialize_schema(self):
        """Creates the necessary database tables."""
        schema = """
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sport TEXT NOT NULL,
            event_name TEXT NOT NULL,
            event_date TEXT NOT NULL,
            competitor1 TEXT NOT NULL,
            competitor2 TEXT NOT NULL,
            predicted_winner TEXT NOT NULL,
            confidence REAL NOT NULL,
            probability_c1 REAL,
            probability_c2 REAL,
            reasoning TEXT,
            factor_scores TEXT,
            created_at TEXT NOT NULL,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_id INTEGER NOT NULL,
            actual_winner TEXT NOT NULL,
            score TEXT,
            fetched_from TEXT,
            fetched_at TEXT NOT NULL,
            is_correct BOOLEAN,
            notes TEXT,
            FOREIGN KEY (prediction_id) REFERENCES predictions (id)
        );

        CREATE TABLE IF NOT EXISTS sports_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sport TEXT NOT NULL,
            data_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            data TEXT NOT NULL,
            source TEXT,
            fetched_at TEXT NOT NULL,
            expires_at TEXT
        );
        """
        with self.get_connection() as conn:
            conn.executescript(schema)
            conn.commit()

    def _serialize_competitor(self, competitor: Competitor) -> str:
        return json.dumps(asdict(competitor))

    def _deserialize_competitor(self, data: str) -> Competitor:
        d = json.loads(data)
        return Competitor(**d)

    def save_prediction(self, prediction: Prediction) -> int:
        """Saves a prediction to the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO predictions (
                    sport, event_name, event_date, competitor1, competitor2,
                    predicted_winner, confidence, probability_c1, probability_c2,
                    reasoning, factor_scores, created_at, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    prediction.match.sport,
                    prediction.match.event_name,
                    prediction.match.event_date.isoformat(),
                    self._serialize_competitor(prediction.match.competitor1),
                    self._serialize_competitor(prediction.match.competitor2),
                    self._serialize_competitor(prediction.predicted_winner),
                    prediction.confidence,
                    prediction.probability_c1,
                    prediction.probability_c2,
                    prediction.reasoning,
                    json.dumps(prediction.factor_scores),
                    prediction.created_at.isoformat(),
                    prediction.notes
                )
            )
            conn.commit()
            return cursor.lastrowid

    def get_prediction(self, prediction_id: int) -> Optional[Prediction]:
        """Retrieves a prediction by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM predictions WHERE id = ?", (prediction_id,))
            row = cursor.fetchone()
            if not row:
                return None

            c1 = self._deserialize_competitor(row['competitor1'])
            c2 = self._deserialize_competitor(row['competitor2'])
            match = Match(
                sport=row['sport'],
                event_name=row['event_name'],
                event_date=datetime.fromisoformat(row['event_date']),
                competitor1=c1,
                competitor2=c2
            )

            predicted_winner = self._deserialize_competitor(row['predicted_winner'])
            
            return Prediction(
                id=row['id'],
                match=match,
                predicted_winner=predicted_winner,
                confidence=row['confidence'],
                probability_c1=row['probability_c1'],
                probability_c2=row['probability_c2'],
                reasoning=row['reasoning'],
                factor_scores=json.loads(row['factor_scores']),
                created_at=datetime.fromisoformat(row['created_at']),
                notes=row['notes']
            )

    def update_prediction(self, prediction: Prediction) -> bool:
        """Updates an existing prediction."""
        if prediction.id is None:
            return False
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE predictions SET
                    sport = ?, event_name = ?, event_date = ?, competitor1 = ?, competitor2 = ?,
                    predicted_winner = ?, confidence = ?, probability_c1 = ?, probability_c2 = ?,
                    reasoning = ?, factor_scores = ?, created_at = ?, notes = ?
                WHERE id = ?
                """,
                (
                    prediction.match.sport,
                    prediction.match.event_name,
                    prediction.match.event_date.isoformat(),
                    self._serialize_competitor(prediction.match.competitor1),
                    self._serialize_competitor(prediction.match.competitor2),
                    self._serialize_competitor(prediction.predicted_winner),
                    prediction.confidence,
                    prediction.probability_c1,
                    prediction.probability_c2,
                    prediction.reasoning,
                    json.dumps(prediction.factor_scores),
                    prediction.created_at.isoformat(),
                    prediction.notes,
                    prediction.id
                )
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_prediction(self, prediction_id: int) -> bool:
        """Deletes a prediction by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM predictions WHERE id = ?", (prediction_id,))
            conn.commit()
            return cursor.rowcount > 0

    def save_result(self, result: Result) -> int:
        """Saves a result to the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO results (
                    prediction_id, actual_winner, score, fetched_from,
                    fetched_at, is_correct, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.prediction_id,
                    result.actual_winner,
                    result.score,
                    result.fetched_from,
                    result.fetched_at.isoformat(),
                    result.is_correct,
                    result.notes
                )
            )
            conn.commit()
            return cursor.lastrowid

    def get_result(self, result_id: int) -> Optional[Result]:
        """Retrieves a result by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM results WHERE id = ?", (result_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            return Result(
                id=row['id'],
                prediction_id=row['prediction_id'],
                actual_winner=row['actual_winner'],
                score=row['score'],
                fetched_from=row['fetched_from'],
                fetched_at=datetime.fromisoformat(row['fetched_at']),
                is_correct=bool(row['is_correct']),
                notes=row['notes']
            )

    def update_result(self, result: Result) -> bool:
        """Updates an existing result."""
        if result.id is None:
            return False

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE results SET
                    prediction_id = ?, actual_winner = ?, score = ?, fetched_from = ?,
                    fetched_at = ?, is_correct = ?, notes = ?
                WHERE id = ?
                """,
                (
                    result.prediction_id,
                    result.actual_winner,
                    result.score,
                    result.fetched_from,
                    result.fetched_at.isoformat(),
                    result.is_correct,
                    result.notes,
                    result.id
                )
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_result(self, result_id: int) -> bool:
        """Deletes a result by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM results WHERE id = ?", (result_id,))
            conn.commit()
            return cursor.rowcount > 0

    def save_sports_data(self, data: SportsData) -> int:
        """Saves sports data to the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            expires_at = data.expires_at.isoformat() if data.expires_at else None
            cursor.execute(
                """
                INSERT INTO sports_data (
                    sport, data_type, entity_id, data, source, fetched_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data.sport,
                    data.data_type,
                    data.entity_id,
                    json.dumps(data.data),
                    data.source,
                    data.fetched_at.isoformat(),
                    expires_at
                )
            )
            conn.commit()
            return cursor.lastrowid

    def get_sports_data(self, data_id: int) -> Optional[SportsData]:
        """Retrieves sports data by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sports_data WHERE id = ?", (data_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            expires_at = datetime.fromisoformat(row['expires_at']) if row['expires_at'] else None
            
            return SportsData(
                id=row['id'],
                sport=row['sport'],
                data_type=row['data_type'],
                entity_id=row['entity_id'],
                data=json.loads(row['data']),
                source=row['source'],
                fetched_at=datetime.fromisoformat(row['fetched_at']),
                expires_at=expires_at
            )

    def update_sports_data(self, data: SportsData) -> bool:
        """Updates existing sports data."""
        if data.id is None:
            return False

        with self.get_connection() as conn:
            cursor = conn.cursor()
            expires_at = data.expires_at.isoformat() if data.expires_at else None
            cursor.execute(
                """
                UPDATE sports_data SET
                    sport = ?, data_type = ?, entity_id = ?, data = ?, source = ?,
                    fetched_at = ?, expires_at = ?
                WHERE id = ?
                """,
                (
                    data.sport,
                    data.data_type,
                    data.entity_id,
                    json.dumps(data.data),
                    data.source,
                    data.fetched_at.isoformat(),
                    expires_at,
                    data.id
                )
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_sports_data(self, data_id: int) -> bool:
        """Deletes sports data by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sports_data WHERE id = ?", (data_id,))
            conn.commit()
            return cursor.rowcount > 0
