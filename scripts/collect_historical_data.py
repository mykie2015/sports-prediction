#!/usr/bin/env python3
"""
Historical Data Collection Script
=================================

Collects past tennis matches from TennisAPI to train ML models.

Strategy:
1. Find recent completed ATP tournaments
2. Fetch match results from those tournaments
3. For each match, fetch player stats at that time
4. Extract features and outcomes
5. Save to training dataset
"""

import os
import sys
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sports_prediction.data.api_client import APIClient
from sports_prediction.sports.tennis.fetcher import TennisAPIFetcher
from sports_prediction.core.database import DatabaseManager
from sports_prediction.sports.tennis.features import TennisFeatureExtractor


def load_env():
    """Load environment variables."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


def collect_live_matches(api_client: APIClient) -> List[Dict[str, Any]]:
    """
    Collect recent/completed matches from live events API.
    
    The /api/tennis/events/live endpoint gives us current matches.
    We'll look for recently completed ones.
    """
    print("\n🔍 Searching for recent matches...")
    
    try:
        # Get live events (includes recently finished)
        response = api_client.get("/api/tennis/events/live")
        events = response.get('events', [])
        
        print(f"   Found {len(events)} events")
        
        # Filter for ATP matches that are finished
        completed_matches = []
        for event in events:
            status = event.get('status', {})
            tournament = event.get('tournament', {})
            category = tournament.get('category', {}).get('name', '')
            
            # Check if ATP and finished
            if 'atp' in category.lower() and status.get('type') == 'finished':
                completed_matches.append(event)
        
        print(f"   ✓ Found {len(completed_matches)} completed ATP matches")
        return completed_matches[:50]  # Limit to 50 for now
        
    except Exception as e:
        print(f"   ✗ Error fetching matches: {e}")
        return []


def extract_match_data(match_event: Dict[str, Any]) -> Dict[str, Any]:
    """Extract relevant data from a match event."""
    home_team = match_event.get('homeTeam', {})
    away_team = match_event.get('awayTeam', {})
    home_score = match_event.get('homeScore', {})
    away_score = match_event.get('awayScore', {})
    tournament = match_event.get('tournament', {})
    
    # Determine winner (higher 'current' score wins)
    home_won = home_score.get('current', 0) > away_score.get('current', 0)
    
    return {
        'match_id': match_event.get('id'),
        'player1_id': home_team.get('id'),
        'player1_name': home_team.get('name'),
        'player2_id': away_team.get('id'),
        'player2_name': away_team.get('name'),
        'winner': 1 if home_won else 0,  # 1=player1, 0=player2
        'score': f"{home_score.get('display', 0)}-{away_score.get('display', 0)}",
        'tournament': tournament.get('name', ''),
        'surface': tournament.get('uniqueTournament', {}).get('groundType', 'hard'),
        'date': match_event.get('startTimestamp'),
    }


def collect_historical_dataset(
    api_client: APIClient,
    fetcher: TennisAPIFetcher,
    feature_extractor: TennisFeatureExtractor,
    target_matches: int = 100
) -> tuple:
    """
    Collect historical matches and extract features.
    
    Returns:
        (X, y, metadata) where:
        - X: list of feature vectors
        - y: list of outcomes (1=player1 won, 0=player2 won)
        - metadata: list of match info dicts
    """
    print(f"\n{'='*70}")
    print(f"COLLECTING HISTORICAL DATA (Target: {target_matches} matches)")
    print(f"{'='*70}")
    
    # Get completed matches
    matches = collect_live_matches(api_client)
    
    if not matches:
        print("\n⚠️  No historical matches found from API.")
        print("   Using synthetic data for demonstration...")
        return generate_synthetic_data(feature_extractor, target_matches)
    
    X = []  # Features
    y = []  # Outcomes
    metadata = []  # Match info
    
    print(f"\n📊 Processing {len(matches)} matches...")
    
    for i, match_event in enumerate(matches[:target_matches], 1):
        try:
            # Extract match data
            match_data = extract_match_data(match_event)
            
            print(f"\n[{i}/{len(matches)}] {match_data['player1_name']} vs {match_data['player2_name']}")
            
            # Fetch player stats
            try:
                p1_stats = fetcher.api_client.get(f"/api/tennis/player/{match_data['player1_id']}")
                p2_stats = fetcher.api_client.get(f"/api/tennis/player/{match_data['player2_id']}")
            except Exception as e:
                print(f"   ✗ Error fetching player stats: {e}")
                continue
            
            # Extract features
            features = feature_extractor.extract_match_features(
                player1_stats=p1_stats,
                player2_stats=p2_stats,
                h2h_data=None,
                surface=match_data['surface'],
                tournament_name=match_data['tournament']
            )
            
            # Convert to feature vector
            feature_names = feature_extractor.get_feature_names()
            feature_vector = [features[name] for name in feature_names]
            
            X.append(feature_vector)
            y.append(match_data['winner'])
            metadata.append(match_data)
            
            print(f"   ✓ Features extracted ({len(feature_vector)} features)")
            print(f"   Winner: {match_data['player1_name'] if match_data['winner'] == 1 else match_data['player2_name']}")
            
            # Rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            print(f"   ✗ Error processing match: {e}")
            continue
    
    print(f"\n{'='*70}")
    print(f"✓ Collected {len(X)} matches for training")
    print(f"{'='*70}")
    
    return X, y, metadata


def generate_synthetic_data(
    feature_extractor: TennisFeatureExtractor,
    n_samples: int = 100
) -> tuple:
    """
    Generate synthetic training data for demonstration.
    
    Creates realistic feature distributions based on tennis statistics.
    """
    import numpy as np
    
    print(f"\n📊 Generating {n_samples} synthetic training samples...")
    
    X = []
    y = []
    metadata = []
    
    np.random.seed(42)
    
    for i in range(n_samples):
        # Generate realistic features
        p1_rank = np.random.randint(1, 200)
        p2_rank = np.random.randint(1, 200)
        
        # Higher ranked player (lower number) is more likely to win
        prob_p1_wins = 1 / (1 + np.exp((p1_rank - p2_rank) / 50))
        winner = 1 if np.random.random() < prob_p1_wins else 0
        
        # Generate feature vector
        features = {
            'p1_ranking': float(p1_rank),
            'p2_ranking': float(p2_rank),
            'ranking_diff': float(p1_rank - p2_rank),
            'ranking_ratio': float(p1_rank) / float(p2_rank) if p2_rank > 0 else 1.0,
            'p1_is_higher_ranked': 1.0 if p1_rank < p2_rank else 0.0,
            
            'p1_age': float(np.random.randint(20, 38)),
            'p2_age': float(np.random.randint(20, 38)),
            'age_diff': float(np.random.randint(-15, 15)),
            'p1_experience_years': float(np.random.randint(1, 20)),
            'p2_experience_years': float(np.random.randint(1, 20)),
            'experience_diff': float(np.random.randint(-15, 15)),
            
            'p1_prize_log': float(np.random.uniform(15, 19)),
            'p2_prize_log': float(np.random.uniform(15, 19)),
            'prize_diff_log': float(np.random.uniform(-3, 3)),
            
            'p1_height': float(np.random.uniform(1.75, 2.0)),
            'p2_height': float(np.random.uniform(1.75, 2.0)),
            'height_diff': float(np.random.uniform(-0.15, 0.15)),
            'p1_weight': float(np.random.uniform(70, 90)),
            'p2_weight': float(np.random.uniform(70, 90)),
            
            'h2h_total_matches': float(np.random.randint(0, 20)),
            'h2h_p1_wins': float(np.random.randint(0, 15)),
            'h2h_p2_wins': float(np.random.randint(0, 15)),
            'h2h_p1_win_rate': float(np.random.uniform(0.2, 0.8)),
            
            'surface_hard': 1.0 if np.random.random() < 0.5 else 0.0,
            'surface_clay': 1.0 if np.random.random() < 0.3 else 0.0,
            'surface_grass': 1.0 if np.random.random() < 0.2 else 0.0,
            
            'is_grand_slam': 1.0 if np.random.random() < 0.15 else 0.0,
        }
        
        feature_names = feature_extractor.get_feature_names()
        feature_vector = [features[name] for name in feature_names]
        
        X.append(feature_vector)
        y.append(winner)
        metadata.append({
            'match_id': f'synthetic_{i}',
            'player1_name': f'Player {i}A',
            'player2_name': f'Player {i}B',
            'winner': winner,
        })
    
    print(f"✓ Generated {len(X)} synthetic samples")
    print(f"  Class distribution: {sum(y)} Player1 wins, {len(y) - sum(y)} Player2 wins")
    
    return X, y, metadata


def main():
    """Main execution."""
    load_env()
    
    api_key = os.getenv('RAPIDAPI_KEY')
    api_host = os.getenv('RAPIDAPI_HOST')
    
    if not api_key or api_key == 'your_rapidapi_key_here':
        print("\n✗ ERROR: RAPIDAPI_KEY not configured")
        return 1
    
    # Initialize components
    db_path = Path(__file__).parent.parent / "data" / "predictions.db"
    db = DatabaseManager(str(db_path))
    db.initialize_schema()
    
    api_client = APIClient(
        base_url=f"https://{api_host}",
        api_key=api_key,
        host=api_host
    )
    
    fetcher = TennisAPIFetcher(api_client, db)
    feature_extractor = TennisFeatureExtractor()
    
    # Collect historical data
    X, y, metadata = collect_historical_dataset(
        api_client=api_client,
        fetcher=fetcher,
        feature_extractor=feature_extractor,
        target_matches=100
    )
    
    if len(X) < 20:
        print("\n⚠️  Not enough historical data collected.")
        print("   Need at least 20 matches for training.")
        return 1
    
    # Save dataset
    dataset_path = Path(__file__).parent.parent / "data" / "training_dataset.json"
    dataset = {
        'X': X,
        'y': y,
        'metadata': metadata,
        'feature_names': feature_extractor.get_feature_names(),
        'collected_at': datetime.now(timezone.utc).isoformat(),
        'n_samples': len(X)
    }
    
    with open(dataset_path, 'w') as f:
        json.dump(dataset, f, indent=2)
    
    print(f"\n💾 Training dataset saved to: {dataset_path}")
    print(f"   Samples: {len(X)}")
    print(f"   Features: {len(X[0])}")
    print(f"   Class distribution: {sum(y)} P1 wins, {len(y) - sum(y)} P2 wins")
    
    print(f"\n{'='*70}")
    print("✓ Historical data collection complete!")
    print(f"{'='*70}")
    print("\nNext step: Run train_models.py to train ML models")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
