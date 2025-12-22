"""
STEP-BY-STEP SETUP AND RUN SCRIPT
Run this to set up everything automatically
"""

import os
import sys
import subprocess

def print_step(step_num, message):
    print("\n" + "="*80)
    print(f"STEP {step_num}: {message}")
    print("="*80)

def check_python():
    print_step(1, "Checking Python Installation")
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("ERROR: Python 3.8 or higher required")
        return False
    print("SUCCESS: Python version is compatible")
    return True

def check_api_key():
    print_step(2, "Checking API Key")
    api_key = os.getenv('ODDS_API_KEY')
    if not api_key:
        print("ERROR: ODDS_API_KEY not set")
        print("\nPlease run ONE of these commands first:")
        print("\nLinux/Mac:")
        print("  export ODDS_API_KEY='your_api_key_here'")
        print("\nWindows Command Prompt:")
        print("  set ODDS_API_KEY=your_api_key_here")
        print("\nWindows PowerShell:")
        print("  $env:ODDS_API_KEY='your_api_key_here'")
        print("\nGet your API key from: https://the-odds-api.com/")
        return False
    print(f"SUCCESS: API key found ({api_key[:10]}...)")
    return True

def install_packages():
    print_step(3, "Installing Required Packages")
    packages = ['Flask', 'flask-cors', 'requests', 'pandas']
    
    for package in packages:
        try:
            __import__(package.lower().replace('-', '_'))
            print(f"  {package}: Already installed")
        except ImportError:
            print(f"  {package}: Installing...")
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package, '-q'])
                print(f"  {package}: Installed successfully")
            except:
                print(f"  {package}: Failed to install")
                return False
    
    print("SUCCESS: All packages installed")
    return True

def check_files():
    print_step(4, "Checking Required Files")
    required_files = [
        'odds_api_scraper.py',
        'player_props_scraper.py', 
        'dashboard.py',
        'dashboard.html'
    ]
    
    missing = []
    for file in required_files:
        if os.path.exists(file):
            print(f"  {file}: Found")
        else:
            print(f"  {file}: MISSING")
            missing.append(file)
    
    if missing:
        print(f"\nERROR: Missing files: {', '.join(missing)}")
        print("Make sure all files are in the same directory")
        return False
    
    print("SUCCESS: All required files present")
    return True

def create_data_directory():
    print_step(5, "Creating Data Directory")
    if not os.path.exists('data'):
        os.makedirs('data')
        print("Created 'data' directory")
    else:
        print("'data' directory already exists")
    return True

