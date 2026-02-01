#!/usr/bin/env python3
"""
Australian Open 2026 Men's Singles Final Prediction - ML VERSION
================================================================

Uses the new ML Prediction Engine with feature extraction.

Match: Carlos Alcaraz [1] vs. Novak Djokovic [4]
Date: Sunday, February 1, 2026, 7:30 PM AEDT (3:30 AM EST)
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
from sports_prediction.sports.tennis.ml_predictor import TennisMLPredictor


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


def main():
    """Main execution function."""
    print("\n" + "="*70)
    print("AUSTRALIAN OPEN 2026 MEN'S SINGLES FINAL")
    print("ML Prediction Engine - Version 2.0")
    print("="*70)
    
    # Load environment
    load_env()
    
    api_key = os.getenv('RAPIDAPI_KEY')
    api_host = os.getenv('RAPIDAPI_HOST')
    
    if not api_key or api_key == 'your_rapidapi_key_here':
        print("\n✗ ERROR: RAPIDAPI_KEY not configured in .env file")
        return 1
    
    print(f"\n✓ API configured")
    
    # Initialize components
    db_path = Path(__file__).parent.parent / "data" / "predictions.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    db = DatabaseManager(str(db_path))
    db.initialize_schema()
    
    api_client = APIClient(
        base_url=f"https://{api_host}",
        api_key=api_key,
        host=api_host
    )
    
    fetcher = TennisAPIFetcher(api_client, db)
    ml_predictor = TennisMLPredictor()
    
    print(f"✓ Database: {db_path}")
    print(f"✓ ML Predictor initialized")
    
    # Fetch player stats
    print(f"\n{'='*70}")
    print("FETCHING PLAYER DATA")
    print(f"{'='*70}")
    
    print("\nFetching Carlos Alcaraz (ID: 275923)...")
    alcaraz_stats = fetcher.api_client.get("/api/tennis/player/275923")
    alcaraz_info = alcaraz_stats['team']['playerTeamInfo']
    print(f"✓ Alcaraz: Rank #{alcaraz_info['currentRanking']}, Age {calculate_age(alcaraz_info['birthDateTimestamp'])}")
    
    print("\nFetching Novak Djokovic (ID: 14882)...")
    djokovic_stats = fetcher.api_client.get("/api/tennis/player/14882")
    djokovic_info = djokovic_stats['team']['playerTeamInfo']
    print(f"✓ Djokovic: Rank #{djokovic_info['currentRanking']}, Age {calculate_age(djokovic_info['birthDateTimestamp'])}")
    
    # Run ML prediction
    print(f"\n{'='*70}")
    print("RUNNING ML PREDICTION")
    print(f"{'='*70}")
    
    prob_alcaraz, prob_djokovic, metadata = ml_predictor.predict(
        player1_stats=alcaraz_stats,
        player2_stats=djokovic_stats,
        h2h_data=None,  # TODO: Fetch real H2H data
        surface="hard",
        tournament_name="Australian Open 2026 Men's Singles Final"
    )
    
    print(f"\n✓ Prediction Method: {metadata['method'].upper()}")
    print(f"✓ Features Used: {metadata['features_used']}")
    
    if metadata['method'] == 'heuristic':
        print("\n⚠️  NOTE: No trained ML models found.")
        print("   Using intelligent heuristic based on multiple factors.")
        print("   For better predictions, train models with historical data.")
    
    # Determine winner
    if prob_alcaraz > prob_djokovic:
        predicted_winner_name = "Carlos Alcaraz"
        confidence = prob_alcaraz
    else:
        predicted_winner_name = "Novak Djokovic"
        confidence = prob_djokovic
    
    # Create prediction entities
    alcaraz = Competitor(
        name="Carlos Alcaraz",
        sport="Tennis",
        metadata={
            "ranking": alcaraz_info['currentRanking'],
            "age": calculate_age(alcaraz_info['birthDateTimestamp']),
            "seed": 1,
            "country": "Spain"
        }
    )
    
    djokovic = Competitor(
        name="Novak Djokovic",
        sport="Tennis",
        metadata={
            "ranking": djokovic_info['currentRanking'],
            "age": calculate_age(djokovic_info['birthDateTimestamp']),
            "seed": 4,
            "country": "Serbia"
        }
    )
    
    match = Match(
        sport="Tennis",
        event_name="Australian Open 2026 Men's Singles Final",
        event_date=datetime(2026, 2, 1, 19, 30, tzinfo=timezone.utc),
        competitor1=alcaraz,
        competitor2=djokovic
    )
    
    predicted_winner = alcaraz if predicted_winner_name == "Carlos Alcaraz" else djokovic
    
    # Generate reasoning
    reasoning = f"""
