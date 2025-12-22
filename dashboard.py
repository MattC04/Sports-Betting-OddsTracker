"""
Enhanced Flask API backend for the Sports Betting Analytics Dashboard.
Provides comprehensive endpoints for player props, game data, and analytics.
"""

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

app = Flask(__name__, static_folder='.')
CORS(app)  # Enable CORS for frontend development

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.getenv('PLAYER_PROPS_DB', os.path.join(BASE_DIR, 'data', 'player_props.db'))


def get_db_connection():
    """Get database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def format_game_time(commence_time):
    """Format game commence time for display."""
    try:
        dt = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
        return dt.strftime('%I:%M %p')
    except:
        return commence_time


@app.route('/')
def index():
    """Serve the main dashboard HTML."""
    return send_from_directory(BASE_DIR, 'dashboard.html')


@app.route('/api/sports')
def get_sports():
    """Get list of available sports from the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT sport_key, sport_title, COUNT(DISTINCT event_id) as game_count
            FROM player_props
            WHERE date(commence_time) >= date('now')
            GROUP BY sport_key, sport_title
            ORDER BY sport_key
        """)
        rows = cursor.fetchall()
        conn.close()
        
        sports = [{
            'key': row['sport_key'], 
            'title': row['sport_title'],
            'game_count': row['game_count']
        } for row in rows]
        
        return jsonify({'sports': sports, 'success': True})
    except Exception as e:
        logger.error(f"Error fetching sports: {e}")
        return jsonify({'sports': [], 'error': str(e), 'success': False}), 500


@app.route('/api/games')
def get_games():
    """Get games for today or upcoming, organized by sport."""
    sport = request.args.get('sport', 'basketball_nba')
    date_filter = request.args.get('date', 'today')  # today, tomorrow, week
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build date filter
        if date_filter == 'today':
            date_condition = "date(commence_time) = date('now')"
        elif date_filter == 'tomorrow':
            date_condition = "date(commence_time) = date('now', '+1 day')"
        elif date_filter == 'week':
            date_condition = "date(commence_time) BETWEEN date('now') AND date('now', '+7 days')"
        else:
            date_condition = "date(commence_time) >= date('now')"
        
        query = f"""
            SELECT DISTINCT 
                event_id,
                sport_key,
                sport_title,
                home_team,
                away_team,
                commence_time,
                MIN(scraped_at) as first_scraped,
                COUNT(DISTINCT player_name) as player_count,
                COUNT(DISTINCT bookmaker_key) as bookmaker_count
            FROM player_props
            WHERE {date_condition}
            AND sport_key = ?
            GROUP BY event_id, sport_key, sport_title, home_team, away_team, commence_time
            ORDER BY commence_time ASC
        """
        
        cursor.execute(query, (sport,))
        rows = cursor.fetchall()
        conn.close()
        
        games = []
        for row in rows:
            games.append({
                'event_id': row['event_id'],
                'sport_key': row['sport_key'],
                'sport_title': row['sport_title'],
                'home_team': row['home_team'],
                'away_team': row['away_team'],
                'commence_time': row['commence_time'],
                'commence_time_formatted': format_game_time(row['commence_time']),
                'first_scraped': row['first_scraped'],
                'player_count': row['player_count'],
                'bookmaker_count': row['bookmaker_count']
            })
        
        return jsonify({
            'games': games, 
            'count': len(games),
            'sport': sport,
            'date_filter': date_filter,
            'success': True
        })
    except Exception as e:
        logger.error(f"Error fetching games: {e}")
        return jsonify({'games': [], 'error': str(e), 'success': False}), 500


@app.route('/api/game/<event_id>')
def get_game_details(event_id):
    """Get detailed information for a specific game including all player props."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get game info
        cursor.execute("""
            SELECT DISTINCT 
                event_id,
                sport_key,
                sport_title,
                home_team,
                away_team,
                commence_time
            FROM player_props
            WHERE event_id = ?
            LIMIT 1
        """, (event_id,))
        
        game_row = cursor.fetchone()
        if not game_row:
            conn.close()
            return jsonify({'error': 'Game not found', 'success': False}), 404
        
        # Get all props for this game
        cursor.execute("""
            SELECT * FROM player_props
            WHERE event_id = ?
            ORDER BY player_name, prop_type, bookmaker_title, outcome_name
        """, (event_id,))
        
        props_rows = cursor.fetchall()
        props = [dict(row) for row in props_rows]
        
        # Organize props by player
        players = {}
        for prop in props:
            player = prop.get('player_name', 'Unknown')
            if player not in players:
                players[player] = {
                    'name': player,
                    'props': []
                }
            players[player]['props'].append(prop)
        
        # Get unique bookmakers and prop types
        bookmakers = set(prop.get('bookmaker_title') for prop in props if prop.get('bookmaker_title'))
        prop_types = set(prop.get('prop_type') for prop in props if prop.get('prop_type'))
        
        conn.close()
        
        return jsonify({
            'game': dict(game_row),
            'players': list(players.values()),
            'bookmakers': sorted(list(bookmakers)),
            'prop_types': sorted(list(prop_types)),
            'total_props': len(props),
            'player_count': len(players),
            'success': True
        })
    except Exception as e:
        logger.error(f"Error fetching game details: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/game/<event_id>/player/<player_name>')
def get_player_props(event_id, player_name):
    """Get all props for a specific player in a game, organized by prop type and bookmaker."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM player_props
            WHERE event_id = ? AND player_name = ?
            ORDER BY prop_type, bookmaker_title, outcome_name
        """, (event_id, player_name))
        
        props_rows = cursor.fetchall()
        
        if not props_rows:
            conn.close()
            return jsonify({'error': 'Player not found in this game', 'success': False}), 404
        
        # Organize by prop type
        props_by_type = {}
        for row in props_rows:
            prop = dict(row)
            prop_type = prop.get('prop_type', 'Unknown')
            
            if prop_type not in props_by_type:
                props_by_type[prop_type] = {
                    'prop_type': prop_type,
                    'lines': []
                }
            
            # Group by line value
            line_value = prop.get('outcome_point')
            if line_value:
                # Find or create line entry
                line_entry = None
                for line in props_by_type[prop_type]['lines']:
                    if line['value'] == line_value:
                        line_entry = line
                        break
                
                if not line_entry:
                    line_entry = {
                        'value': line_value,
                        'bookmakers': {}
                    }
                    props_by_type[prop_type]['lines'].append(line_entry)
                
                # Add bookmaker odds
                bookmaker = prop.get('bookmaker_title')
                if bookmaker not in line_entry['bookmakers']:
                    line_entry['bookmakers'][bookmaker] = {}
                
                outcome_name = prop.get('outcome_name', 'Unknown')
                line_entry['bookmakers'][bookmaker][outcome_name] = {
                    'price': prop.get('outcome_price'),
                    'last_update': prop.get('last_update')
                }
        
        conn.close()
        
        return jsonify({
            'player_name': player_name,
            'event_id': event_id,
            'props': list(props_by_type.values()),
            'success': True
        })
    except Exception as e:
        logger.error(f"Error fetching player props: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/player/<player_name>/history')
def get_player_history(player_name):
    """Get historical prop data for a player across all games."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                event_id,
                home_team,
                away_team,
                commence_time,
                prop_type,
                outcome_point as line_value,
                COUNT(DISTINCT bookmaker_key) as bookmaker_count,
                AVG(CASE WHEN outcome_name = 'Over' THEN outcome_price END) as avg_over_price,
                AVG(CASE WHEN outcome_name = 'Under' THEN outcome_price END) as avg_under_price
            FROM player_props
            WHERE player_name = ?
            GROUP BY event_id, home_team, away_team, commence_time, prop_type, outcome_point
            ORDER BY commence_time DESC
            LIMIT 20
        """, (player_name,))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = [{
            'event_id': row['event_id'],
            'matchup': f"{row['away_team']} @ {row['home_team']}",
            'commence_time': row['commence_time'],
            'prop_type': row['prop_type'],
            'line_value': row['line_value'],
            'bookmaker_count': row['bookmaker_count'],
            'avg_over_price': row['avg_over_price'],
            'avg_under_price': row['avg_under_price']
        } for row in rows]
        
        return jsonify({
            'player_name': player_name,
            'history': history,
            'count': len(history),
            'success': True
        })
    except Exception as e:
        logger.error(f"Error fetching player history: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/stats')
def get_stats():
    """Get dashboard statistics."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Total props
        cursor.execute("SELECT COUNT(*) as total FROM player_props")
        stats['total_props'] = cursor.fetchone()['total']
        
        # Unique players
        cursor.execute("SELECT COUNT(DISTINCT player_name) as unique_players FROM player_props")
        stats['unique_players'] = cursor.fetchone()['unique_players']
        
        # Total games
        cursor.execute("SELECT COUNT(DISTINCT event_id) as total_games FROM player_props")
        stats['total_games'] = cursor.fetchone()['total_games']
        
        # Today's games
        cursor.execute("""
            SELECT COUNT(DISTINCT event_id) as today_games 
            FROM player_props 
            WHERE date(commence_time) = date('now')
        """)
        stats['today_games'] = cursor.fetchone()['today_games']
        
        # Unique bookmakers
        cursor.execute("SELECT COUNT(DISTINCT bookmaker_key) as unique_bookmakers FROM player_props")
        stats['unique_bookmakers'] = cursor.fetchone()['unique_bookmakers']
        
        # Last update
        cursor.execute("SELECT MAX(scraped_at) as last_update FROM player_props")
        stats['last_update'] = cursor.fetchone()['last_update']
        
        conn.close()
        return jsonify({**stats, 'success': True})
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return jsonify({
            'total_props': 0, 
            'unique_players': 0, 
            'total_games': 0, 
            'today_games': 0,
            'unique_bookmakers': 0,
            'last_update': None,
            'error': str(e),
            'success': False
        })


@app.route('/api/search')
def search():
    """Search for players, teams, or games."""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'all')  # all, player, team, game
    
    if not query or len(query) < 2:
        return jsonify({'results': [], 'success': False, 'error': 'Query too short'})
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        results = {'players': [], 'teams': [], 'games': []}
        
        # Search players
        if search_type in ['all', 'player']:
            cursor.execute("""
                SELECT DISTINCT player_name, COUNT(DISTINCT event_id) as game_count
                FROM player_props
                WHERE player_name LIKE ?
                GROUP BY player_name
                ORDER BY game_count DESC
                LIMIT 10
            """, (f'%{query}%',))
            results['players'] = [{'name': row['player_name'], 'game_count': row['game_count']} 
                                 for row in cursor.fetchall()]
        
        # Search teams
        if search_type in ['all', 'team']:
            cursor.execute("""
                SELECT DISTINCT home_team as team, COUNT(DISTINCT event_id) as game_count
                FROM player_props
                WHERE home_team LIKE ? OR away_team LIKE ?
                GROUP BY team
                ORDER BY game_count DESC
                LIMIT 10
            """, (f'%{query}%', f'%{query}%'))
            results['teams'] = [{'name': row['team'], 'game_count': row['game_count']} 
                               for row in cursor.fetchall()]
        
        # Search games
        if search_type in ['all', 'game']:
            cursor.execute("""
                SELECT DISTINCT 
                    event_id,
                    home_team || ' vs ' || away_team as matchup,
                    commence_time
                FROM player_props
                WHERE home_team LIKE ? OR away_team LIKE ?
                ORDER BY commence_time DESC
                LIMIT 10
            """, (f'%{query}%', f'%{query}%'))
            results['games'] = [{'event_id': row['event_id'], 
                                'matchup': row['matchup'],
                                'commence_time': row['commence_time']} 
                               for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({'results': results, 'query': query, 'success': True})
    except Exception as e:
        logger.error(f"Error searching: {e}")
        return jsonify({'results': {}, 'error': str(e), 'success': False}), 500


@app.route('/api/compare')
def compare_lines():
    """Compare lines across different bookmakers for a specific prop."""
    event_id = request.args.get('event_id')
    player_name = request.args.get('player')
    prop_type = request.args.get('prop_type')
    
    if not all([event_id, player_name, prop_type]):
        return jsonify({'error': 'Missing required parameters', 'success': False}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                bookmaker_title,
                outcome_name,
                outcome_point,
                outcome_price,
                last_update
            FROM player_props
            WHERE event_id = ? AND player_name = ? AND prop_type = ?
            ORDER BY bookmaker_title, outcome_name
        """, (event_id, player_name, prop_type))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return jsonify({'error': 'No data found', 'success': False}), 404
        
        # Organize by bookmaker
        comparison = {}
        for row in rows:
            bookmaker = row['bookmaker_title']
            if bookmaker not in comparison:
                comparison[bookmaker] = {
                    'bookmaker': bookmaker,
                    'lines': {}
                }
            
            line = row['outcome_point']
            outcome = row['outcome_name']
            price = row['outcome_price']
            
            if line not in comparison[bookmaker]['lines']:
                comparison[bookmaker]['lines'][line] = {}
            
            comparison[bookmaker]['lines'][line][outcome] = price
        
        return jsonify({
            'comparison': list(comparison.values()),
            'player': player_name,
            'prop_type': prop_type,
            'event_id': event_id,
            'success': True
        })
    except Exception as e:
        logger.error(f"Error comparing lines: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        logger.warning(f"Database not found at {DB_PATH}.")
        logger.info("Run the scraper first to populate data: python player_props_scraper.py")
    
    logger.info("Starting Sports Betting Analytics Dashboard")
    logger.info("Dashboard: http://localhost:5000/")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
