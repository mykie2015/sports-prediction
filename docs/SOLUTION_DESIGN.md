# Sports Prediction Framework - Solution Design

## Vision

A **general-purpose sports prediction framework** that can predict outcomes for any sport using:
- Sport-specific factor analysis
- Confidence scoring (0-100%)
- Transparent reasoning
- Extensible architecture for adding new sports

**Phase 1**: Tennis (Australian Open 2026 as example)  
**Future**: Basketball, Football, Baseball, Soccer, etc.

## Architecture Overview

```
sports-prediction/
├── pyproject.toml          # uv project config
├── README.md               # General framework documentation
├── .gitignore
├── .python-version
├── src/
│   └── sports_prediction/
│       ├── __init__.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── models.py       # Base classes (Competitor, Match, Prediction)
│       │   ├── predictor.py    # Abstract prediction engine
│       │   └── analyzer.py     # Base reasoning generator
│       ├── sports/
│       │   ├── __init__.py
│       │   ├── tennis/
│       │   │   ├── __init__.py
│       │   │   ├── models.py       # TennisPlayer, TennisMatch
│       │   │   ├── predictor.py    # Tennis-specific prediction
│       │   │   ├── analyzer.py     # Tennis reasoning
│       │   │   └── factors.py      # H2H, surface, form, etc.
│       │   └── [future: basketball/, football/, etc.]
│       └── cli.py              # Universal CLI for all sports
├── data/
│   └── tennis/
│       └── ao2026_final.json   # Example: AO 2026 data
├── tests/
│   ├── core/
│   │   ├── test_models.py
│   │   └── test_predictor.py
│   └── sports/
│       └── tennis/
│           ├── test_models.py
│           ├── test_predictor.py
│           └── test_analyzer.py
└── examples/
    └── tennis_ao2026.py        # Example: Predict AO 2026
```

## MVP Architecture (Phase 1)

### Core Components

1. **Data Layer** - SQLite database for persistence
2. **Data Fetcher** - Web scraping/APIs for live sports data
3. **Prediction Engine** - Simple statistical model (weighted factors)
4. **Result Tracker** - Store predictions, fetch results, calculate accuracy
5. **CLI** - User interface

### Database Schema (SQLite)

```sql
-- Predictions table
CREATE TABLE predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sport TEXT NOT NULL,
    event_name TEXT NOT NULL,
    event_date DATETIME NOT NULL,
    competitor1 TEXT NOT NULL,
    competitor2 TEXT NOT NULL,
    predicted_winner TEXT NOT NULL,
    confidence REAL NOT NULL,  -- 0-100
    probability_c1 REAL NOT NULL,  -- 0-1
    probability_c2 REAL NOT NULL,  -- 0-1
    reasoning TEXT,
    factor_scores TEXT,  -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- Results table
CREATE TABLE results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_id INTEGER NOT NULL,
    actual_winner TEXT NOT NULL,
    score TEXT,
    fetched_from TEXT,  -- Source URL
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_correct BOOLEAN,
    notes TEXT,
    FOREIGN KEY (prediction_id) REFERENCES predictions(id)
);

-- Data sources table (cache fetched data)
CREATE TABLE sports_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sport TEXT NOT NULL,
    data_type TEXT NOT NULL,  -- 'player_stats', 'match_info', 'h2h'
    entity_id TEXT NOT NULL,  -- player name, match id, etc.
    data TEXT NOT NULL,  -- JSON
    source TEXT,  -- API/website source
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME
);
```

### Data Fetching Strategy

**Recommended APIs (Free Tiers Available):**

1. **API-SPORTS (api-sports.io)** - Primary choice
   - 100 requests/day free tier
   - Tennis, Football, Basketball coverage
   - Real-time scores, statistics, predictions
   - H2H records, player stats, rankings

2. **RapidAPI - Tennis API (Matchstat.com)**
   - Free plan available
   - ATP, WTA, ITF matches
   - Historical stats datasets
   - Player profiles with career statistics

