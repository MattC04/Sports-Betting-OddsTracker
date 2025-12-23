"""
Debug script - Test the exact queries the dashboard uses
"""

import sqlite3
import os
from datetime import datetime, timedelta

# Find database
possible_dbs = [
    'data/odds_data.db',
    'data/player_props.db',
    'data/enhanced_odds.db'
]

DB_PATH = None
for db in possible_dbs:
    if os.path.exists(db):
        DB_PATH = db
        break

if not DB_PATH:
    print("ERROR: No database found!")
    exit(1)

print("="*70)
print(f"Testing database: {DB_PATH}")
print("="*70)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check table structure
print("\n1. TABLE STRUCTURE")
print("-"*70)
cursor.execute("PRAGMA table_info(player_props)")
columns = cursor.fetchall()
print("Columns in player_props:")
for col in columns:
    print(f"  - {col[1]} ({col[2]})")

# Check total data
print("\n2. TOTAL DATA")
print("-"*70)
cursor.execute("SELECT COUNT(*) as count FROM player_props")
total = cursor.fetchone()[0]
print(f"Total props: {total}")

cursor.execute("SELECT COUNT(DISTINCT event_id) as count FROM player_props")
events = cursor.fetchone()[0]
print(f"Total events: {events}")

# Check date range
print("\n3. DATE RANGE OF DATA")
print("-"*70)
cursor.execute("""
    SELECT 
        MIN(commence_time) as earliest,
        MAX(commence_time) as latest,
        COUNT(DISTINCT DATE(commence_time)) as unique_dates
    FROM player_props
""")
row = cursor.fetchone()
print(f"Earliest game: {row['earliest']}")
print(f"Latest game: {row['latest']}")
print(f"Unique dates: {row['unique_dates']}")

# Show all games with their dates
print("\n4. ALL GAMES BY DATE")
print("-"*70)
cursor.execute("""
    SELECT DISTINCT
        event_id,
        home_team,
        away_team,
        commence_time,
        DATE(commence_time) as game_date
    FROM player_props
    ORDER BY commence_time
""")
games = cursor.fetchall()
print(f"Found {len(games)} unique games:\n")
for i, game in enumerate(games, 1):
    print(f"{i}. {game['away_team']} @ {game['home_team']}")
    print(f"   Time: {game['commence_time']}")
    print(f"   Date: {game['game_date']}")
    print()

# Test SQLite's date functions
print("\n5. SQLITE DATE TESTING")
print("-"*70)
cursor.execute("SELECT date('now') as today")
today = cursor.fetchone()['today']
print(f"SQLite thinks today is: {today}")

cursor.execute("SELECT date('now', '+1 day') as tomorrow")
tomorrow = cursor.fetchone()['tomorrow']
print(f"SQLite thinks tomorrow is: {tomorrow}")

# Python's date
print(f"Python thinks today is: {datetime.now().date()}")
print(f"Python thinks tomorrow is: {(datetime.now() + timedelta(days=1)).date()}")

# Test today's filter
print("\n6. TESTING 'TODAY' FILTER")
print("-"*70)
print(f"Query: date(commence_time) = date('now')")
cursor.execute("""
    SELECT DISTINCT
        event_id,
        home_team,
        away_team,
        commence_time,
        date(commence_time) as game_date
    FROM player_props
    WHERE date(commence_time) = date('now')
""")
today_games = cursor.fetchall()
print(f"Found {len(today_games)} games for today:")
for game in today_games:
    print(f"  - {game['away_team']} @ {game['home_team']} ({game['game_date']})")

# Test tomorrow's filter
print("\n7. TESTING 'TOMORROW' FILTER")
print("-"*70)
print(f"Query: date(commence_time) = date('now', '+1 day')")
cursor.execute("""
    SELECT DISTINCT
        event_id,
        home_team,
        away_team,
        commence_time,
        date(commence_time) as game_date
    FROM player_props
    WHERE date(commence_time) = date('now', '+1 day')
""")
tomorrow_games = cursor.fetchall()
print(f"Found {len(tomorrow_games)} games for tomorrow:")
for game in tomorrow_games:
    print(f"  - {game['away_team']} @ {game['home_team']} ({game['game_date']})")

# Test week filter
print("\n8. TESTING 'WEEK' FILTER")
print("-"*70)
print(f"Query: date(commence_time) BETWEEN date('now') AND date('now', '+7 days')")
cursor.execute("""
    SELECT DISTINCT
        event_id,
        home_team,
        away_team,
        commence_time,
        date(commence_time) as game_date
    FROM player_props
    WHERE date(commence_time) BETWEEN date('now') AND date('now', '+7 days')
""")
week_games = cursor.fetchall()
print(f"Found {len(week_games)} games this week:")
for game in week_games:
    print(f"  - {game['away_team']} @ {game['home_team']} ({game['game_date']})")

# Test the exact dashboard query
print("\n9. TESTING EXACT DASHBOARD QUERY")
print("-"*70)
sport = 'basketball_nba'
date_condition = "date(commence_time) = date('now')"

query = f"""
    SELECT DISTINCT 
        event_id,
        sport_key,
        home_team,
        away_team,
        commence_time,
        COUNT(DISTINCT player_name) as player_count,
        COUNT(DISTINCT bookmaker_key) as bookmaker_count
    FROM player_props
    WHERE {date_condition}
    AND sport_key = ?
    GROUP BY event_id, sport_key, home_team, away_team, commence_time
    ORDER BY commence_time ASC
"""

print(f"Sport filter: {sport}")
print(f"Date condition: {date_condition}")
print()

cursor.execute(query, (sport,))
dashboard_games = cursor.fetchall()
print(f"Dashboard query returned {len(dashboard_games)} games:")
for game in dashboard_games:
    print(f"  - {game['away_team']} @ {game['home_team']}")
    print(f"    Players: {game['player_count']}, Bookmakers: {game['bookmaker_count']}")

# Check if games are in the past
print("\n10. CHECKING IF GAMES ARE IN THE PAST")
print("-"*70)
cursor.execute("""
    SELECT 
        event_id,
        home_team,
        away_team,
        commence_time,
        CASE 
            WHEN commence_time < datetime('now') THEN 'PAST'
            ELSE 'FUTURE'
        END as status
    FROM player_props
    GROUP BY event_id, home_team, away_team, commence_time
    ORDER BY commence_time
""")
for game in cursor.fetchall():
    print(f"{game['status']}: {game['away_team']} @ {game['home_team']}")
    print(f"  Time: {game['commence_time']}")

# Check current datetime
print("\n11. CURRENT DATETIME COMPARISON")
print("-"*70)
cursor.execute("SELECT datetime('now') as now")
sqlite_now = cursor.fetchone()['now']
print(f"SQLite now: {sqlite_now}")
print(f"Python now: {datetime.utcnow().isoformat()}")
print(f"Python local: {datetime.now().isoformat()}")

conn.close()

print("\n" + "="*70)
print("DIAGNOSIS COMPLETE")
print("="*70)
print("\nIf games show as PAST but should be FUTURE:")
print("  - The database has old data")
print("  - Re-run: python enhanced_scraper_v2.py basketball_nba")
print("\nIf date filters return 0 games:")
print("  - Check the game_date values vs SQLite's date('now')")
print("  - Timezone mismatch between data and SQLite")
print("="*70)