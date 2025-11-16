# Sports-Betting-Bankroll-Manager

A comprehensive sports betting bankroll management system with odds data collection from the Odds API.

## Features

- **Odds API Integration**: Fetch real-time sports betting odds from multiple bookmakers
- **Multiple Sports Support**: NBA, NFL, MLB, NHL, NCAA, Soccer, and more
- **Multiple Markets**: Head-to-head, spreads, totals, and more
- **Flexible Data Export**: CSV format with structured odds data
- **Robust Error Handling**: Retry logic and comprehensive error messages
- **Easy Configuration**: Environment variable support for API key

## Quick Start

### 1. Get Your Odds API Key

1. Sign up at [The Odds API](https://the-odds-api.com/)
2. Get your free API key from the dashboard (emailed to you when you sign up)
3. Free tier includes usage credits (cost = markets × regions per request)

### 2. Set Your API Key

**Windows PowerShell:**
```powershell
$env:ODDS_API_KEY='your_api_key_here'
```

**Windows CMD:**
```cmd
set ODDS_API_KEY=your_api_key_here
```

**Linux/Mac:**
```bash
export ODDS_API_KEY='your_api_key_here'
```

**Permanent (Windows):**
- Go to System Properties → Environment Variables
- Add `ODDS_API_KEY` as a new user variable

**Permanent (Linux/Mac):**
- Add to `~/.bashrc` or `~/.zshrc`:
```bash
export ODDS_API_KEY='your_api_key_here'
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Scraper

#### Basic Usage (Default: NBA)

```bash
python test_simple_scraper.py
```

#### Scrape Specific Sports

```bash
# NFL
python test_simple_scraper.py nfl

# MLB
python test_simple_scraper.py mlb

# NHL
python test_simple_scraper.py nhl

# NCAA Basketball
python test_simple_scraper.py ncaab

# NCAA Football
python test_simple_scraper.py ncaaf

# Soccer (EPL)
python test_simple_scraper.py soccer
```

#### Using the Module Directly

```python
from scripts.odds_api_scraper import scrape_odds_data, list_available_sports
import os

api_key = os.getenv('ODDS_API_KEY')

# List all available sports
sports = list_available_sports(api_key)

# Scrape NBA odds
df = scrape_odds_data(
    api_key=api_key,
    sport='basketball_nba',
    regions='us',
    markets='h2h,spreads,totals',
    output_file='data/nba_odds.csv'
)
```

## Available Sports

The Odds API supports many sports. Common sport keys include:

- `basketball_nba` - NBA
- `americanfootball_nfl` - NFL
- `baseball_mlb` - MLB
- `icehockey_nhl` - NHL
- `basketball_ncaab` - NCAA Basketball
- `americanfootball_ncaaf` - NCAA Football
- `soccer_epl` - English Premier League
- `soccer_usa_mls` - MLS
- And many more...

To see all available sports, run:
```python
from scripts.odds_api_scraper import list_available_sports
list_available_sports()
```

## Data Output

The scraper outputs CSV files with the following columns:

- `event_id`: Unique event identifier
- `sport`: Sport name
- `home_team`: Home team name
- `away_team`: Away team name
- `commence_time`: Event start time
- `bookmaker_key`: Bookmaker identifier
- `bookmaker_title`: Bookmaker name (e.g., "DraftKings", "FanDuel")
- `market`: Market type (h2h, spreads, totals)
- `outcome_name`: Outcome name (team name or over/under)
- `outcome_price`: Odds price (in specified format)
- `outcome_point`: Point spread or total (if applicable)
- `last_update`: When odds were last updated
- `scraped_at`: When data was scraped

## Configuration Options

### Environment Variables

- `ODDS_API_KEY`: Your Odds API key (required)
- `ODDS_API_SPORT`: Default sport key (default: `basketball_nba`)
- `ODDS_API_OUTPUT`: Output file path (default: `data/odds_data.csv`)
- `ODDS_API_REGIONS`: Comma-separated regions (default: `us`)
- `ODDS_API_MARKETS`: Comma-separated markets (default: `h2h,spreads`)
- `ODDS_API_ODDS_FORMAT`: Odds format - `american` or `decimal` (default: `decimal`)
- `SAVE_RAW`: Set to `true` to save raw JSON response (default: `false`)

### Markets

Available markets:
- `h2h` - Head-to-head (moneyline)
- `spreads` - Point spreads (handicaps)
- `totals` - Over/under totals
- `outrights` - Outright winners (for tournaments/futures)

**Usage Cost**: Each market × each region = usage credits
- Example: `h2h,spreads` (2 markets) × `us` (1 region) = 2 credits
- Example: `h2h,spreads,totals` (3 markets) × `us,uk` (2 regions) = 6 credits

### Regions

Available regions:
- `us` - United States
- `us2` - US alternate
- `uk` - United Kingdom
- `au` - Australia
- And more...

### Odds Formats

- `decimal` - Decimal odds (e.g., 1.91, 2.50) - **Default**
- `american` - American odds (e.g., -110, +150)

## Example Output

```
✅ Successfully scraped 150 odds records
📊 Events found: 5
💾 Data saved to data/basketball_nba_odds.csv

Sample data:
event_id    sport         home_team          away_team          bookmaker_title  market   outcome_name  outcome_price
abc123      Basketball    Los Angeles Lakers Boston Celtics     DraftKings       h2h      Lakers        -110
abc123      Basketball    Los Angeles Lakers Boston Celtics     DraftKings       h2h      Celtics       +120
abc123      Basketball    Los Angeles Lakers Boston Celtics     DraftKings       spreads  Lakers        -110
...
```

## Troubleshooting

### API Key Issues

**Error: "Invalid API key"**
- Verify your API key is correct
- Check that the environment variable is set correctly
- Ensure there are no extra spaces or quotes

**Error: "Rate limit exceeded"**
- You've exceeded your monthly request limit
- Free tier: 500 requests/month
- Wait until next month or upgrade your plan

### No Data Returned

- Check that events are scheduled for the sport you're querying
- Verify the sport key is correct (use `list_available_sports()` to check)
- Some sports may not have active events at certain times

### Network Errors

- Check your internet connection
- The Odds API may be temporarily unavailable
- Try again after a few minutes

## API Usage Quota

The API uses a usage credit system. Each request costs:
- **Cost = [number of markets] × [number of regions]**

Examples:
- 1 market, 1 region = 1 credit
- 3 markets, 1 region = 3 credits  
- 1 market, 3 regions = 3 credits
- 3 markets, 3 regions = 9 credits

**Note**: The `/sports` and `/events` endpoints don't count against your quota.

Check your usage in the response headers (`x-requests-remaining`, `x-requests-used`) or at [The Odds API Dashboard](https://the-odds-api.com/)

## Legal Notice

This tool is for educational and research purposes only. Always comply with the Odds API terms of service and respect rate limits. Sports betting may be regulated in your jurisdiction - please check local laws.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational purposes. Please respect the Odds API terms of service when using this tool.

## Resources

- [The Odds API Documentation v4](https://docs.odds-api.com/)
- [The Odds API Dashboard](https://the-odds-api.com/)
- [API Reference](https://docs.odds-api.com/)