3. **Stevegtennis.com API** - Backup
   - Free plan for testing
   - 60+ years of match data
   - Comprehensive player profiles
   - Weekly rankings, H2H stats

**Data to fetch:**
- Player rankings (ATP/WTA)
- Head-to-head records
- Recent match results (last 10-20 matches)
- Surface-specific stats (hard, clay, grass)
- Tournament history
- Real-time match results

**Example API Integration:**
```python
# src/sports_prediction/data/fetchers/tennis.py
import requests

class TennisAPIFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api-tennis.com/v1"  # or API-SPORTS
        
    def fetch_player_stats(self, player_name: str) -> dict:
        """Fetch player stats from API"""
        response = requests.get(
            f"{self.base_url}/players/search",
            headers={"X-API-Key": self.api_key},
            params={"name": player_name}
        )
        # Cache in sports_data table
        return response.json()
        
    def fetch_head_to_head(self, player1_id: int, player2_id: int) -> dict:
        """Fetch H2H record from API"""
        response = requests.get(
            f"{self.base_url}/h2h/{player1_id}/{player2_id}",
            headers={"X-API-Key": self.api_key}
        )
        return response.json()
        
    def fetch_match_result(self, match_id: str) -> dict:
        """Fetch actual match result after completion"""
        response = requests.get(
            f"{self.base_url}/matches/{match_id}",
            headers={"X-API-Key": self.api_key}
        )
        return response.json()
```

### Prediction Model (ML from Day 1!)

**Approach**: Hybrid - Statistical + Machine Learning

With OpenCode's help, we can implement ML from the start!

**Models to implement:**

1. **Logistic Regression** (Baseline)
   - Simple, interpretable
   - ~71% accuracy reported
   - Fast training

2. **Random Forest** (Primary)
   - Best performance: ~83% accuracy
   - Handles non-linear relationships
   - Feature importance analysis

3. **XGBoost** (Advanced)
   - State-of-the-art for sports prediction
   - Gradient boosting
   - Can beat betting markets

**Features for ML Model:**
```python
# Feature engineering
features = [
    # Player stats
    'player1_ranking',
    'player2_ranking',
    'player1_elo_rating',
    'player2_elo_rating',
    'player1_win_rate_last_10',
    'player2_win_rate_last_10',
    
    # H2H
    'h2h_wins_p1',
    'h2h_wins_p2',
    'h2h_wins_on_surface_p1',
    'h2h_wins_on_surface_p2',
    
    # Surface-specific
    'player1_surface_win_rate',
    'player2_surface_win_rate',
    
    # Experience
    'player1_gs_titles',
    'player2_gs_titles',
    'player1_gs_finals',
    'player2_gs_finals',
    
    # Form
    'player1_recent_form_score',
    'player2_recent_form_score',
    
    # Match context
    'tournament_level',  # GS, Masters, ATP 250, etc.
    'surface_type',  # hard, clay, grass
    'best_of_sets'  # 3 or 5
]
```

**Implementation:**
```python
# src/sports_prediction/sports/tennis/ml_predictor.py
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
import xgboost as xgb
import joblib

class TennisMLPredictor:
    def __init__(self):
        self.models = {
            'logistic': LogisticRegression(),
            'random_forest': RandomForestClassifier(n_estimators=100),
            'xgboost': xgb.XGBClassifier()
        }
        self.trained_model = None
        
    def train(self, X_train, y_train, model_type='random_forest'):
        """Train the model on historical data"""
        self.trained_model = self.models[model_type]
        self.trained_model.fit(X_train, y_train)
        
    def predict(self, features: dict) -> tuple:
        """Predict match outcome with confidence"""
        X = self._prepare_features(features)
        
        # Get probability estimates
        proba = self.trained_model.predict_proba(X)[0]
        
        winner_idx = proba.argmax()
        confidence = proba[winner_idx] * 100
        
        return winner_idx, confidence, proba
        
    def get_feature_importance(self):
        """Get which features matter most"""
        if hasattr(self.trained_model, 'feature_importances_'):
            return self.trained_model.feature_importances_
        return None
        
    def save_model(self, path: str):
        """Save trained model"""
        joblib.dump(self.trained_model, path)
        
    def load_model(self, path: str):
        """Load pre-trained model"""
        self.trained_model = joblib.load(path)
```

