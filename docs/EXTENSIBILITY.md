# Sports Prediction Framework - Extensibility Guide

## Adding New Sports

The framework is designed to easily add new sports. Here's how:

### 1. Create Sport Module

```
src/sports_prediction/sports/[sport_name]/
├── __init__.py
├── models.py       # Sport-specific data models
├── predictor.py    # Prediction logic
├── analyzer.py     # Reasoning generator
└── factors.py      # Sport-specific factors
```

### 2. Define Sport-Specific Models

```python
# src/sports_prediction/sports/basketball/models.py
from sports_prediction.core.models import Competitor, Match

@dataclass
class BasketballTeam(Competitor):
    """Basketball-specific team data"""
    points_per_game: float
    rebounds_per_game: float
    assists_per_game: float
    three_point_percentage: float
    # ... other stats

@dataclass
class BasketballMatch(Match):
    """Basketball-specific match"""
    home_team: BasketballTeam
    away_team: BasketballTeam
    venue: str
    # ... other details
```

### 3. Implement Prediction Logic

```python
# src/sports_prediction/sports/basketball/ml_predictor.py
from sklearn.ensemble import RandomForestClassifier
from sports_prediction.core.predictor import BaseMLPredictor

class BasketballMLPredictor(BaseMLPredictor):
    def get_features(self, match: BasketballMatch) -> list:
        """Extract features for ML model"""
        return [
            match.home_team.points_per_game,
            match.away_team.points_per_game,
            match.home_team.rebounds_per_game,
            match.away_team.rebounds_per_game,
            match.home_team.three_point_percentage,
            match.away_team.three_point_percentage,
            # ... more features
        ]
    
    def get_feature_names(self) -> list:
        return [
            'home_ppg', 'away_ppg',
            'home_rpg', 'away_rpg',
            'home_3pt_pct', 'away_3pt_pct',
            # ...
        ]
    
    def get_factor_weights(self) -> dict:
        """For statistical baseline model"""
        return {
            'offensive_efficiency': 0.30,
            'defensive_rating': 0.25,
            'home_advantage': 0.20,
            'recent_form': 0.15,
            'head_to_head': 0.10
        }
```

### 4. Implement Data Fetcher

```python
# src/sports_prediction/sports/basketball/fetcher.py
import requests
from sports_prediction.data.api_client import BaseAPIClient

class BasketballAPIFetcher(BaseAPIClient):
    def __init__(self, api_key: str):
        super().__init__(api_key, sport='basketball')
        
    def fetch_team_stats(self, team_id: int) -> dict:
        """Fetch team statistics from API"""
        response = self.get(f'/teams/{team_id}/statistics')
        return response.json()
        
    def fetch_head_to_head(self, team1_id: int, team2_id: int) -> dict:
        """Fetch H2H record"""
        response = self.get(f'/h2h/{team1_id}/{team2_id}')
        return response.json()
        
    def fetch_match_result(self, match_id: str) -> dict:
        """Fetch actual match result"""
        response = self.get(f'/matches/{match_id}')
        return response.json()
```

### 5. Register Sport in CLI

```python
# src/sports_prediction/cli.py
from sports_prediction.sports.tennis.ml_predictor import TennisMLPredictor
from sports_prediction.sports.basketball.ml_predictor import BasketballMLPredictor

SPORTS = {
    'tennis': TennisMLPredictor,
    'basketball': BasketballMLPredictor,
    'football': FootballMLPredictor,
    # ... add more
}
```

### 6. Usage

```bash
# Tennis with ML
uv run sports-prediction predict \
  --sport tennis \
  --player1 "Alcaraz" \
  --player2 "Djokovic" \
  --model random_forest

# Basketball with ML
uv run sports-prediction predict \
  --sport basketball \
  --team1 "Lakers" \
  --team2 "Celtics" \
  --model xgboost

# Football with statistical model
uv run sports-prediction predict \
  --sport football \
  --team1 "Real Madrid" \
  --team2 "Barcelona" \
  --model statistical
```

## Sport-Specific Factors

### Tennis
- Head-to-Head record
- Surface performance (hard, clay, grass)
- Recent form
- Grand Slam experience
- Ranking

### Basketball
- Offensive efficiency
- Defensive rating
- Home court advantage
- Recent form
- Head-to-head

### Football (Soccer)
- Goal difference
- Home advantage
- Recent form
- Head-to-head
- League position

### American Football
- Offensive yards per game
- Defensive yards allowed
- Turnover differential
- Home advantage
- Playoff experience

## Core Abstractions

All sports share these base classes:

```python
# core/models.py
class Competitor(ABC):
    """Base class for any competitor (player, team, etc.)"""
    name: str
    ranking: Optional[int]
    
class Match(ABC):
    """Base class for any match/game"""
    competitor1: Competitor
    competitor2: Competitor
    date: datetime
    
class Prediction:
    """Universal prediction output"""
    winner: str
    confidence: float  # 0-100
    probability_c1: float  # 0-1
    probability_c2: float  # 0-1
    reasoning: str
    factor_scores: dict
```

This design allows the framework to grow while maintaining consistency across all sports!
