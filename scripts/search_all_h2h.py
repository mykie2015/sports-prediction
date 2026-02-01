#!/usr/bin/env python3
"""
Deep Search for ALL Alcaraz vs Djokovic Historical Matches
===========================================================
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sports_prediction.data.api_client import APIClient


def load_env():
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


def main():
    load_env()
    
    api_client = APIClient(
        base_url=f"https://tennisapi1.p.rapidapi.com",
        api_key=os.getenv('RAPIDAPI_KEY'),
        host='tennisapi1.p.rapidapi.com'
    )
    
    alcaraz_id = 275923
    djokovic_id = 14882
    
    print("\n" + "="*80)
    print("DEEP SEARCH: ALL ALCARAZ vs DJOKOVIC MATCHES")
    print("="*80)
    
    all_matches = []
    
    # Strategy 1: Search by player last matches
    print("\n1️⃣  Checking Alcaraz's last matches...")
    try:
        alcaraz_matches = api_client.get(f"/api/tennis/player/{alcaraz_id}/matches/last/0")
        
        if 'events' in alcaraz_matches:
            print(f"   Found {len(alcaraz_matches['events'])} recent Alcaraz matches")
            
            # Filter for matches vs Djokovic
            for match in alcaraz_matches['events']:
                home_id = match.get('homeTeam', {}).get('id')
                away_id = match.get('awayTeam', {}).get('id')
                
                if home_id == djokovic_id or away_id == djokovic_id:
                    all_matches.append(match)
                    print(f"\n   ✓ MATCH FOUND!")
                    print(f"     Date: {datetime.fromtimestamp(match.get('startTimestamp', 0))}")
                    print(f"     Tournament: {match.get('tournament', {}).get('name')}")
                    print(f"     Round: {match.get('roundInfo', {}).get('name')}")
                    print(f"     Status: {match.get('status', {}).get('description')}")
                    score = match.get('homeScore', {}).get('display', '?')
                    score2 = match.get('awayScore', {}).get('display', '?')
                    print(f"     Score: {score} - {score2}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Strategy 2: Check Djokovic's last matches
    print("\n2️⃣  Checking Djokovic's last matches...")
    try:
        djokovic_matches = api_client.get(f"/api/tennis/player/{djokovic_id}/matches/last/0")
        
        if 'events' in djokovic_matches:
            print(f"   Found {len(djokovic_matches['events'])} recent Djokovic matches")
            
            for match in djokovic_matches['events']:
                home_id = match.get('homeTeam', {}).get('id')
                away_id = match.get('awayTeam', {}).get('id')
                
                if home_id == alcaraz_id or away_id == alcaraz_id:
                    # Check if we already have this match
                    match_id = match.get('id')
                    if not any(m.get('id') == match_id for m in all_matches):
                        all_matches.append(match)
                        print(f"\n   ✓ NEW MATCH FOUND!")
                        print(f"     Date: {datetime.fromtimestamp(match.get('startTimestamp', 0))}")
                        print(f"     Tournament: {match.get('tournament', {}).get('name')}")
                        print(f"     Round: {match.get('roundInfo', {}).get('name')}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Strategy 3: Try tournament-specific searches (Grand Slams)
    print("\n3️⃣  Checking Grand Slam tournaments...")
    grand_slams = [
        (2449, "US Open"),
        (2513, "Australian Open"),
        (2452, "Wimbledon"),
        (2451, "Roland Garros")
    ]
    
    for tournament_id, tournament_name in grand_slams:
        try:
            print(f"\n   Checking {tournament_name} (ID: {tournament_id})...")
            # Try different year ranges
            for year in [2025, 2024, 2023, 2022]:
                try:
                    events = api_client.get(f"/api/tennis/tournament/{tournament_id}/season/{year}/events")
                    
                    if 'events' in events:
                        for match in events['events']:
                            home_id = match.get('homeTeam', {}).get('id')
                            away_id = match.get('awayTeam', {}).get('id')
                            
                            if (home_id == alcaraz_id and away_id == djokovic_id) or \
                               (home_id == djokovic_id and away_id == alcaraz_id):
                                match_id = match.get('id')
                                if not any(m.get('id') == match_id for m in all_matches):
                                    all_matches.append(match)
                                    print(f"     ✓ Found {year} match!")
                except:
                    pass
        except Exception as e:
            pass
    
    # Save all matches
    print("\n" + "="*80)
    print(f"TOTAL MATCHES FOUND: {len(all_matches)}")
    print("="*80)
    
    if all_matches:
        output_path = Path(__file__).parent.parent / "data" / "alcaraz_djokovic_all_matches.json"
        with open(output_path, 'w') as f:
            json.dump(all_matches, f, indent=2)
        print(f"\n💾 Saved to: {output_path}")
        
        # Summary
        print("\n📋 MATCH SUMMARY:")
        for i, match in enumerate(sorted(all_matches, key=lambda x: x.get('startTimestamp', 0)), 1):
            date = datetime.fromtimestamp(match.get('startTimestamp', 0))
            tournament = match.get('tournament', {}).get('name', 'Unknown')
            round_name = match.get('roundInfo', {}).get('name', '')
            print(f"{i}. {date.strftime('%Y-%m-%d')} | {tournament} | {round_name}")
    else:
        print("\n⚠️  No matches found. The API may have limited historical data.")
        print("    Real H2H record (as of 2026): They've played ~10+ times")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
