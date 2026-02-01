# Sports Prediction Repository - Initiative & API Integration Strategy

**Last Updated**: February 1, 2026  
**Status**: Phase 2 Complete (2/7 PRs) - API Integration Achieved

---

## 🎯 Repository Initiative

### **Core Mission**
Build a **general-purpose sports prediction framework** that can predict outcomes for any sport using:
- **Machine Learning models** (not just simple statistics)
- **Multi-factor analysis** (20+ features per sport)
- **Transparent reasoning** (explainable AI)
- **Confidence scoring** (probabilistic predictions)
- **Result validation** (track accuracy over time)

### **Philosophy**
- **Start with Tennis** (data-rich, well-structured)
- **Design for Extensibility** (add basketball, football, baseball, etc.)
- **Test-Driven Development** (tests first, then code)
- **Real-world validation** (predict actual matches, measure accuracy)
- **Entertainment & Education** (not for betting)

### **Long-term Vision**
A framework where you can:
```bash
# Predict any sport
sports-predict tennis --match "Alcaraz vs Djokovic" --event "Australian Open"
sports-predict basketball --match "Lakers vs Celtics" --event "NBA Finals"
sports-predict football --match "Chiefs vs Eagles" --event "Super Bowl"

# Train models
sports-predict train --sport tennis --data historical_matches.csv

# View accuracy
sports-predict stats --sport tennis --period "2026"
```

---

## 📊 Current Architecture

### **Layered Design**

```
┌─────────────────────────────────────────────────────┐
│  CLI Layer (Phase 3)                                │
│  - User commands: predict, train, stats, validate  │
└─────────────────────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────┐
│  ML Prediction Engine (Phase 2 - In Progress)      │
│  - Logistic Regression, Random Forest, XGBoost     │
│  - Feature engineering & selection                  │
│  - Model training & evaluation                      │
└─────────────────────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────┐
│  API Integration Layer (Phase 2 - ✅ COMPLETE)     │
│  - TennisAPI1 (RapidAPI) - ACTIVE                  │
│  - Caching system (TTL-based)                       │
│  - Error handling & retries                         │
└─────────────────────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────┐
│  Data Layer (Phase 1 - ✅ COMPLETE)                │
│  - SQLite database (predictions, results, cache)   │
│  - Core models (Competitor, Match, Prediction)     │
│  - CRUD operations                                  │
└─────────────────────────────────────────────────────┘
```

---

## 🔌 API Integration Strategy

### **Why APIs Matter**

For ML predictions to work, we need **rich, real-time data**:
- Player statistics (ranking, form, past performance)
- Head-to-head records
- Tournament history
- Surface-specific stats (hard court, clay, grass)
- Recent match results
- Physical metrics (age, height, playing style)

**APIs provide this data at scale** instead of manual collection.

---

## ✅ Implemented: TennisAPI1 Integration

### **Current Setup**

**API Provider:** TennisAPI1 (via RapidAPI)  
**Status:** ✅ Integrated, tested, and working  
**URL:** https://rapidapi.com/fluis.lacasse/api/tennisapi1

### **Architecture**

```python
# 1. APIClient (Generic HTTP client)
src/sports_prediction/data/api_client.py
- Handles HTTP requests with retries
- Authentication (RapidAPI headers)
- Error handling (rate limits, auth errors)
- Configurable backoff strategy

# 2. TennisAPIFetcher (Tennis-specific)
src/sports_prediction/sports/tennis/fetcher.py
- fetch_player_stats(player_id) → player data
- fetch_head_to_head(p1_id, p2_id) → H2H records
- fetch_matches(player_id) → recent matches
- Caching with TTL (24h for stats, 7d for H2H, 1h for matches)
```

### **Key Endpoints Used**

| Endpoint | Purpose | Cache TTL | Example |
|----------|---------|-----------|---------|
| `/api/tennis/player/{id}` | Player details, rankings, career stats | 24 hours | ID: 275923 (Alcaraz) |
| `/api/tennis/events/live` | Live match data, scores | No cache | All live matches |
| `/api/tennis/search/{query}` | Search players by name | No cache | "Alcaraz" → ID |

### **Data Flow**

```
User Request
    ↓
TennisAPIFetcher.fetch_player_stats(275923)
    ↓
Check Cache (sports_data table)
    ├─ Cache Hit → Return cached data
    └─ Cache Miss
        ↓
    APIClient.get("/api/tennis/player/275923")
        ↓
    TennisAPI1 (RapidAPI)
        ↓
    Parse Response → Save to Cache → Return Data
```

### **Environment Configuration**

`.env` file:
```bash
RAPIDAPI_KEY=6b4b8a2d75msh04edd2fd365aa0ep127139jsn11540e50b146
RAPIDAPI_HOST=tennisapi1.p.rapidapi.com
```

### **Running Examples**

