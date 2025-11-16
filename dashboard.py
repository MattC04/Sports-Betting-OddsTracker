"""
Flask dashboard for displaying player props data.
Provides web interface for viewing scraped player props.
"""

from flask import Flask, render_template, jsonify, request
import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = os.getenv('PLAYER_PROPS_DB', 'data/player_props.db')


def get_db_connection():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('dashboard.html')


@app.route('/api/props')
def get_props():
    """API endpoint to get player props."""
    sport = request.args.get('sport', '')
    player = request.args.get('player', '')
    limit = int(request.args.get('limit', 100))
    hours = int(request.args.get('hours', 24))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT * FROM player_props 
        WHERE scraped_at >= datetime('now', '-{} hours')
    """.format(hours)
    
    params = []
    if sport:
        query += " AND sport_key = ?"
        params.append(sport)
    
    if player:
        query += " AND player_name LIKE ?"
        params.append(f"%{player}%")
    
    query += " ORDER BY scraped_at DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    props = [dict(row) for row in rows]
    return jsonify({'props': props, 'count': len(props)})


@app.route('/api/stats')
def get_stats():
    """API endpoint to get dashboard statistics."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    cursor.execute("SELECT COUNT(*) as total FROM player_props")
    stats['total_props'] = cursor.fetchone()['total']
    
    cursor.execute("""
        SELECT COUNT(DISTINCT player_name) as unique_players 
        FROM player_props
    """)
    stats['unique_players'] = cursor.fetchone()['unique_players']
    
    cursor.execute("""
        SELECT COUNT(DISTINCT sport_key) as sports 
        FROM player_props
    """)
    stats['sports'] = cursor.fetchone()['sports']
    
    cursor.execute("""
        SELECT COUNT(DISTINCT bookmaker_title) as bookmakers 
        FROM player_props
    """)
    stats['bookmakers'] = cursor.fetchone()['bookmakers']
    
    cursor.execute("""
        SELECT sport_key, COUNT(*) as count 
        FROM player_props 
        GROUP BY sport_key 
        ORDER BY count DESC
    """)
    stats['by_sport'] = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("""
        SELECT player_name, COUNT(*) as count 
        FROM player_props 
        GROUP BY player_name 
        ORDER BY count DESC 
        LIMIT 10
    """)
    stats['top_players'] = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return jsonify(stats)


@app.route('/api/players')
def get_players():
    """API endpoint to get list of players."""
    sport = request.args.get('sport', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT DISTINCT player_name FROM player_props WHERE player_name IS NOT NULL AND player_name != ''"
    params = []
    
    if sport:
        query += " AND sport_key = ?"
        params.append(sport)
    
    query += " ORDER BY player_name"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    players = [row['player_name'] for row in rows]
    return jsonify({'players': players})


@app.route('/api/sports')
def get_sports():
    """API endpoint to get list of sports."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT sport_key, sport_title FROM player_props ORDER BY sport_key")
    rows = cursor.fetchall()
    conn.close()
    
    sports = [{'key': row['sport_key'], 'title': row['sport_title']} for row in rows]
    return jsonify({'sports': sports})


if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        logger.warning(f"Database not found at {DB_PATH}. Please run the scraper first.")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

