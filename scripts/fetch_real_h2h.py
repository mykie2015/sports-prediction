#!/usr/bin/env python3
"""
Fetch Real Historical Matches Between Alcaraz and Djokovic
==========================================================

Uses TennisAPI to get their actual head-to-head history.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sports_prediction.data.api_client import APIClient
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


def main():
    """Fetch Alcaraz vs Djokovic historical matches."""
    load_env()
    
    api_key = os.getenv('RAPIDAPI_KEY')
    api_host = os.getenv('RAPIDAPI_HOST')
    
    if not api_key:
        print("ERROR: No API key")
        return 1
    
    print("\n" + "="*70)
    print("FETCHING ALCARAZ vs DJOKOVIC HEAD-TO-HEAD")
    print("="*70)
    
    api_client = APIClient(
        base_url=f"https://{api_host}",
        api_key=api_key,
        host=api_host
    )
    
    # Player IDs
    alcaraz_id = 275923
    djokovic_id = 14882
    
    print(f"\nPlayer IDs:")
    print(f"  Carlos Alcaraz: {alcaraz_id}")
    print(f"  Novak Djokovic: {djokovic_id}")
    
    # Get player stats (current)
    print(f"\n📊 Fetching current player stats...")
    try:
        alcaraz_stats = api_client.get(f"/api/tennis/player/{alcaraz_id}")
        djokovic_stats = api_client.get(f"/api/tennis/player/{djokovic_id}")
        print(f"✓ Player stats fetched")
    except Exception as e:
        print(f"✗ Error: {e}")
        return 1
    
    # Search for their matches
    print(f"\n🔍 Searching for Alcaraz matches...")
    try:
        # Search for matches involving Alcaraz
        search_result = api_client.get(f"/api/tennis/search/alcaraz djokovic")
        print(f"✓ Search completed")
        print(json.dumps(search_result, indent=2)[:500])
    except Exception as e:
        print(f"✗ Search failed: {e}")
    
    # Try to get H2H data directly
    print(f"\n🔍 Attempting H2H endpoint...")
    h2h_attempts = [
        f"/api/tennis/h2h/{alcaraz_id}/{djokovic_id}",
        f"/api/tennis/headtohead?player1={alcaraz_id}&player2={djokovic_id}",
        f"/api/tennis/matches?player1={alcaraz_id}&player2={djokovic_id}",
    ]
    
    for endpoint in h2h_attempts:
        try:
            print(f"\n  Trying: {endpoint}")
            result = api_client.get(endpoint)
            print(f"  ✓ Success! Got data:")
            print(json.dumps(result, indent=2)[:1000])
            
            # Save the data
            output_path = Path(__file__).parent.parent / "data" / "alcaraz_djokovic_h2h.json"
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n💾 Saved to: {output_path}")
            break
        except Exception as e:
            print(f"  ✗ Failed: {e}")
    
    # Alternative: Get recent events and filter
    print(f"\n🔍 Checking recent events for their matches...")
    try:
        events = api_client.get("/api/tennis/events/live")
        
        # Look for matches between these two players
        their_matches = []
        for event in events.get('events', []):
            home_id = event.get('homeTeam', {}).get('id')
            away_id = event.get('awayTeam', {}).get('id')
            
            if (home_id == alcaraz_id and away_id == djokovic_id) or \
               (home_id == djokovic_id and away_id == alcaraz_id):
                their_matches.append(event)
                print(f"\n  ✓ Found match!")
                print(f"    Tournament: {event.get('tournament', {}).get('name')}")
                print(f"    Status: {event.get('status', {}).get('description')}")
                print(f"    Score: {event.get('homeScore', {}).get('display')} - {event.get('awayScore', {}).get('display')}")
        
        if their_matches:
            output_path = Path(__file__).parent.parent / "data" / "alcaraz_djokovic_matches.json"
            with open(output_path, 'w') as f:
                json.dump(their_matches, f, indent=2)
            print(f"\n💾 Saved {len(their_matches)} matches to: {output_path}")
        else:
            print(f"\n  No direct matches found in current events")
            
    except Exception as e:
        print(f"✗ Error checking events: {e}")
    
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print("\nThe TennisAPI1 appears to have limited H2H history endpoints.")
    print("We have their current stats, but need a different approach for history.")
    print("\nOptions:")
    print("1. Use synthetic data (what we did)")
    print("2. Use a different API (API-SPORTS might have better H2H)")
    print("3. Manually create dataset from known match results")
    print("\nFor now, our model is trained on synthetic data that follows")
    print("realistic tennis patterns (ranking, age, experience, etc.)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
