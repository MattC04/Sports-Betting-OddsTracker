import os
import sys
import requests
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass


class OddsAPI:
    """Complete implementation of The Odds API v4"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.the-odds-api.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.last_response_headers = {}
    
    def _request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make API request and track usage"""
        if params is None:
            params = {}
        params['apiKey'] = self.api_key
        
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, params=params, timeout=30)
        
        # Store response headers for usage tracking
        self.last_response_headers = {
            'remaining': response.headers.get('x-requests-remaining', 'N/A'),
            'used': response.headers.get('x-requests-used', 'N/A'),
            'last': response.headers.get('x-requests-last', 'N/A')
        }
        
        # Print usage info
        print(f"  API Usage - Remaining: {self.last_response_headers['remaining']}, "
              f"Used: {self.last_response_headers['used']}, "
              f"Last Cost: {self.last_response_headers['last']}")
        
        response.raise_for_status()
        return response.json()
    
    # ==================== FREE ENDPOINTS ====================
    
    def get_sports(self, all_sports: bool = False) -> List[Dict]:
        """
        GET /v4/sports - List available sports (FREE)
        
        Args:
            all_sports: If True, returns both in and out of season sports
            
        Returns:
            List of sport objects with keys: key, group, title, description, active, has_outrights
        """
        params = {}
        if all_sports:
            params['all'] = 'true'
        
        return self._request("/v4/sports", params)
    
    def get_events(self, sport: str, date_format: str = 'iso',
                   event_ids: str = None, commence_time_from: str = None,
                   commence_time_to: str = None, include_rotation_numbers: bool = False) -> List[Dict]:
        """
        GET /v4/sports/{sport}/events - Get upcoming events (FREE)
        
        Args:
            sport: Sport key from get_sports()
            date_format: 'iso' or 'unix'
            event_ids: Comma-separated event IDs to filter
            commence_time_from: ISO format (e.g., '2023-09-09T00:00:00Z')
            commence_time_to: ISO format
            include_rotation_numbers: Include rotation numbers if available
            
        Returns:
            List of event objects with: id, sport_key, sport_title, commence_time, home_team, away_team
        """
        params = {'dateFormat': date_format}
        
        if event_ids:
            params['eventIds'] = event_ids
        if commence_time_from:
            params['commenceTimeFrom'] = commence_time_from
        if commence_time_to:
            params['commenceTimeTo'] = commence_time_to
        if include_rotation_numbers:
            params['includeRotationNumbers'] = 'true'
        
        return self._request(f"/v4/sports/{sport}/events", params)
    
    # ==================== PAID ENDPOINTS ====================
    
    def get_odds(self, sport: str, regions: str, markets: str = 'h2h',
                 odds_format: str = 'decimal', date_format: str = 'iso',
                 event_ids: str = None, bookmakers: str = None,
                 commence_time_from: str = None, commence_time_to: str = None,
                 include_links: bool = False, include_sids: bool = False,
                 include_bet_limits: bool = False, include_rotation_numbers: bool = False) -> List[Dict]:
        """
        GET /v4/sports/{sport}/odds - Get odds for multiple games
        COST: 1 credit per region per market
        
        Args:
            sport: Sport key (or 'upcoming' for next 8 games across all sports)
            regions: Comma-separated regions (us, us2, uk, eu, au)
            markets: Comma-separated markets (h2h, spreads, totals, outrights)
            odds_format: 'decimal' or 'american'
            date_format: 'iso' or 'unix'
            event_ids: Filter to specific game IDs
            bookmakers: Comma-separated bookmaker keys (10 bookmakers = 1 region)
            commence_time_from: ISO format
            commence_time_to: ISO format
            include_links: Include bookmaker links
            include_sids: Include source IDs
            include_bet_limits: Include bet limits (mainly exchanges)
            include_rotation_numbers: Include rotation numbers
            
        Returns:
            List of games with odds from bookmakers
            
        Notes:
            - Use for featured markets: h2h, spreads, totals
            - For player props, use get_event_odds() instead
            - Lay odds automatically included for exchanges (h2h_lay, outrights_lay)
        """
        params = {
            'regions': regions,
            'markets': markets,
            'oddsFormat': odds_format,
            'dateFormat': date_format
        }
        
        if event_ids:
            params['eventIds'] = event_ids
        if bookmakers:
            params['bookmakers'] = bookmakers
        if commence_time_from:
            params['commenceTimeFrom'] = commence_time_from
        if commence_time_to:
            params['commenceTimeTo'] = commence_time_to
        if include_links:
            params['includeLinks'] = 'true'
        if include_sids:
            params['includeSids'] = 'true'
        if include_bet_limits:
            params['includeBetLimits'] = 'true'
        if include_rotation_numbers:
            params['includeRotationNumbers'] = 'true'
        
        return self._request(f"/v4/sports/{sport}/odds", params)
    
    def get_scores(self, sport: str, days_from: int = None,
                   date_format: str = 'iso', event_ids: str = None) -> List[Dict]:
        """
        GET /v4/sports/{sport}/scores - Get live scores and results
        COST: 1 credit (2 if using days_from)
        
        Args:
            sport: Sport key from get_sports()
            days_from: Include completed games from last 1-3 days
            date_format: 'iso' or 'unix'
            event_ids: Filter to specific game IDs
            
        Returns:
            List of games with scores (if completed or live)
            Fields: id, sport_key, sport_title, commence_time, completed, 
                   home_team, away_team, scores, last_update
            
        Notes:
            - Live scores update every ~30 seconds
            - Only available for selected sports
        """
        params = {'dateFormat': date_format}
        
        if days_from:
            params['daysFrom'] = days_from
        if event_ids:
            params['eventIds'] = event_ids
        
        return self._request(f"/v4/sports/{sport}/scores", params)
    
    def get_event_odds(self, sport: str, event_id: str, regions: str, markets: str,
                       odds_format: str = 'decimal', date_format: str = 'iso',
                       bookmakers: str = None, include_links: bool = False,
                       include_sids: bool = False, include_bet_limits: bool = False,
                       include_multipliers: bool = False) -> Dict:
        """
        GET /v4/sports/{sport}/events/{eventId}/odds - Get detailed odds for ONE game
        COST: 1 credit per unique market returned × regions
        
        Args:
            sport: Sport key
            event_id: Event ID from get_events()
            regions: Comma-separated regions
            markets: Comma-separated markets (accepts ANY market including player props)
            odds_format: 'decimal' or 'american'
            date_format: 'iso' or 'unix'
            bookmakers: Comma-separated bookmaker keys
            include_links: Include bookmaker links
            include_sids: Include source IDs
            include_bet_limits: Include bet limits
            include_multipliers: Include multipliers for DFS sites
            
        Returns:
            Single game object with detailed odds
            
        IMPORTANT:
            - Player name is in 'description' field, NOT 'name' field
            - last_update is on MARKET level, not bookmaker level
            - Use this for: player props, period markets, alternate lines
            - Cost only charged for markets actually returned
            
        Available Player Props Markets (NBA):
            player_points, player_assists, player_rebounds, player_threes,
            player_steals, player_blocks, player_points_rebounds_assists,
            player_double_double, player_triple_double
            
        Available Player Props Markets (NFL):
            player_pass_tds, player_pass_yds, player_pass_completions,
            player_pass_attempts, player_pass_interceptions, player_rush_yds,
            player_rush_attempts, player_rush_longest, player_receptions,
            player_reception_yds, player_anytime_td, player_1st_td, player_last_td
        """
        params = {
            'regions': regions,
            'markets': markets,
            'oddsFormat': odds_format,
            'dateFormat': date_format
        }
        
        if bookmakers:
            params['bookmakers'] = bookmakers
        if include_links:
            params['includeLinks'] = 'true'
        if include_sids:
            params['includeSids'] = 'true'
        if include_bet_limits:
            params['includeBetLimits'] = 'true'
        if include_multipliers:
            params['includeMultipliers'] = 'true'
        
        return self._request(f"/v4/sports/{sport}/events/{event_id}/odds", params)
    
    def get_event_markets(self, sport: str, event_id: str, regions: str,
                         bookmakers: str = None, date_format: str = 'iso') -> Dict:
        """
        GET /v4/sports/{sport}/events/{eventId}/markets - Get available markets
        COST: 1 credit
        
        Args:
            sport: Sport key
            event_id: Event ID from get_events()
            regions: Comma-separated regions
            bookmakers: Comma-separated bookmaker keys
            date_format: 'iso' or 'unix'
            
        Returns:
            Game object with available market keys per bookmaker
            
        Notes:
            - Shows recently seen markets, not comprehensive list
            - More markets appear as game time approaches
            - Use to discover what markets to query with get_event_odds()
        """
        params = {'regions': regions, 'dateFormat': date_format}
        
        if bookmakers:
            params['bookmakers'] = bookmakers
        
        return self._request(f"/v4/sports/{sport}/events/{event_id}/markets", params)
    
    def get_participants(self, sport: str) -> List[Dict]:
        """
        GET /v4/sports/{sport}/participants - Get teams/players list
        COST: 1 credit
        
        Args:
            sport: Sport key
            
        Returns:
            List of participants with: full_name, id
            
        Notes:
            - For NBA: Returns teams
            - For tennis: Returns players
            - Does NOT return players on a team
            - Includes inactive participants (whitelist)
        """
        return self._request(f"/v4/sports/{sport}/participants")
    
    # ==================== HISTORICAL ENDPOINTS (10x COST) ====================
    
    def get_historical_odds(self, sport: str, regions: str, markets: str, date: str,
                           odds_format: str = 'decimal', date_format: str = 'iso',
                           event_ids: str = None, bookmakers: str = None,
                           commence_time_from: str = None, commence_time_to: str = None) -> Dict:
        """
        GET /v4/historical/sports/{sport}/odds - Get historical odds snapshot
        COST: 10 credits per region per market
        
        Args:
            sport: Sport key
            regions: Comma-separated regions
            markets: Comma-separated markets
            date: ISO timestamp (e.g., '2021-10-18T12:00:00Z')
            odds_format: 'decimal' or 'american'
            date_format: 'iso' or 'unix'
            event_ids: Filter to specific games
            bookmakers: Comma-separated bookmaker keys
            commence_time_from: ISO format
            commence_time_to: ISO format
            
        Returns:
            Snapshot object with: timestamp, previous_timestamp, next_timestamp, data
            
        Notes:
            - Returns closest snapshot equal to or earlier than date
            - Featured markets: Available from June 6, 2020
            - Additional markets (props): Available from May 3, 2023
            - Snapshots at 5 minute intervals (10 min before Sept 2022)
            - Only available on paid plans
        """
        params = {
            'regions': regions,
            'markets': markets,
            'date': date,
            'oddsFormat': odds_format,
            'dateFormat': date_format
        }
        
        if event_ids:
            params['eventIds'] = event_ids
        if bookmakers:
            params['bookmakers'] = bookmakers
        if commence_time_from:
            params['commenceTimeFrom'] = commence_time_from
        if commence_time_to:
            params['commenceTimeTo'] = commence_time_to
        
        return self._request(f"/v4/historical/sports/{sport}/odds", params)
    
    def get_historical_events(self, sport: str, date: str, date_format: str = 'iso',
                             event_ids: str = None, commence_time_from: str = None,
                             commence_time_to: str = None, include_rotation_numbers: bool = False) -> Dict:
        """
        GET /v4/historical/sports/{sport}/events - Get historical events
        COST: 1 credit (if events found)
        
        Args:
            sport: Sport key
            date: ISO timestamp
            date_format: 'iso' or 'unix'
            event_ids: Filter to specific games
            commence_time_from: ISO format
            commence_time_to: ISO format
            include_rotation_numbers: Include rotation numbers
            
        Returns:
            Snapshot object with: timestamp, previous_timestamp, next_timestamp, data
            
        Notes:
            - Use to find historical event IDs
            - Only available on paid plans
        """
        params = {
            'date': date,
            'dateFormat': date_format
        }
        
        if event_ids:
            params['eventIds'] = event_ids
        if commence_time_from:
            params['commenceTimeFrom'] = commence_time_from
        if commence_time_to:
            params['commenceTimeTo'] = commence_time_to
        if include_rotation_numbers:
            params['includeRotationNumbers'] = 'true'
        
        return self._request(f"/v4/historical/sports/{sport}/events", params)
    
    def get_historical_event_odds(self, sport: str, event_id: str, regions: str,
                                  markets: str, date: str, odds_format: str = 'decimal',
                                  date_format: str = 'iso', bookmakers: str = None,
                                  include_multipliers: bool = False) -> Dict:
        """
        GET /v4/historical/sports/{sport}/events/{eventId}/odds - Historical odds for ONE game
        COST: 10 credits per unique market returned × regions
        
        Args:
            sport: Sport key
            event_id: Historical event ID from get_historical_events()
            regions: Comma-separated regions
            markets: Comma-separated markets (including player props)
            date: ISO timestamp
            odds_format: 'decimal' or 'american'
            date_format: 'iso' or 'unix'
            bookmakers: Comma-separated bookmaker keys
            include_multipliers: Include multipliers for DFS
            
        Returns:
            Snapshot object with: timestamp, previous_timestamp, next_timestamp, data
            
        Notes:
            - Additional markets (props) available from May 3, 2023
            - Snapshots at 5 minute intervals
            - Only available on paid plans
            - Cost only for markets actually returned
        """
        params = {
            'regions': regions,
            'markets': markets,
            'date': date,
            'oddsFormat': odds_format,
            'dateFormat': date_format
        }
        
        if bookmakers:
            params['bookmakers'] = bookmakers
        if include_multipliers:
            params['includeMultipliers'] = 'true'
        
        return self._request(f"/v4/historical/sports/{sport}/events/{event_id}/odds", params)


