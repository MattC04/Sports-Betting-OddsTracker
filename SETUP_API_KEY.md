# Setting Up Your API Key

## Quick Setup

1. **Create a `.env` file** in the project root directory:
   ```
   Sports-Betting-Bankroll-Manager/
   ├── .env          ← Create this file
   ├── .gitignore    ← Already created (ignores .env)
   └── ...
   ```

2. **Add your API key to `.env`**:
   ```env
   ODDS_API_KEY=your_actual_api_key_here
   ```
   
   Replace `your_actual_api_key_here` with your actual API key from https://the-odds-api.com/

3. **Install dependencies** (if you haven't already):
   ```powershell
   pip install -r requirements.txt
   ```

4. **Run the scraper**:
   ```powershell
   python run_scraper.py
   ```

## Example .env file

```env
# Odds API Configuration
ODDS_API_KEY=abc123xyz789your_actual_key_here

# Optional settings (can also be set in code)
# ODDS_API_SPORT=basketball_nba
# ODDS_API_REGIONS=us
# ODDS_API_MARKETS=h2h,spreads
# ODDS_API_ODDS_FORMAT=decimal
```

## Security Notes

- ✅ `.env` is already in `.gitignore` - your API key won't be committed to git
- ✅ Never share your `.env` file or commit it to version control
- ✅ The `.env` file stays on your local machine only

## Alternative: Environment Variable

If you prefer not to use a `.env` file, you can set the environment variable directly:

**Windows PowerShell:**
```powershell
$env:ODDS_API_KEY='your_api_key_here'
python run_scraper.py
```

**Windows (Permanent):**
1. Press `Win + R`, type `sysdm.cpl`, press Enter
2. Click "Environment Variables"
3. Under "User variables", click "New"
4. Variable name: `ODDS_API_KEY`
5. Variable value: `your_api_key_here`
6. Click OK, restart terminal

