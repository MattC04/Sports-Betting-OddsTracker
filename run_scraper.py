"""
Main script to run the Odds API scraper.
Reads API key from .env file or environment variable.
"""

import os
import sys
from dotenv import load_dotenv
from scripts.odds_api_scraper import scrape_odds_data, list_available_sports
from scripts.player_props_scraper import scrape_player_props

def get_api_key():
    """Get API key from .env file or environment variable."""
    # Load .env file if it exists
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        # Try to load from current directory
        load_dotenv()
    
    # Get API key from environment variable (loaded from .env or system)
    api_key = os.getenv('ODDS_API_KEY')
    
    # Check if it's still the placeholder
    if api_key and api_key == 'your_api_key_here':
        return None
    
    return api_key

def main():
    """Main function to run the Odds API scraper."""
    
    api_key = get_api_key()
    
    if not api_key:
        print("⚠️  API key not found!")
        print("\n📝 To set your API key:")
        print("\n1. Copy .env.example to .env:")
        print("   copy .env.example .env")
        print("\n2. Edit .env file and replace 'your_api_key_here' with your actual API key")
        print("   Get your API key from: https://the-odds-api.com/")
        print("\nAlternatively, set environment variable:")
        print("   Windows PowerShell: $env:ODDS_API_KEY='your_api_key'")
        print("   Windows CMD: set ODDS_API_KEY=your_api_key")
        print("\nFetching available sports (no API key required)...")
        try:
            list_available_sports()
        except Exception as e:
            print(f"Error: {e}")
        return
    
    print("="*60)
    print("Odds API Scraper")
    print("="*60)
    print(f"API Key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else '****'}")
    print()
    
    # List available sports
    print("📋 Fetching available sports...")
    try:
        sports_df = list_available_sports(api_key)
        print(f"\n✅ Found {len(sports_df)} sports")
    except Exception as e:
        print(f"❌ Error fetching sports: {e}")
        return
    
    # Common sport mappings
    sport_options = {
        'nba': 'basketball_nba',
        'nfl': 'americanfootball_nfl',
        'mlb': 'baseball_mlb',
        'nhl': 'icehockey_nhl',
        'ncaab': 'basketball_ncaab',
        'ncaaf': 'americanfootball_ncaaf',
        'soccer': 'soccer_epl',
    }
    
    # Default to NBA
    sport_key = 'basketball_nba'
    
    # Check if player props mode is requested
    scrape_player_props_mode = '--player-props' in sys.argv or '-pp' in sys.argv
    
    # Check if sport is provided as command line argument
    if len(sys.argv) > 1:
        args = [arg for arg in sys.argv[1:] if not arg.startswith('--')]
        if args:
            sport_arg = args[0].lower()
            sport_key = sport_options.get(sport_arg, sport_arg)
            print(f"\n🎯 Using sport: {sport_key} (from argument: {sport_arg})")
        else:
            print(f"\n🎯 Using default sport: {sport_key}")
    else:
        print(f"\n🎯 Using default sport: {sport_key}")
        print("💡 Tip: Pass a sport as argument, e.g., 'python run_scraper.py nfl'")
        print("   Available shortcuts: nba, nfl, mlb, nhl, ncaab, ncaaf, soccer")
        print("   For player props: 'python run_scraper.py nba --player-props'")
    
    # Scrape odds data
    print("\n" + "="*60)
    if scrape_player_props_mode:
        print(f"Scraping PLAYER PROPS for: {sport_key}")
        print("="*60)
        
        try:
            props = scrape_player_props(
                api_key=api_key,
                sport=sport_key,
                regions="us",
                odds_format="decimal"
            )
            
            if props:
                print(f"\n✅ Successfully scraped {len(props)} player props")
                print(f"📊 Data saved to database: data/player_props.db")
                print(f"\n💡 Run the dashboard with: python dashboard.py")
            else:
                print("\n⚠️  No player props found.")
                print("\n📋 IMPORTANT: The Odds API v4 does NOT support player_props market.")
                print("   Available markets: h2h, spreads, totals, outrights")
                print("\n💡 Alternative solutions:")
                print("   1. Use PrizePicks scraper for player props")
                print("   2. Use sportsbook APIs directly (DraftKings, FanDuel)")
                print("   3. See PLAYER_PROPS_NOTE.md for more details")
                print("\n💻 The dashboard is ready - just needs a player props data source!")
        except ValueError as e:
            print(f"\n❌ Configuration Error: {e}")
        except Exception as e:
            print(f"\n❌ Error during scraping: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"Scraping odds for: {sport_key}")
        print("="*60)
        
        try:
            output_file = f"data/{sport_key}_odds.csv"
            
            df = scrape_odds_data(
                api_key=api_key,
                sport=sport_key,
                regions="us",
                markets="h2h,spreads",
                odds_format="decimal",
                output_file=output_file,
                save_raw="data/raw_odds_data.json" if os.getenv('SAVE_RAW', 'false').lower() == 'true' else None
            )
        
            if not df.empty:
                print(f"\n📊 Summary:")
                print(f"   Total records: {len(df)}")
                print(f"   Unique events: {df['event_id'].nunique()}")
                print(f"   Bookmakers: {df['bookmaker_title'].nunique()}")
                print(f"   Markets: {', '.join(df['market'].unique())}")
                print(f"\n✅ Scraping completed successfully!")
            else:
                print("\n⚠️  No data was scraped. This might mean:")
                print("   - No events are currently available for this sport")
                print("   - The sport key might be incorrect")
                print("   - Check the available sports list above")
        except ValueError as e:
            print(f"\n❌ Configuration Error: {e}")
        except Exception as e:
            print(f"\n❌ Error during scraping: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()

