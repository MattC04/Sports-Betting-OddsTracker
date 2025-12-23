"""
Complete Diagnostic - Check database, dashboard, and everything
"""

import os
import sqlite3
import sys

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

# Check 1: Find database files
print_section("STEP 1: Looking for database files")

db_files = []
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.db'):
            db_path = os.path.join(root, file)
            db_files.append(db_path)

if db_files:
    print(f"Found {len(db_files)} database file(s):")
    for i, db_file in enumerate(db_files, 1):
        size = os.path.getsize(db_file)
        print(f"  {i}. {db_file}")
        print(f"     Size: {size:,} bytes ({size/1024:.1f} KB)")
else:
    print("ERROR: No database files found!")
    print("\nYou need to run the scraper first:")
    print("  python enhanced_scraper_v2.py basketball_nba")
    sys.exit(1)

# Check 2: Inspect each database
print_section("STEP 2: Inspecting database contents")

for db_file in db_files:
    print(f"\n{db_file}:")
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"  Tables found: {len(tables)}")
        
        for table_name, in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"    - {table_name}: {count} rows")
            
            # Show sample data for player_props if exists
            if table_name == 'player_props' and count > 0:
                print(f"\n    Sample from player_props:")
                cursor.execute(f"SELECT event_id, player_name, prop_type, bookmaker_title, outcome_point FROM player_props LIMIT 3")
                for row in cursor.fetchall():
                    print(f"      Player: {row[1]}, {row[2]}, Line: {row[4]}, Bookmaker: {row[3]}")
        
        conn.close()
        
    except Exception as e:
        print(f"  ERROR reading database: {e}")

# Check 3: What database is dashboard.py looking for?
print_section("STEP 3: Checking dashboard.py configuration")

dashboard_file = 'dashboard.py'
if os.path.exists(dashboard_file):
    with open(dashboard_file, 'r') as f:
        content = f.read()
        
    # Look for database path
    if 'player_props.db' in content:
        print("Dashboard is looking for: data/player_props.db")
        expected_db = 'data/player_props.db'
    elif 'odds_data.db' in content:
        print("Dashboard is looking for: data/odds_data.db")
        expected_db = 'data/odds_data.db'
    elif 'enhanced_odds.db' in content:
        print("Dashboard is looking for: data/enhanced_odds.db")
        expected_db = 'data/enhanced_odds.db'
    else:
        print("Could not determine which database dashboard.py uses")
        expected_db = None
    
    if expected_db:
        if os.path.exists(expected_db):
            print(f"✓ Database exists at expected location")
        else:
            print(f"✗ Database NOT found at expected location: {expected_db}")
            print(f"\nAvailable databases:")
            for db in db_files:
                print(f"  - {db}")
else:
    print("ERROR: dashboard.py not found!")

# Check 4: Check if dashboard is running
print_section("STEP 4: Dashboard status")

print("To check if dashboard is running:")
print("  1. Look for this message in your terminal:")
print("     'Running on http://127.0.0.1:5000'")
print("  2. Open browser to: http://localhost:5000")
print("  3. Check browser console for errors (F12 -> Console tab)")

# Check 5: Test database query that dashboard uses
print_section("STEP 5: Testing dashboard queries")

if db_files:
    db_to_test = db_files[0]
    print(f"Testing queries on: {db_to_test}")
    
    try:
        conn = sqlite3.connect(db_to_test)
        cursor = conn.cursor()
        
        # Check if player_props table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='player_props'")
        if cursor.fetchone():
            # Test the query dashboard uses
            cursor.execute("""
                SELECT COUNT(DISTINCT event_id) as game_count,
                       COUNT(DISTINCT player_name) as player_count,
                       COUNT(*) as prop_count,
                       COUNT(DISTINCT bookmaker_title) as bookmaker_count
                FROM player_props
            """)
            
            result = cursor.fetchone()
            print(f"\nQuery results:")
            print(f"  Games: {result[0]}")
            print(f"  Players: {result[1]}")
            print(f"  Props: {result[2]}")
            print(f"  Bookmakers: {result[3]}")
            
            if result[0] == 0:
                print("\n✗ PROBLEM: No data in player_props table!")
                print("\nYou need to run the scraper:")
                print("  python enhanced_scraper_v2.py basketball_nba")
            else:
                print("\n✓ Data exists in database!")
                
                # Show what data we have
                print("\nAvailable games:")
                cursor.execute("""
                    SELECT DISTINCT home_team, away_team, commence_time
                    FROM player_props
                    LIMIT 5
                """)
                for row in cursor.fetchall():
                    print(f"  - {row[1]} @ {row[0]} ({row[2]})")
        else:
            print("\n✗ PROBLEM: player_props table doesn't exist!")
            print("\nRun the correct scraper:")
            print("  python enhanced_scraper_v2.py basketball_nba")
        
        conn.close()
        
    except Exception as e:
        print(f"\n✗ ERROR testing queries: {e}")

# Check 6: Browser console errors
print_section("STEP 6: Check browser console")

print("""
Open your browser and:
1. Go to http://localhost:5000
2. Press F12 to open Developer Tools
3. Click 'Console' tab
4. Look for errors (red text)

Common errors:
- "Failed to fetch" = Dashboard not running
- "404 Not Found" = API endpoint doesn't exist
- "500 Internal Server Error" = Database issue

If you see errors, copy them and share them.
""")

# Summary
print_section("SUMMARY & NEXT STEPS")

print("\nCurrent status:")
print(f"  Database files found: {len(db_files)}")

if db_files:
    total_props = 0
    for db_file in db_files:
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='player_props'")
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM player_props")
                count = cursor.fetchone()[0]
                total_props += count
            conn.close()
        except:
            pass
    
    print(f"  Total props in databases: {total_props}")
    
    if total_props == 0:
        print("\n✗ PROBLEM: No data in any database")
        print("\nSOLUTION:")
        print("  1. Run: python test_env.py  (check API key)")
        print("  2. Run: python enhanced_scraper_v2.py basketball_nba")
        print("  3. Run: python dashboard.py")
        print("  4. Open: http://localhost:5000")
    else:
        print("\n✓ Data exists!")
        print("\nIf dashboard shows no data:")
        print("  1. Check dashboard.py is looking at correct database")
        print("  2. Restart dashboard: Ctrl+C then 'python dashboard.py'")
        print("  3. Clear browser cache: Ctrl+Shift+R")
        print("  4. Check browser console for errors (F12)")

print("\n" + "="*70)