class Database:
    """Enhanced database for storing all API data"""
    
    def __init__(self, db_path: str = "data/odds_data.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', exist_ok=True)
        self._create_tables()
    
    def _create_tables(self):
        """Create all database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sports table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sports (
                key TEXT PRIMARY KEY,
                group_name TEXT,
                title TEXT,
                description TEXT,
                active INTEGER,
                has_outrights INTEGER,
                updated_at TEXT
            )
        """)
        
        # Events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                sport_key TEXT,
                sport_title TEXT,
                commence_time TEXT,
                home_team TEXT,
                away_team TEXT,
                updated_at TEXT
            )
        """)
        
        # Scores table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT,
                sport_key TEXT,
                sport_title TEXT,
                commence_time TEXT,
                completed INTEGER,
                home_team TEXT,
                away_team TEXT,
                home_score TEXT,
                away_score TEXT,
                last_update TEXT,
                scraped_at TEXT
            )
        """)
        
        # Game odds table (h2h, spreads, totals)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS game_odds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT,
                sport_key TEXT,
                bookmaker_key TEXT,
                bookmaker_title TEXT,
                market_key TEXT,
                outcome_name TEXT,
                outcome_price REAL,
                outcome_point REAL,
                last_update TEXT,
                scraped_at TEXT
            )
        """)
        
        # Player props table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_props (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT,
                sport_key TEXT,
                sport_title TEXT,
                home_team TEXT,
                away_team TEXT,
                commence_time TEXT,
                player_name TEXT,
                prop_type TEXT,
                outcome_name TEXT,
                outcome_price REAL,
                outcome_point REAL,
                bookmaker_key TEXT,
                bookmaker_title TEXT,
                market_last_update TEXT,
                scraped_at TEXT
            )
        """)
        
        # Available markets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS available_markets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT,
                sport_key TEXT,
                bookmaker_key TEXT,
                bookmaker_title TEXT,
                market_key TEXT,
                market_last_update TEXT,
                scraped_at TEXT
            )
        """)
        
        # Participants table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS participants (
                id TEXT PRIMARY KEY,
                sport_key TEXT,
                full_name TEXT,
                scraped_at TEXT
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_sport ON events(sport_key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_time ON events(commence_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scores_event ON scores(event_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_game_odds_event ON game_odds(event_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_props_event ON player_props(event_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_props_player ON player_props(player_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_props_time ON player_props(commence_time)")
        
        conn.commit()
        conn.close()
        print(f"Database initialized: {self.db_path}")
    
    def save_sports(self, sports: List[Dict]):
        """Save sports list"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for sport in sports:
            cursor.execute("""
                INSERT OR REPLACE INTO sports VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                sport['key'],
                sport.get('group', ''),
                sport.get('title', ''),
                sport.get('description', ''),
                1 if sport.get('active') else 0,
                1 if sport.get('has_outrights') else 0,
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
        print(f"Saved {len(sports)} sports")
    
    def save_events(self, events: List[Dict]):
        """Save events"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for event in events:
            cursor.execute("""
                INSERT OR REPLACE INTO events VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                event['id'],
                event['sport_key'],
                event.get('sport_title', ''),
                event.get('commence_time', ''),
                event.get('home_team', ''),
                event.get('away_team', ''),
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
        print(f"Saved {len(events)} events")
    
    def save_scores(self, scores: List[Dict]):
        """Save scores"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for score in scores:
            home_score = None
            away_score = None
            if score.get('scores'):
                for s in score['scores']:
                    if s['name'] == score['home_team']:
                        home_score = s['score']
                    elif s['name'] == score['away_team']:
                        away_score = s['score']
            
            cursor.execute("""
                INSERT INTO scores VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                score['id'],
                score['sport_key'],
                score.get('sport_title', ''),
                score.get('commence_time', ''),
                1 if score.get('completed') else 0,
                score.get('home_team', ''),
                score.get('away_team', ''),
                home_score,
                away_score,
                score.get('last_update', ''),
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
        print(f"Saved {len(scores)} scores")
    
    def save_player_props(self, event_data: Dict) -> int:
        """Save player props from event odds response"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        count = 0
        for bookmaker in event_data.get('bookmakers', []):
            for market in bookmaker.get('markets', []):
                # Check if this is a player prop market (has 'description' field)
                has_player_props = any('description' in outcome for outcome in market.get('outcomes', []))
                
                if has_player_props:
                    for outcome in market['outcomes']:
                        player_name = outcome.get('description', '')
                        if player_name:  # Only save if has player name
                            cursor.execute("""
                                INSERT INTO player_props VALUES 
                                (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                event_data['id'],
                                event_data['sport_key'],
                                event_data.get('sport_title', ''),
                                event_data.get('home_team', ''),
                                event_data.get('away_team', ''),
                                event_data.get('commence_time', ''),
                                player_name,
                                market['key'],
                                outcome.get('name', ''),
                                outcome.get('price'),
                                outcome.get('point'),
                                bookmaker['key'],
                                bookmaker['title'],
                                market.get('last_update', ''),
                                datetime.now().isoformat()
                            ))
                            count += 1
        
        conn.commit()
        conn.close()
        return count
    
    def save_participants(self, participants: List[Dict], sport_key: str):
        """Save participants"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for participant in participants:
            cursor.execute("""
                INSERT OR REPLACE INTO participants VALUES (?, ?, ?, ?)
            """, (
                participant.get('id', ''),
                sport_key,
                participant.get('full_name', ''),
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
        print(f"Saved {len(participants)} participants")


def main():
    """Main scraper function"""
    print("="*80)
    print("ENHANCED ODDS API SCRAPER")
    print("Based on Official The Odds API v4 Documentation")
    print("="*80)
    
    # Get API key
    api_key = os.getenv('ODDS_API_KEY')
    if not api_key:
        print("\nERROR: ODDS_API_KEY not set")
        print("Set it in your .env file or environment")
        return
    
    # Initialize
    api = OddsAPI(api_key)
    db = Database()
    
    # Get sport from command line or default to NBA
    sport = sys.argv[1] if len(sys.argv) > 1 else "basketball_nba"
    
    print(f"\nTarget Sport: {sport}")
    print("="*80)
    
    try:
        # 1. Get available sports (FREE)
        print("\n[1/6] Fetching available sports (FREE)...")
        sports = api.get_sports()
        print(f"  Found {len(sports)} sports")
        db.save_sports(sports)
        
        # 2. Get events (FREE)
        print("\n[2/6] Fetching events schedule (FREE)...")
        events = api.get_events(sport)
        print(f"  Found {len(events)} upcoming events")
        
        if not events:
            print("\n  No events found for this sport.")
            print("  The sport may be out of season or no games scheduled soon.")
            return
        
        db.save_events(events)
        
        # Show next 3 games
        print("\n  Next games:")
        for i, event in enumerate(events[:3], 1):
            try:
                commence = datetime.fromisoformat(event['commence_time'].replace('Z', '+00:00'))
                print(f"    {i}. {event['away_team']} @ {event['home_team']}")
                print(f"       {commence.strftime('%b %d, %I:%M %p')}")
            except:
                pass
        
        # 3. Get scores (COSTS: 2 credits with days_from)
        print("\n[3/6] Fetching scores (COSTS 2 credits)...")
        try:
            scores = api.get_scores(sport, days_from=1)
            print(f"  Found {len(scores)} games with scores")
            db.save_scores(scores)
        except Exception as e:
            print(f"  Scores not available: {e}")
        
        # 4. Get participants (COSTS: 1 credit)
        print("\n[4/6] Fetching participants (COSTS 1 credit)...")
        try:
            participants = api.get_participants(sport)
            print(f"  Found {len(participants)} participants")
            db.save_participants(participants, sport)
        except Exception as e:
            print(f"  Participants not available: {e}")
        
        # 5. Get player props for upcoming games
        print("\n[5/6] Fetching player props for upcoming games...")
        
        # Filter to upcoming games only
        now = datetime.now(datetime.now().astimezone().tzinfo)
        upcoming = []
        for event in events:
            try:
                commence = datetime.fromisoformat(event['commence_time'].replace('Z', '+00:00'))
                if commence > now:
                    upcoming.append(event)
            except:
                continue
        
        print(f"  Found {len(upcoming)} upcoming games")
        
        if upcoming:
            # Common player prop markets by sport
            prop_markets = {
                'basketball_nba': 'player_points,player_assists,player_rebounds,player_threes',
                'americanfootball_nfl': 'player_pass_tds,player_pass_yds,player_rush_yds,player_receptions',
                'baseball_mlb': 'batter_hits,batter_home_runs,pitcher_strikeouts',
                'icehockey_nhl': 'player_points,player_shots_on_goal'
            }
            
            markets = prop_markets.get(sport, 'player_points,player_assists,player_rebounds')
            
            # Get props for first 3 upcoming games
            total_props = 0
            for i, event in enumerate(upcoming[:3], 1):
                print(f"\n  Game {i}/{min(3, len(upcoming))}: {event['away_team']} @ {event['home_team']}")
                
                try:
                    event_odds = api.get_event_odds(
                        sport=sport,
                        event_id=event['id'],
                        regions='us',
                        markets=markets,
                        odds_format='decimal'
                    )
                    
                    count = db.save_player_props(event_odds)
                    total_props += count
                    print(f"  Saved {count} player props")
                    
                except Exception as e:
                    print(f"  Props not available: {e}")
                    print(f"  (Props usually appear 2-4 hours before game time)")
            
            print(f"\n  Total props saved: {total_props}")
        else:
            print("  No upcoming games to fetch props for")
        
        # 6. Summary
        print("\n" + "="*80)
        print("SCRAPING COMPLETE")
        print("="*80)
        print(f"\nDatabase: {db.db_path}")
        print("\nNext steps:")
        print("  1. Start dashboard: python dashboard.py")
        print("  2. Open browser: http://localhost:5000")
        print("  3. Run scraper again to update data")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()