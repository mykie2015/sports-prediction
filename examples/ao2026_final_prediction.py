#!/usr/bin/env python3
"""
Australian Open 2026 Men's Singles Final Prediction Example
===========================================================

Match: Carlos Alcaraz [1] vs. Novak Djokovic [4]
Date: Sunday, February 1, 2026, 7:30 PM AEDT (3:30 AM EST)
Venue: Rod Laver Arena, Melbourne, Australia

This example demonstrates:
1. Fetching real player data from TennisAPI1 (RapidAPI)
2. Creating a prediction based on multiple factors
3. Storing the prediction in the database
4. Generating transparent reasoning

Player IDs (from TennisAPI1):
- Carlos Alcaraz: 275923
- Novak Djokovic: 14882
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sports_prediction.core.database import DatabaseManager
from sports_prediction.core.models import Competitor, Match, Prediction
from sports_prediction.data.api_client import APIClient
from sports_prediction.sports.tennis.fetcher import TennisAPIFetcher


def load_env():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


def fetch_player_stats(fetcher: TennisAPIFetcher, player_id: int, player_name: str):
    """Fetch and display player statistics."""
    print(f"\n{'='*60}")
    print(f"Fetching stats for {player_name} (ID: {player_id})...")
    print(f"{'='*60}")
    
    try:
        stats = fetcher.api_client.get(f"/api/tennis/player/{player_id}")
        team = stats.get('team', {})
        info = team.get('playerTeamInfo', {})
        
        print(f"✓ Player: {team.get('fullName', player_name)}")
        print(f"  Ranking: #{info.get('currentRanking', 'N/A')}")
        print(f"  Country: {team.get('country', {}).get('name', 'N/A')}")
        print(f"  Age: {calculate_age(info.get('birthDateTimestamp', 0))} years")
        print(f"  Height: {info.get('height', 'N/A')} m")
        print(f"  Plays: {info.get('plays', 'N/A')}")
        print(f"  Turned Pro: {info.get('turnedPro', 'N/A')}")
        print(f"  Prize Money: €{info.get('prizeTotal', 0):,}")
        
        return team
        
    except Exception as e:
        print(f"✗ Error fetching stats: {e}")
        return None


def calculate_age(birth_timestamp: int) -> int:
    """Calculate age from birth timestamp."""
    if not birth_timestamp:
        return 0
    birth_date = datetime.fromtimestamp(birth_timestamp, tz=timezone.utc)
    today = datetime.now(timezone.utc)
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def create_simple_prediction(alcaraz_stats: dict, djokovic_stats: dict) -> Prediction:
    """
    Create a prediction based on multiple factors.
    
    This is a simplified model. In production, we'll use ML models.
    """
    
    # Extract key stats
    alcaraz_info = alcaraz_stats.get('playerTeamInfo', {})
    djokovic_info = djokovic_stats.get('playerTeamInfo', {})
    
    alcaraz_ranking = alcaraz_info.get('currentRanking', 1)
    djokovic_ranking = djokovic_info.get('currentRanking', 7)
    
    alcaraz_age = calculate_age(alcaraz_info.get('birthDateTimestamp', 0))
    djokovic_age = calculate_age(djokovic_info.get('birthDateTimestamp', 0))
    
    # Factor scores (0-1 scale)
    factors = {}
    
    # 1. Ranking Factor (20% weight)
    # Lower ranking number is better
    if alcaraz_ranking < djokovic_ranking:
        factors['ranking'] = 0.65  # Alcaraz advantage
    else:
        factors['ranking'] = 0.35  # Djokovic advantage
    
    # 2. Age/Experience Factor (20% weight)
    # Djokovic has experience, Alcaraz has youth
    # Historical H2H: Djokovic 5-4 overall, Alcaraz 3-2 in Grand Slams
    factors['experience_h2h'] = 0.48  # Slight Alcaraz advantage in GS
    
    # 3. Surface Performance (25% weight)
    # Hard court at Australian Open - both excellent
    factors['surface'] = 0.52  # Slight Alcaraz edge
    
    # 4. Current Form (25% weight)
    # Both made it to final - excellent form
    # Alcaraz as #1 seed suggests better current form
    factors['form'] = 0.58  # Alcaraz advantage
    
    # 5. Grand Slam Experience (10% weight)
    # Djokovic: 24 GS titles, Alcaraz: 4 GS titles
    factors['gs_experience'] = 0.35  # Djokovic significant advantage
    
    # Calculate weighted probability
    weights = {
        'ranking': 0.20,
        'experience_h2h': 0.20,
        'surface': 0.25,
        'form': 0.25,
        'gs_experience': 0.10
    }
    
    alcaraz_probability = sum(factors[k] * weights[k] for k in factors)
    djokovic_probability = 1 - alcaraz_probability
    
    # Determine winner (higher probability)
    if alcaraz_probability > djokovic_probability:
        predicted_winner_name = "Carlos Alcaraz"
        confidence = alcaraz_probability
    else:
        predicted_winner_name = "Novak Djokovic"
        confidence = djokovic_probability
    
    # Create Competitor objects
    alcaraz = Competitor(
        name="Carlos Alcaraz",
        sport="Tennis",
        metadata={
            "ranking": alcaraz_ranking,
            "age": alcaraz_age,
            "seed": 1,
            "country": "Spain"
        }
    )
    
    djokovic = Competitor(
        name="Novak Djokovic",
        sport="Tennis",
        metadata={
            "ranking": djokovic_ranking,
            "age": djokovic_age,
            "seed": 4,
            "country": "Serbia"
        }
    )
    
    # Create Match
    match = Match(
        sport="Tennis",
        event_name="Australian Open 2026 Men's Singles Final",
        event_date=datetime(2026, 2, 1, 19, 30, tzinfo=timezone.utc),  # 7:30 PM AEDT
        competitor1=alcaraz,
        competitor2=djokovic
    )
    
    # Determine predicted winner object
    predicted_winner = alcaraz if predicted_winner_name == "Carlos Alcaraz" else djokovic
    
    # Generate reasoning
    reasoning = f"""
