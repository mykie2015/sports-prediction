from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any

@dataclass
class Competitor:
    """
    Represents a competitor in a sports match.

    Attributes:
        name: The name of the competitor (e.g., team name or player name).
        sport: The sport the competitor plays.
        metadata: Additional information about the competitor (e.g., rank, stats).
    """
    name: str
    sport: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Match:
    """
    Represents a sports match between two competitors.

    Attributes:
        sport: The sport of the match.
        event_name: The name of the event/tournament.
        event_date: The date and time of the match.
        competitor1: The first competitor.
        competitor2: The second competitor.
    """
    sport: str
    event_name: str
    event_date: datetime
    competitor1: Competitor
    competitor2: Competitor


@dataclass
class Prediction:
    """
    Represents a prediction for a specific match.

    Attributes:
        match: The match being predicted.
        predicted_winner: The competitor predicted to win.
        confidence: A score between 0 and 1 indicating confidence.
        probability_c1: Probability of competitor 1 winning.
        probability_c2: Probability of competitor 2 winning.
        reasoning: Textual explanation for the prediction.
        factor_scores: Dictionary of scores contributing to the prediction.
        created_at: When the prediction was made.
        id: Unique identifier for the prediction (database ID).
        notes: Optional notes.
    """
    match: Match
    predicted_winner: Competitor
    confidence: float
    probability_c1: float
    probability_c2: float
    reasoning: str
    factor_scores: dict[str, float]
    created_at: datetime
    id: Optional[int] = None
    notes: Optional[str] = None


@dataclass
class Result:
    """
    Represents the result of a predicted match.

    Attributes:
        prediction_id: The ID of the associated prediction.
        actual_winner: The name of the actual winner.
        score: The final score.
        fetched_from: Source of the result data.
        fetched_at: When the result was fetched.
        is_correct: Whether the prediction was correct.
        id: Unique identifier for the result.
        notes: Optional notes.
    """
    prediction_id: int
    actual_winner: str
    score: str
    fetched_from: str
    fetched_at: datetime
    is_correct: bool
    id: Optional[int] = None
    notes: Optional[str] = None


@dataclass
class SportsData:
    """
    Represents generic sports data fetched from an external source.

    Attributes:
        sport: The sport the data belongs to.
        data_type: The type of data (e.g., "rankings", "stats").
        entity_id: Identifier for the entity the data pertains to.
        data: The actual data payload.
        source: Source of the data.
        fetched_at: When the data was fetched.
        expires_at: When the data is considered expired.
        id: Unique identifier.
    """
    sport: str
    data_type: str
    entity_id: str
    data: dict[str, Any]
    source: str
    fetched_at: datetime
    expires_at: Optional[datetime] = None
    id: Optional[int] = None
