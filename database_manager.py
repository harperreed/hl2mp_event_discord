import sqlite3
import logging
from config import DB_FILE

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE)
        self.cursor = self.conn.cursor()
        self.init_db()

    def init_db(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS players
                               (steam_id TEXT PRIMARY KEY, player_name TEXT, last_seen TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS kills
                               (timestamp TEXT, attacker_steam_id TEXT, victim_steam_id TEXT, weapon TEXT,
                                attacker_health INTEGER, distance REAL, headshot BOOLEAN)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS map_changes
                               (timestamp TEXT, map_name TEXT)''')
        self.conn.commit()

    def update_player(self, steam_id, player_name, timestamp):
        self.cursor.execute('''INSERT OR REPLACE INTO players (steam_id, player_name, last_seen)
                               VALUES (?, ?, ?)''', (steam_id, player_name, timestamp))
        self.conn.commit()

    def record_kill(self, timestamp, attacker_steam_id, victim_steam_id, weapon, attacker_health, distance, headshot):
        self.cursor.execute('''INSERT INTO kills VALUES (?, ?, ?, ?, ?, ?, ?)''',
                            (timestamp, attacker_steam_id, victim_steam_id, weapon, attacker_health, distance, headshot))
        self.conn.commit()

    def record_map_change(self, timestamp, map_name):
        self.cursor.execute('''INSERT INTO map_changes VALUES (?, ?)''', (timestamp, map_name))
        self.conn.commit()

    def get_player_steam_id(self, player_name):
        self.cursor.execute("SELECT steam_id FROM players WHERE player_name = ?", (player_name,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def close(self):
        self.conn.close()