PREDICTION: {predicted_winner_name} to win

CONFIDENCE: {confidence:.1%}

FACTOR ANALYSIS:
1. Ranking ({weights['ranking']:.0%} weight): {factors['ranking']:.2f}
   - Alcaraz #1 vs Djokovic #7
   - {"Advantage: Alcaraz" if factors['ranking'] > 0.5 else "Advantage: Djokovic"}

2. Experience & H2H ({weights['experience_h2h']:.0%} weight): {factors['experience_h2h']:.2f}
   - Head-to-Head: Djokovic 5-4 overall, Alcaraz 3-2 in Grand Slams
   - Slight advantage: Alcaraz in GS finals

3. Surface Performance ({weights['surface']:.0%} weight): {factors['surface']:.2f}
   - Hard court (Rod Laver Arena)
   - Both excel on hard courts
   - Slight edge: Alcaraz

4. Current Form ({weights['form']:.0%} weight): {factors['form']:.2f}
   - Both reached the final undefeated in this tournament
   - Alcaraz as #1 seed shows dominant form
   - Advantage: Alcaraz

5. Grand Slam Experience ({weights['gs_experience']:.0%} weight): {factors['gs_experience']:.2f}
   - Djokovic: 24 Grand Slam titles (record)
   - Alcaraz: 4 Grand Slam titles
   - Clear advantage: Djokovic

FINAL PROBABILITIES:
- Carlos Alcaraz: {alcaraz_probability:.1%}
- Novak Djokovic: {djokovic_probability:.1%}

KEY INSIGHTS:
- This is the "dream final" everyone anticipated
- Alcaraz's youth, ranking, and recent GS H2H record give him a slight edge
- Djokovic's experience and championship mentality cannot be underestimated
- Expected to be a close, high-quality match
- Could easily go either way (confidence reflects this uncertainty)

DISCLAIMER: This is a statistical prediction for entertainment purposes only.
Actual match outcomes depend on many real-time factors including form, fitness, and momentum.
"""
    
    # Create Prediction
    prediction = Prediction(
        match=match,
        predicted_winner=predicted_winner,
        confidence=confidence,
        probability_c1=alcaraz_probability,
        probability_c2=djokovic_probability,
        reasoning=reasoning.strip(),
        factor_scores=factors,
        created_at=datetime.now(timezone.utc),
        notes="Simplified prediction model - ML models to be implemented in future PRs"
    )
    
    return prediction


def main():
    """Main execution function."""
    print("\n" + "="*60)
    print("AUSTRALIAN OPEN 2026 MEN'S SINGLES FINAL")
    print("Prediction System - Example Run")
    print("="*60)
    
    # Load environment variables
    load_env()
    
    # Check for API key
    api_key = os.getenv('RAPIDAPI_KEY')
    api_host = os.getenv('RAPIDAPI_HOST')
    
    if not api_key or api_key == 'your_rapidapi_key_here':
        print("\n✗ ERROR: RAPIDAPI_KEY not configured in .env file")
        print("  Please add your RapidAPI key to .env file")
        return 1
    
    print(f"\n✓ API Key loaded: {api_key[:10]}...{api_key[-4:]}")
    print(f"✓ API Host: {api_host}")
    
    # Initialize database
    db_path = Path(__file__).parent.parent / "data" / "predictions.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n✓ Database: {db_path}")
    
    db = DatabaseManager(str(db_path))
    db.initialize_schema()
    print("✓ Database schema initialized")
    
    # Initialize API client
    api_client = APIClient(
        base_url=f"https://{api_host}",
        api_key=api_key,
        host=api_host
    )
    
    fetcher = TennisAPIFetcher(api_client, db)
    
    # Fetch player stats
    alcaraz_stats = fetch_player_stats(fetcher, 275923, "Carlos Alcaraz")
    djokovic_stats = fetch_player_stats(fetcher, 14882, "Novak Djokovic")
    
    if not alcaraz_stats or not djokovic_stats:
        print("\n✗ ERROR: Could not fetch player stats")
        return 1
    
    # Create prediction
    print(f"\n{'='*60}")
    print("GENERATING PREDICTION")
    print(f"{'='*60}")
    
    prediction = create_simple_prediction(alcaraz_stats, djokovic_stats)
    
    # Save to database
    prediction_id = db.save_prediction(prediction)
    print(f"\n✓ Prediction saved with ID: {prediction_id}")
    
    # Display prediction
    print(f"\n{'='*60}")
    print("PREDICTION REPORT")
    print(f"{'='*60}")
    print(prediction.reasoning)
    
    print(f"\n{'='*60}")
    print("NEXT STEPS")
    print(f"{'='*60}")
    print("1. Wait for the match to complete")
    print("2. Fetch the actual result using the API")
    print("3. Compare prediction vs actual result")
    print("4. Calculate accuracy metrics")
    print("5. Learn from the prediction for model improvement")
    
    print(f"\n✓ Example completed successfully!")
    print(f"  Prediction ID: {prediction_id}")
    print(f"  Database: {db_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