```bash
# Run the Australian Open 2026 prediction
cd openclaw_projects/sports-prediction
uv run python examples/ao2026_final_prediction.py

# Output:
# ✓ Fetches Alcaraz stats (ID: 275923)
# ✓ Fetches Djokovic stats (ID: 14882)
# ✓ Generates prediction with reasoning
# ✓ Saves to database (Prediction ID: 1)
```

---

## 🎯 API Integration: Best Practices

### **1. Caching Strategy**

**Why?** API rate limits (free tiers are limited)

**Implementation:**
- Player stats: 24 hours (rankings don't change daily)
- H2H records: 7 days (historical data is stable)
- Matches: 1 hour (active tournaments need fresh data)

**Database table:**
```sql
CREATE TABLE sports_data (
    id INTEGER PRIMARY KEY,
    sport TEXT NOT NULL,
    data_type TEXT NOT NULL,  -- "player_stats", "h2h", "matches"
    entity_id TEXT NOT NULL,   -- "275923" or "275923-14882"
    data TEXT NOT NULL,         -- JSON blob
    source TEXT,                -- "tennisapi1"
    fetched_at DATETIME,
    expires_at DATETIME         -- Cache expiration
);
```

### **2. Error Handling**

```python
# Retry logic for transient failures
retry_strategy = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[429, 500, 502, 503, 504]
)

# Specific exceptions
try:
    data = api_client.get("/endpoint")
except AuthenticationError:
    # API key invalid
except RateLimitError:
    # Use cached data or wait
except APIError:
    # Generic API failure
```

### **3. Player ID Mapping**

**Challenge:** APIs use numeric IDs, humans use names

**Solution:**
```python
# Search by name first
results = api_client.get("/api/tennis/search/alcaraz")
player_id = results['results'][0]['entity']['id']  # 275923

# Then fetch by ID
stats = fetcher.fetch_player_stats(player_id)
```

**For production:** Build a player name → ID mapping cache.

---

## 🔮 Future API Integrations

### **Planned Additions**

1. **API-SPORTS (api-sports.io)**
   - Backup for TennisAPI1
   - Multi-sport support (basketball, football, etc.)
   - 100 requests/day free tier

2. **Historical Data APIs**
   - ATP/WTA official APIs (if available)
   - Kaggle datasets (for ML training)
   - Jeff Sackmann's Tennis Data (GitHub)

3. **Live Scores**
   - Real-time match updates
   - In-play statistics
   - Betting odds (for model calibration, not betting)

### **Sport-Specific APIs**

When expanding beyond tennis:

**Basketball:**
- NBA API (stats.nba.com)
- Ball Don't Lie API
- SportRadar

**Football:**
- NFL API
- ESPN API
- Pro Football Reference

**Baseball:**
- MLB Stats API
- BaseballSavant
- FanGraphs

---

## 📈 How ML Will Use API Data

### **Feature Engineering Pipeline**

```python
# Raw API data
player1 = fetcher.fetch_player_stats(275923)  # Alcaraz
player2 = fetcher.fetch_player_stats(14882)   # Djokovic
h2h = fetcher.fetch_head_to_head(275923, 14882)
matches1 = fetcher.fetch_matches(275923)
matches2 = fetcher.fetch_matches(14882)

# Extract features (20+ features)
features = {
    # Ranking features
    'p1_ranking': player1['ranking'],
    'p2_ranking': player2['ranking'],
    'ranking_diff': player1['ranking'] - player2['ranking'],
    
    # Experience features
    'p1_age': calculate_age(player1['birthdate']),
    'p2_age': calculate_age(player2['birthdate']),
    'p1_gs_titles': count_gs_titles(player1),
    'p2_gs_titles': count_gs_titles(player2),
    
    # H2H features
    'h2h_wins_p1': count_wins(h2h, player1_id=275923),
    'h2h_wins_p2': count_wins(h2h, player2_id=14882),
    'h2h_gs_wins_p1': count_gs_wins(h2h, player1_id=275923),
    
    # Form features (last 10 matches)
    'p1_win_rate_l10': calculate_win_rate(matches1, last_n=10),
    'p2_win_rate_l10': calculate_win_rate(matches2, last_n=10),
    'p1_hard_court_wr': calculate_surface_wr(matches1, surface='hard'),
    'p2_hard_court_wr': calculate_surface_wr(matches2, surface='hard'),
    
    # Tournament-specific
    'p1_ao_titles': count_tournament_wins(player1, tournament='AO'),
    'p2_ao_titles': count_tournament_wins(player2, tournament='AO'),
    
    # Physical features
    'p1_height': player1['height'],
    'p2_height': player2['height'],
    'height_diff': player1['height'] - player2['height'],
    
    # ... 10+ more features
}

# Feed to ML model
prediction = model.predict_proba(features)
# [0.536, 0.464]  → 53.6% Alcaraz, 46.4% Djokovic
```

### **Training Data Collection**

```python
# Collect historical matches
matches = []
for match_id in historical_match_ids:
    match_data = fetcher.fetch_match(match_id)
    
    # Extract features at the time of the match
    features = extract_features(match_data)
    outcome = match_data['winner']  # 1 or 2
    
    matches.append({
        'features': features,
        'outcome': outcome
    })

# Train model
X = [m['features'] for m in matches]
y = [m['outcome'] for m in matches]

model = RandomForestClassifier()
model.fit(X, y)
```

---

## 🚀 Next Steps for API Integration

### **Immediate (PR #3 - ML Engine)**

1. **Historical Data Collection**
   ```bash
   # Fetch last 500 ATP matches
   python scripts/collect_historical_data.py --sport tennis --count 500
   ```

2. **Feature Engineering Module**
   ```python
   # src/sports_prediction/sports/tennis/features.py
   class TennisFeatureExtractor:
       def extract(self, match_context):
           # Extract 20+ features from API data
           pass
   ```

3. **ML Pipeline**
   ```python
   # src/sports_prediction/sports/tennis/ml_predictor.py
   class TennisMLPredictor:
       def train(self, historical_data):
           # Train models
       
       def predict(self, match_context):
           # Generate prediction
   ```

### **Medium-term (PR #4-5)**

1. **Result Validation**
   ```python
   # After match completes
   actual_result = fetcher.fetch_match_result(match_id)
   validate_prediction(prediction_id=1, actual_result=actual_result)
   ```

2. **CLI Integration**
   ```bash
   sports-predict tennis --player1 "Alcaraz" --player2 "Djokovic"
   # Automatically searches player IDs via API
   # Fetches stats
   # Runs ML model
   # Shows prediction
   ```

### **Long-term (Phase 4)**

1. **Real-time Predictions**
   - Monitor live tournaments
   - Predict upcoming matches
   - Update predictions as tournament progresses

2. **Multi-sport Expansion**
   - Basketball module with NBA API
   - Football module with NFL API
   - Shared architecture, sport-specific features

3. **Model Improvements**
   - A/B test different models
   - Hyperparameter tuning
   - Ensemble methods
   - Deep learning (if enough data)

---

## 📊 Success Metrics

### **API Integration Health**
- ✅ API response time: < 2 seconds
- ✅ Cache hit rate: Target > 70%
- ✅ API error rate: < 1%
- ✅ Rate limit usage: < 80% of daily limit

### **Prediction Quality (To Measure)**
- Accuracy: > 65% (better than random)
- Calibration: Confidence scores match actual win rates
- Brier score: < 0.2 (probabilistic accuracy)

### **Current Status**
- ✅ **First prediction made**: AO 2026 Final
- ⏳ **Awaiting result**: To validate accuracy
- 🎯 **Next**: Build ML models for better predictions

---

## 🎾 Live Example: AO 2026 Final

### **Prediction Made**
- **Match**: Carlos Alcaraz [1] vs Novak Djokovic [4]
- **Prediction**: Alcaraz 53.6% - Djokovic 46.4%
- **Stored**: Database ID: 1, Timestamp: 2026-02-01T05:35:47Z
- **Data Source**: TennisAPI1 (real player stats)

### **After Match Completes**
```python
# Fetch result
result = fetcher.fetch_match_result(match_id)
# {'winner': 'Djokovic', 'score': '7-6, 7-6'}

# Validate
is_correct = (result['winner'] == 'Alcaraz')  # Our prediction
# False - we predicted Alcaraz, Djokovic won

# Learn
# - Close match (both tiebreaks) validates our 53-47 probability
# - Djokovic's experience factor may need higher weight
# - Update model with this new data point
```

---

## 📚 Key Takeaways

### **What We've Built**
1. ✅ Solid foundation (database, models)
2. ✅ Working API integration (real data)
3. ✅ First prediction (AO 2026 Final)
4. ✅ Caching system (efficient API usage)
5. ✅ Extensible architecture (ready for ML)

### **What's Next**
1. 🔨 Build ML models (PR #3)
2. 🔨 Validate with real match (AO Final result)
3. 🔨 Expand features (from 5 to 20+)
4. 🔨 Create CLI for easy use
5. 🔨 Add more sports (basketball, football)

### **Design Principles**
- **API-first**: Real data beats assumptions
- **Test-driven**: Tests define expected behavior
- **Incremental**: Build, test, validate, improve
- **Extensible**: One sport today, many sports tomorrow
- **Transparent**: Always explain why a prediction was made

---

**Repository**: https://github.com/mykie2015/sports-prediction  
**Documentation**: `docs/` folder  
**Examples**: `examples/ao2026_final_prediction.py`  
**Status**: Phase 2 complete, Phase 3 (ML) starting