**Training Data:**
- Use historical tennis match data (can fetch from APIs)
- Or use public datasets from Kaggle/GitHub
- Train on 5-10 years of data
- Validate on recent season

**Hybrid Approach:**
```python
def hybrid_predict(statistical_score, ml_probability):
    """Combine statistical and ML predictions"""
    # Weight: 40% statistical, 60% ML
    final_score = 0.4 * statistical_score + 0.6 * ml_probability
    return final_score
```

### Prediction Tracking Workflow

```bash
# 1. Make prediction BEFORE match
uv run sports-prediction predict \
  --sport tennis \
  --event "2026 Australian Open Final" \
  --player1 "Carlos Alcaraz" \
  --player2 "Novak Djokovic" \
  --notes "First prediction using MVP model"

# Output: Prediction saved to DB with ID #1

# 2. After match, fetch result
uv run sports-prediction fetch-result --prediction-id 1

# 3. View accuracy
uv run sports-prediction stats --sport tennis

# 4. Add notes/learnings
uv run sports-prediction comment --prediction-id 1 \
  --note "Model underestimated Djokovic's experience factor"
```

## Prediction Algorithm

### Multi-Factor Weighted Scoring

**Factors:**
1. Head-to-Head Record (20%)
2. Grand Slam H2H (25%)
3. Recent Form (25%)
4. Surface Performance (15%)
5. Experience (15%)

### Expected Output
```
PREDICTION: Novak Djokovic to win
CONFIDENCE: 58%

Factor Breakdown:
• Head-to-Head: Djokovic 56% (5-4)
• Grand Slam H2H: Alcaraz 60% (3-2)
• Recent Form: Djokovic 100% (5/5 wins)
• Hard Court: Djokovic 85% vs Alcaraz 82%
• Experience: Djokovic 90% (24 GS titles)

Actual Result: Djokovic won 7-6, 7-6 ✓
```

## Development Workflow (Updated for MVP)

### PR #1: Database & Core Models
- SQLite database setup
- Base models (Competitor, Match, Prediction)
- Database operations (CRUD)
- Tests

### PR #2: Data Fetchers
- Tennis data fetcher (web scraping/API)
- Data caching in database
- Tests with mock data

### PR #3: Prediction Engine
- Simple statistical model
- Factor calculations
- Confidence scoring
- Tests

### PR #4: Result Tracker
- Fetch match results from web
- Compare with predictions
- Calculate accuracy
- Tests

### PR #5: CLI Interface
- Predict command
- Fetch-result command
- Stats command
- Comment command
- Tests

### PR #6: Documentation
- README with examples
- API documentation
- Disclaimers

## Technology Stack

**Core:**
- Python 3.11+
- SQLite (local database)
- `uv` for dependency management

**Data Fetching:**
- `requests` - HTTP API calls
- `python-dotenv` - API key management

**Machine Learning:**
- `scikit-learn` - ML models (Logistic Regression, Random Forest)
- `xgboost` - Gradient boosting
- `pandas` - Data manipulation
- `numpy` - Numerical computations
- `joblib` - Model persistence

**CLI:**
- `typer` - Modern CLI framework
- `rich` - Beautiful terminal output with tables

**Testing:**
- `pytest` - Testing framework
- `pytest-mock` - Mocking
- `responses` - Mock HTTP requests
- `pytest-cov` - Code coverage

**Optional (Future):**
- `matplotlib` / `seaborn` - Visualizations
- `streamlit` - Web dashboard
- `fastapi` - REST API server

## Safety & Ethics

⚠️ **DISCLAIMER**: For entertainment and educational purposes only. Not for betting.