def test_api_connection():
    print_step(6, "Testing API Connection")
    try:
        import requests
        api_key = os.getenv('ODDS_API_KEY')
        
        response = requests.get(
            "https://api.the-odds-api.com/v4/sports",
            params={'apiKey': api_key},
            timeout=10
        )
        
        if response.status_code == 200:
            sports = response.json()
            print(f"SUCCESS: Connected to API")
            print(f"Available sports: {len(sports)}")
            return True
        else:
            print(f"ERROR: API returned status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def run_scraper():
    print_step(7, "Running Scraper to Fetch Data")
    print("\nFetching NBA player props...")
    print("This may take 30-60 seconds...\n")
    
    try:
        # Import and run the scraper
        import requests
        import sqlite3
        from datetime import datetime
        
        api_key = os.getenv('ODDS_API_KEY')
        
        # Simple inline scraper
        print("Fetching events...")
        response = requests.get(
            "https://api.the-odds-api.com/v4/sports/basketball_nba/events",
            params={'apiKey': api_key}
        )
        
        if response.status_code != 200:
            print(f"ERROR: Could not fetch events - Status {response.status_code}")
            return False
        
        events = response.json()
        print(f"Found {len(events)} events")
        
        if not events:
            print("\nNo NBA games scheduled today.")
            print("Try a different sport or check back later.")
            return False
        
        # Filter to today's events
        today = datetime.now().date()
        today_events = []
        for event in events:
            try:
                commence = datetime.fromisoformat(event['commence_time'].replace('Z', '+00:00'))
                if commence.date() == today:
                    today_events.append(event)
            except:
                continue
        
        print(f"Today's events: {len(today_events)}")
        
        if not today_events:
            print("\nNo games today. Database will be empty.")
            print("Try again on a game day.")
            return False
        
        # Fetch player props for first event
        print(f"\nFetching player props for event: {today_events[0]['home_team']} vs {today_events[0]['away_team']}")
        
        event_id = today_events[0]['id']
        response = requests.get(
            f"https://api.the-odds-api.com/v4/sports/basketball_nba/events/{event_id}/odds",
            params={
                'apiKey': api_key,
                'regions': 'us',
                'markets': 'player_points,player_assists,player_rebounds'
            }
        )
        
        if response.status_code != 200:
            print(f"WARNING: Could not fetch player props")
            print(f"This may mean player props aren't available yet")
            print(f"Props usually appear 2-4 hours before game time")
            return False
        
        event_data = response.json()
        
        # Save to database
        print("\nSaving to database...")
        conn = sqlite3.connect('data/player_props.db')
        cursor = conn.cursor()
        
        # Create table
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
                scraped_at TEXT
            )
        """)
        
        # Insert data
        count = 0
        if 'bookmakers' in event_data:
            for bookmaker in event_data['bookmakers']:
                for market in bookmaker.get('markets', []):
                    for outcome in market.get('outcomes', []):
                        cursor.execute("""
                            INSERT INTO player_props VALUES (
                                NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                            )
                        """, (
                            event_data['id'],
                            event_data['sport_key'],
                            event_data['sport_title'],
                            event_data['home_team'],
                            event_data['away_team'],
                            event_data['commence_time'],
                            outcome.get('description', ''),
                            market['key'],
                            outcome.get('name', ''),
                            outcome.get('price'),
                            outcome.get('point'),
                            bookmaker['key'],
                            bookmaker['title'],
                            datetime.now().isoformat()
                        ))
                        count += 1
        
        conn.commit()
        conn.close()
        
        print(f"SUCCESS: Saved {count} player props to database")
        return True
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def start_dashboard():
    print_step(8, "Starting Dashboard")
    print("\nDashboard will start on http://localhost:5000")
    print("Press Ctrl+C to stop the dashboard\n")
    print("Once started, open your browser to: http://localhost:5000")
    print("\nStarting in 3 seconds...")
    
    import time
    time.sleep(3)
    
    try:
        subprocess.run([sys.executable, 'dashboard.py'])
    except KeyboardInterrupt:
        print("\n\nDashboard stopped")

def main():
    print("\n" + "="*80)
    print("SPORTS BETTING ANALYTICS - AUTOMATED SETUP")
    print("="*80)
    
    steps = [
        ("Checking Python", check_python),
        ("Checking API Key", check_api_key),
        ("Installing Packages", install_packages),
        ("Checking Files", check_files),
        ("Creating Directories", create_data_directory),
        ("Testing API Connection", test_api_connection),
        ("Running Scraper", run_scraper),
    ]
    
    for i, (name, func) in enumerate(steps, 1):
        if not func():
            print(f"\n{'='*80}")
            print(f"SETUP FAILED AT STEP {i}: {name}")
            print(f"{'='*80}")
            print("\nPlease fix the error above and run this script again")
            sys.exit(1)
    
    print("\n" + "="*80)
    print("SETUP COMPLETE!")
    print("="*80)
    
    response = input("\nDo you want to start the dashboard now? (y/n): ")
    if response.lower() == 'y':
        start_dashboard()
    else:
        print("\nTo start the dashboard later, run:")
        print("  python dashboard.py")
        print("\nThen open your browser to: http://localhost:5000")

if __name__ == "__main__":
    main()
