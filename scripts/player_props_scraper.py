"""
Player props scraper and database storage.
Fetches player props from Odds API and stores in SQLite database.
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional
import logging
from scripts.odds_api_scraper import OddsAPIClient

logger = logging.getLogger(__name__)


class PlayerPropsDatabase:
    """Database manager for storing player props."""
    
    def __init__(self, db_path: str = "data/player_props.db"):
        self.db_path = db_path
        self._setup_database()
    
    def _setup_database(self):
        """Create SQLite database with optimized schema."""
        os.makedirs(os.path.dirname(self.db_path) if os.path.dirname(self.db_path) else '.', exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_props (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL,
                sport_key TEXT NOT NULL,
                sport_title TEXT,
                home_team TEXT,
                away_team TEXT,
                commence_time TIMESTAMP,
                player_name TEXT NOT NULL,
                prop_type TEXT,
                outcome_name TEXT,
                outcome_price REAL,
                outcome_point REAL,
                bookmaker_key TEXT,
                bookmaker_title TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_update TIMESTAMP,
                UNIQUE(event_id, player_name, prop_type, bookmaker_key, outcome_name)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_player_props_sport ON player_props(sport_key);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_player_props_player ON player_props(player_name);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_player_props_event ON player_props(event_id);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_player_props_scraped ON player_props(scraped_at);
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    def save_player_props(self, props_data: List[Dict]):
        """Save player props to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        saved = 0
        for prop in props_data:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO player_props 
                    (event_id, sport_key, sport_title, home_team, away_team, commence_time,
                     player_name, prop_type, outcome_name, outcome_price, outcome_point,
                     bookmaker_key, bookmaker_title, scraped_at, last_update)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    prop.get('event_id', ''),
                    prop.get('sport_key', ''),
                    prop.get('sport_title', ''),
                    prop.get('home_team', ''),
                    prop.get('away_team', ''),
                    prop.get('commence_time', ''),
                    prop.get('player_name', ''),
                    prop.get('prop_type', ''),
                    prop.get('outcome_name', ''),
                    prop.get('outcome_price'),
                    prop.get('outcome_point'),
                    prop.get('bookmaker_key', ''),
                    prop.get('bookmaker_title', ''),
                    datetime.now().isoformat(),
                    prop.get('last_update', '')
                ))
                saved += 1
            except sqlite3.Error as e:
                logger.error(f"Error saving prop: {e}")
                continue
        
        conn.commit()
        conn.close()
        logger.info(f"Saved {saved} player props to database")
        return saved
    
    def get_player_props(self, sport_key: Optional[str] = None, 
                        player_name: Optional[str] = None,
                        limit: int = 100) -> List[Dict]:
        """Get player props from database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM player_props WHERE 1=1"
        params = []
        
        if sport_key:
            query += " AND sport_key = ?"
            params.append(sport_key)
        
        if player_name:
            query += " AND player_name LIKE ?"
            params.append(f"%{player_name}%")
        
        query += " ORDER BY scraped_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        conn.close()
        return [dict(row) for row in rows]
    
    def get_props_by_player(self, player_name: str, sport_key: Optional[str] = None) -> List[Dict]:
        """Get all props for a specific player."""
        return self.get_player_props(sport_key=sport_key, player_name=player_name, limit=1000)
    
    def get_recent_props(self, hours: int = 24) -> List[Dict]:
        """Get props from the last N hours."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM player_props 
            WHERE scraped_at >= datetime('now', '-{} hours')
            ORDER BY scraped_at DESC
        """.format(hours))
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]


def scrape_player_props(api_key: str, sport: str = "basketball_nba", 
                       regions: str = "us", odds_format: str = "decimal",
                       db_path: str = "data/player_props.db") -> List[Dict]:
    """
    Scrape player props and save to database.
    
    Args:
        api_key: Odds API key
        sport: Sport key (e.g., 'basketball_nba', 'americanfootball_nfl')
        regions: Comma-separated regions (default: 'us')
        odds_format: Format for odds - 'american' or 'decimal' (default: 'decimal')
        db_path: Path to SQLite database
        
    Returns:
        List of player props records
    """
    client = OddsAPIClient(api_key)
    db = PlayerPropsDatabase(db_path)
    
    logger.info(f"Fetching player props for sport: {sport}")
    logger.warning(
        "NOTE: The Odds API v4 may not support player_props market. "
        "This feature may require a premium subscription or may not be available. "
        "Attempting to fetch player props..."
    )
    
    try:
        try:
            odds_data = client.get_player_props(sport=sport, regions=regions, odds_format=odds_format)
        except ValueError as e:
            logger.error(str(e))
            logger.info(
                "\n💡 Alternative Solutions:\n"
                "1. Player props may require a premium Odds API subscription\n"
                "2. Consider using PrizePicks or DraftKings APIs for player props\n"
                "3. Some sportsbooks provide player props in their regular odds feeds\n"
                "4. Check The Odds API documentation for supported markets: "
                "https://the-odds-api.com/liveapi/guides/v4/"
            )
            return []
        
        props_records = []
        events = odds_data if isinstance(odds_data, list) else []
        
        for event in events:
            event_id = event.get('id', '')
            sport_key = event.get('sport_key', sport)
            sport_title = event.get('sport_title', sport_key)
            home_team = event.get('home_team', '')
            away_team = event.get('away_team', '')
            commence_time = event.get('commence_time', '')
            
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
                        player_name = outcome.get('description', '') or outcome.get('name', '')
                        
                        prop_record = {
                            'event_id': event_id,
                            'sport_key': sport_key,
                            'sport_title': sport_title,
                            'home_team': home_team,
                            'away_team': away_team,
                            'commence_time': commence_time,
                            'player_name': player_name,
                            'prop_type': market_key,
                            'outcome_name': outcome.get('name', ''),
                            'outcome_price': outcome.get('price'),
                            'outcome_point': outcome.get('point'),
                            'bookmaker_key': bookmaker_key,
                            'bookmaker_title': bookmaker_title,
                            'last_update': market_last_update or last_update
                        }
                        props_records.append(prop_record)
        
        if props_records:
            saved = db.save_player_props(props_records)
            logger.info(f"Successfully scraped and saved {saved} player props")
            return props_records
        else:
            logger.warning("No player props found")
            return []
            
    except Exception as e:
        logger.error(f"Error fetching player props: {e}")
        raise

