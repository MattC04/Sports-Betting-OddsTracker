"""
Odds API scraper for sports betting odds data.
Fetches sports, events, and odds from The Odds API (api.the-odds-api.com).
Uses API v4 endpoints.
"""

import requests
import pandas as pd
import time
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


class OddsAPIClient:
    """Client for interacting with The Odds API v4."""
    
    BASE_URL = "https://api.the-odds-api.com/v4"
    
    def __init__(self, api_key: str, timeout: int = 30):
        """
        Initialize the Odds API client.
        
        Args:
            api_key: Your Odds API key
            timeout: Request timeout in seconds
        """
        if not api_key:
            raise ValueError("API key is required. Set ODDS_API_KEY environment variable or pass it directly.")
        
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """
        Make a request to The Odds API v4.
        
        Args:
            endpoint: API endpoint (e.g., '/sports', '/sports/{sport}/odds')
            params: Query parameters
            
        Returns:
            JSON response (can be list or dict)
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        if params is None:
            params = {}
        
        # Add API key to params
        params['apiKey'] = self.api_key
        
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            # Check usage quota from headers
            if 'x-requests-remaining' in response.headers:
                remaining = response.headers.get('x-requests-remaining', 'N/A')
                used = response.headers.get('x-requests-used', 'N/A')
                print(f"📊 API Usage - Remaining: {remaining}, Used: {used}")
            
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise ValueError("Invalid API key. Please check your ODDS_API_KEY.")
            elif response.status_code == 429:
                raise ValueError("Rate limit exceeded. Please wait before making more requests.")
            else:
                error_text = response.text if hasattr(response, 'text') else str(e)
                raise Exception(f"HTTP error {response.status_code}: {error_text}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
    
    def get_sports(self, all_sports: bool = False) -> List[Dict[str, Any]]:
        """
        Get list of available sports.
        This endpoint doesn't require authentication and doesn't count against quota.
        
        Args:
            all_sports: If True, returns both in-season and out-of-season sports
        
        Returns:
            List of sports with their keys and details
        """
        url = f"{self.BASE_URL}/sports"
        params = {'apiKey': self.api_key}  # apiKey param is recommended but not strictly required
        if all_sports:
            params['all'] = 'true'
        
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch sports: {e}")
    
    def get_events(self, sport: str, date_format: str = "iso") -> List[Dict[str, Any]]:
        """
        Get events for a specific sport (without odds).
        This endpoint does not count against the usage quota.
        
        Args:
            sport: Sport key (e.g., 'basketball_nba', 'americanfootball_nfl', or 'upcoming')
            date_format: Date format - 'iso' or 'unix' (default: 'iso')
            
        Returns:
            List of events
        """
        endpoint = f"/sports/{sport}/events"
        params = {
            'dateFormat': date_format
        }
        
        return self._make_request(endpoint, params)
    
    def get_odds(self, sport: str, regions: str = "us", markets: str = "h2h", 
                 odds_format: str = "decimal", date_format: str = "iso") -> List[Dict[str, Any]]:
        """
        Get odds for a specific sport.
        
        Args:
            sport: Sport key (e.g., 'basketball_nba', 'americanfootball_nfl', or 'upcoming')
            regions: Comma-separated list of regions (default: 'us')
            markets: Comma-separated list of markets (default: 'h2h')
                     Options: 'h2h' (head-to-head/moneyline), 'spreads', 'totals', 'outrights', 'player_props'
            odds_format: Format for odds - 'american' or 'decimal' (default: 'decimal')
            date_format: Date format - 'iso' or 'unix' (default: 'iso')
            
        Returns:
            List of events with their odds
        """
        endpoint = f"/sports/{sport}/odds"
        params = {
            'regions': regions,
            'markets': markets,
            'oddsFormat': odds_format,
            'dateFormat': date_format
        }
        
        return self._make_request(endpoint, params)
    
    def get_player_props(self, sport: str, regions: str = "us", odds_format: str = "decimal") -> List[Dict[str, Any]]:
        """
        Get player props for a specific sport.
        
        Note: The Odds API v4 may not support 'player_props' as a market type.
        This function attempts to fetch player props, but will return an empty list
        if not available. Player props may require a premium API plan or different endpoint.
        
        Args:
            sport: Sport key (e.g., 'basketball_nba', 'americanfootball_nfl')
            regions: Comma-separated list of regions (default: 'us')
            odds_format: Format for odds - 'american' or 'decimal' (default: 'decimal')
            
        Returns:
            List of events with player props, or empty list if not available
            
        Raises:
            Exception: If API returns an error (may indicate player props not available)
        """
        # Try different market names that might contain player props
        possible_markets = [
            "player_props",
            "player_points",
            "player_assists", 
            "player_rebounds",
            "props"
        ]
        
        for market in possible_markets:
            try:
                result = self.get_odds(sport=sport, regions=regions, markets=market, odds_format=odds_format)
                if result:
                    return result
            except Exception as e:
                # If it's not an invalid market error, re-raise it
                if "INVALID_MARKET" not in str(e) and "422" not in str(e):
                    raise
                continue
        
        # If none of the markets work, return empty list with helpful message
        raise ValueError(
            f"Player props are not available for {sport}. "
            f"The Odds API v4 may not support player props, or they may require a premium subscription. "
            f"Available markets are typically: 'h2h', 'spreads', 'totals', 'outrights'. "
            f"Please check The Odds API documentation or your subscription plan."
        )


def scrape_odds_data(api_key: str, sport: str = "basketball_nba", regions: str = "us", 
                    markets: str = "h2h,spreads", odds_format: str = "decimal",
                    output_file: str = "data/odds_data.csv",
                    save_raw: Optional[str] = None) -> pd.DataFrame:
    """
    Scrape odds data from Odds API and save to CSV.
    
    Args:
        api_key: Odds API key
        sport: Sport key (e.g., 'basketball_nba', 'americanfootball_nfl', 'baseball_mlb')
        regions: Comma-separated regions (default: 'us')
        markets: Comma-separated markets (default: 'h2h,spreads,totals')
        output_file: Path to output CSV file
        save_raw: Optional path to save raw JSON response
        
    Returns:
        DataFrame with odds data
    """
    client = OddsAPIClient(api_key)
    
    print(f"Fetching odds for sport: {sport}")
    print(f"Regions: {regions}, Markets: {markets}, Odds Format: {odds_format}")
    
    # Fetch odds data
    try:
        odds_data = client.get_odds(sport=sport, regions=regions, markets=markets, odds_format=odds_format)
        
        # Save raw JSON if requested
        if save_raw:
            os.makedirs(os.path.dirname(save_raw) if os.path.dirname(save_raw) else '.', exist_ok=True)
            with open(save_raw, 'w') as f:
                json.dump(odds_data, f, indent=2)
            print(f"Raw JSON saved to {save_raw}")
        
        # Parse and flatten the data
        # v4 API returns a direct list of events
        records = []
        events = odds_data if isinstance(odds_data, list) else []
        
        for event in events:
            event_id = event.get('id', '')
            sport_key = event.get('sport_key', sport)
            sport_title = event.get('sport_title', sport_key)
            home_team = event.get('home_team', '')
            away_team = event.get('away_team', '')
            commence_time = event.get('commence_time', '')
            
            # Extract bookmakers and their odds
            bookmakers = event.get('bookmakers', [])
            
            for bookmaker in bookmakers:
                bookmaker_key = bookmaker.get('key', '')
                bookmaker_title = bookmaker.get('title', '')
                last_update = bookmaker.get('last_update', '')
                
                markets_data = bookmaker.get('markets', [])
                
                for market in markets_data:
                    market_key = market.get('key', '')
                    market_last_update = market.get('last_update', '')
                    
                    outcomes = market.get('outcomes', [])
                    
                    for outcome in outcomes:
                        # Extract player name from description (for player props)
                        player_name = outcome.get('description', '') or outcome.get('name', '')
                        
                        record = {
                            'event_id': event_id,
                            'sport_key': sport_key,
                            'sport_title': sport_title,
                            'home_team': home_team,
                            'away_team': away_team,
                            'commence_time': commence_time,
                            'bookmaker_key': bookmaker_key,
                            'bookmaker_title': bookmaker_title,
                            'market': market_key,
                            'outcome_name': outcome.get('name', ''),
                            'player_name': player_name,  # For player props
                            'outcome_price': outcome.get('price', ''),
                            'outcome_point': outcome.get('point', ''),
                            'outcome_description': outcome.get('description', ''),
                            'prop_type': market_key if market_key == 'player_props' else '',  # Identify prop type
                            'last_update': market_last_update or last_update,
                            'scraped_at': datetime.now().isoformat()
                        }
                        records.append(record)
        
        # Create DataFrame
        if records:
            df = pd.DataFrame(records)
            
            # Save to CSV
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
            df.to_csv(output_file, index=False)
            
            print(f"\n✅ Successfully scraped {len(records)} odds records")
            print(f"📊 Events found: {len(events)}")
            print(f"💾 Data saved to {output_file}")
            print(f"\nSample data:")
            print(df.head(10).to_string(index=False))
            
            return df
        else:
            print("❌ No odds data found")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"❌ Error fetching odds: {e}")
        raise


def list_available_sports(api_key: Optional[str] = None, all_sports: bool = False) -> pd.DataFrame:
    """
    List all available sports from The Odds API.
    This endpoint doesn't require authentication and doesn't count against quota.
    
    Args:
        api_key: Optional API key (not required, but can be used)
        all_sports: If True, returns both in-season and out-of-season sports
        
    Returns:
        DataFrame with available sports
    """
    try:
        if api_key:
            client = OddsAPIClient(api_key)
            sports = client.get_sports(all_sports=all_sports)
        else:
            # Sports endpoint doesn't require auth, but apiKey param is still needed
            url = "https://api.the-odds-api.com/v4/sports"
            params = {}
            if all_sports:
                params['all'] = 'true'
            # Note: Even without auth, some endpoints may want apiKey param
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            sports = response.json()
        
        df = pd.DataFrame(sports)
        print("\n📋 Available Sports:")
        print(df.to_string(index=False))
        return df
    except Exception as e:
        print(f"❌ Error fetching sports list: {e}")
        raise


if __name__ == "__main__":
    # Example usage
    api_key = os.getenv('ODDS_API_KEY')
    
    if not api_key:
        print("⚠️  ODDS_API_KEY environment variable not set.")
        print("Please set it using: export ODDS_API_KEY='your_api_key'")
        print("\nFetching available sports (no API key required)...")
        list_available_sports()
    else:
        # List sports
        print("Available sports:")
        list_available_sports(api_key)
        
        # Scrape NBA odds
        print("\n" + "="*50)
        scrape_odds_data(
            api_key=api_key,
            sport="basketball_nba",
            regions="us",
            markets="h2h,spreads",
            odds_format="decimal",
            output_file="data/nba_odds.csv"
        )