PREDICTION: {predicted_winner_name} to win
CONFIDENCE: {confidence:.1%}

METHOD: {metadata['method'].upper()}
{'(Heuristic-based until ML models are trained)' if metadata['method'] == 'heuristic' else '(ML Model Ensemble)'}

PROBABILITIES:
- Carlos Alcaraz: {prob_alcaraz:.1%}
- Novak Djokovic: {prob_djokovic:.1%}

FEATURE ANALYSIS:
{format_feature_analysis(metadata.get('feature_values', {}))}

KEY INSIGHTS:
- Alcaraz is world #1 with peak current form
- Djokovic has unmatched Grand Slam experience (24 titles)
- Both players are performing exceptionally well
- Match is expected to be highly competitive
- Confidence score reflects the uncertainty in this elite matchup

NEXT STEPS:
1. Match will be played at 7:30 PM AEDT (Feb 1, 2026)
2. After match, fetch actual result from API
3. Validate prediction accuracy
4. Use result to improve ML models

ML TRAINING STATUS:
- ⏳ Historical data collection needed
- ⏳ Model training pipeline ready
- ⏳ Awaiting training data to activate full ML predictions

DISCLAIMER: For entertainment purposes only. Sports outcomes are unpredictable.
"""
    
    # Create and save prediction
    prediction = Prediction(
        match=match,
        predicted_winner=predicted_winner,
        confidence=confidence,
        probability_c1=prob_alcaraz,
        probability_c2=prob_djokovic,
        reasoning=reasoning.strip(),
        factor_scores=metadata.get('feature_values', {}),
        created_at=datetime.now(timezone.utc),
        notes=f"ML Prediction v2.0 - Method: {metadata['method']}"
    )
    
    prediction_id = db.save_prediction(prediction)
    
    # Display results
    print(f"\n{'='*70}")
    print("PREDICTION RESULTS")
    print(f"{'='*70}")
    print(f"\n🏆 PREDICTED WINNER: {predicted_winner_name}")
    print(f"📊 CONFIDENCE: {confidence:.1%}")
    print(f"\n📈 PROBABILITIES:")
    print(f"   Alcaraz: {prob_alcaraz:.1%}")
    print(f"   Djokovic: {prob_djokovic:.1%}")
    
    print(f"\n💾 SAVED TO DATABASE:")
    print(f"   Prediction ID: {prediction_id}")
    print(f"   Database: {db_path}")
    
    print(f"\n{'='*70}")
    print("SUCCESS! Prediction complete.")
    print(f"{'='*70}")
    
    return 0


def calculate_age(birth_timestamp: int) -> int:
    """Calculate age from birth timestamp."""
    if not birth_timestamp:
        return 0
    birth_date = datetime.fromtimestamp(birth_timestamp, tz=timezone.utc)
    today = datetime.now(timezone.utc)
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age


def format_feature_analysis(features: dict) -> str:
    """Format feature values for display."""
    if not features:
        return "  (Feature details not available)"
    
    lines = []
    lines.append(f"  • Ranking: Alcaraz #{features.get('p1_ranking', 'N/A')} vs Djokovic #{features.get('p2_ranking', 'N/A')}")
    lines.append(f"  • Age: Alcaraz {features.get('p1_age', 'N/A')} vs Djokovic {features.get('p2_age', 'N/A')} years")
    lines.append(f"  • Experience: {features.get('experience_diff', 0):.0f} years difference")
    lines.append(f"  • Surface: {'Hard Court' if features.get('surface_hard') else 'Other'}")
    lines.append(f"  • Tournament: {'Grand Slam' if features.get('is_grand_slam') else 'Regular'}")
    lines.append(f"  • Total Features: {len(features)}")
    
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
