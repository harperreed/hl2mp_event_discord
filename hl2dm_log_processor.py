import sqlite3
import re
from datetime import datetime
from discord_webhook import DiscordWebhook, DiscordEmbed
from dotenv import load_dotenv
import os
import logging
import json
import random
import requests
import sys
import fcntl
import sys
import os

# Load environment variables
load_dotenv()

# Configuration from .env
LOG_FILE = os.getenv('LOG_FILE')
DB_FILE = os.getenv('DB_FILE')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
LAST_PROCESSED_FILE = 'last_processed.json'

# Set up logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler('hl2dm_log_processor.log'),
                        logging.StreamHandler(sys.stdout)
                    ])

# Regular expressions for parsing log entries
CONNECT_RE = re.compile(r'\[event_logger\.smx\] Player connected: (.+) \(Steam ID: (.+)\)')
DISCONNECT_RE = re.compile(r'\[event_logger\.smx\] Player disconnected: (.+)')
KILL_RE = re.compile(r'\[event_logger\.smx\] Kill: (.+) \((.+)\) killed (.+) \((.+)\) \| Weapon: (.+) \| Attacker Health: (\d+) \| Distance: ([\d.]+) \| Headshot: (.+)')
MAP_CHANGE_RE = re.compile(r'\[event_logger\.smx\] Map changed to: (.+)')

def init_db():
    logging.debug("Initializing database")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS players
                 (steam_id TEXT PRIMARY KEY, player_name TEXT, last_seen TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS kills
                 (timestamp TEXT, attacker_steam_id TEXT, victim_steam_id TEXT, weapon TEXT,
                  attacker_health INTEGER, distance REAL, headshot BOOLEAN)''')
    c.execute('''CREATE TABLE IF NOT EXISTS map_changes
                 (timestamp TEXT, map_name TEXT)''')
    conn.commit()
    logging.debug("Database initialized")
    return conn

def parse_timestamp(line):
    timestamp_match = re.match(r'L (\d{2}/\d{2}/\d{4} - \d{2}:\d{2}:\d{2}):', line)
    if timestamp_match:
        timestamp_str = timestamp_match.group(1)
        try:
            return datetime.strptime(timestamp_str, '%m/%d/%Y - %H:%M:%S')
        except ValueError:
            logging.error(f"Unable to parse timestamp: {timestamp_str}")
            return timestamp_str
    logging.error(f"No timestamp found in line: {line}")
    return None

def get_last_processed_timestamp():
    if os.path.exists(LAST_PROCESSED_FILE):
        try:
            with open(LAST_PROCESSED_FILE, 'r') as f:
                data = json.load(f)
                return datetime.strptime(data['last_processed'], '%m/%d/%Y - %H:%M:%S')
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logging.error(f"Error reading {LAST_PROCESSED_FILE}: {str(e)}")
    return datetime.min

def save_last_processed_timestamp(timestamp):
    try:
        formatted_timestamp = timestamp.strftime('%m/%d/%Y - %H:%M:%S')
        with open(LAST_PROCESSED_FILE, 'w') as f:
            json.dump({'last_processed': formatted_timestamp}, f)
        logging.info(f"Last processed timestamp saved: {formatted_timestamp}")
    except Exception as e:
        logging.error(f"Error saving last processed timestamp: {str(e)}")

def generate_kill_message(attacker, victim, weapon):
    if attacker == victim:
        return f"💀 {attacker} accidentally killed themselves"

    weapon_messages = {
        'crowbar': [f"{attacker} bashed {victim}'s skull in with a crowbar",
                    f"{attacker} showed {victim} the business end of a crowbar"],
        'crossbow_bolt': [f"{attacker} pinned {victim} to the wall with a crossbow bolt",
                          f"{attacker} made a pincushion out of {victim} with their crossbow"],
        'smg1': [f"{attacker} filled {victim} with lead using their SMG",
                 f"{attacker} turned {victim} into swiss cheese with SMG fire"],
        'ar2': [f"{attacker} vaporized {victim} with pulse rifle fire",
                f"{attacker} demonstrated superior marksmanship against {victim} with an AR2"],
        'shotgun': [f"{attacker} blasted {victim} to bits with a shotgun",
                    f"{attacker} introduced {victim} to a face full of buckshot"],
        'grenade': [f"{attacker} blew {victim} to smithereens",
                    f"{victim} was caught in {attacker}'s explosive surprise"],
        'rpg_missile': [f"{attacker} reduced {victim} to giblets with a well-placed rocket",
                        f"{victim} couldn't outrun {attacker}'s rocket"],
        'physics': [f"{victim} succumbed to the laws of physics, courtesy of {attacker}"],
        "physcannon": [f"{victim} ran into a hard place, courtesy of {attacker}"],
    }

    for weapon_type, messages in weapon_messages.items():
        if weapon_type in weapon.lower():
            return f"💀 {random.choice(messages)}"

    return f"💀 {attacker} eliminated {victim} with a {weapon}"

def send_discord_notification(content):
    logging.info(f"Attempting to send Discord notification: {content}")
    try:
        webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL, content=content)
        response = webhook.execute()
        if response.status_code == 200:
            logging.info("Discord notification sent successfully")
        else:
            logging.error(f"Failed to send Discord notification. Status code: {response.status_code}")
    except requests.RequestException as e:
        logging.error(f"Error sending Discord notification: {str(e)}")

def update_player(conn, steam_id, player_name, timestamp):
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO players (steam_id, player_name, last_seen)
                 VALUES (?, ?, ?)''', (steam_id, player_name, timestamp))
    conn.commit()

def process_log(conn):
    logging.info("Starting log processing")
    c = conn.cursor()
    last_processed = get_last_processed_timestamp()
    logging.info(f"Last processed timestamp: {last_processed}")

    with open(LOG_FILE, 'r') as f:
        for line_number, line in enumerate(f, 1):
            logging.debug(f"Processing line {line_number}: {line.strip()}")
            timestamp = parse_timestamp(line)

            if not timestamp or timestamp <= last_processed:
                continue

            timestamp_str = timestamp.strftime('%m/%d/%Y - %H:%M:%S')

            connect_match = CONNECT_RE.search(line)
            if connect_match:
                player_name, steam_id = connect_match.groups()
                update_player(conn, steam_id, player_name, timestamp_str)
                send_discord_notification(f"🟢 {player_name} joined the server")
                continue

            disconnect_match = DISCONNECT_RE.search(line)
            if disconnect_match:
                player_name = disconnect_match.group(1)
                c.execute("SELECT steam_id FROM players WHERE player_name = ?", (player_name,))
                result = c.fetchone()
                if result:
                    steam_id = result[0]
                    update_player(conn, steam_id, player_name, timestamp_str)
                send_discord_notification(f"🔴 {player_name} left the server")
                continue

            kill_match = KILL_RE.search(line)
            if kill_match:
                attacker_name, attacker_steam_id, victim_name, victim_steam_id, weapon, \
                attacker_health, distance, headshot = kill_match.groups()
                c.execute("INSERT INTO kills VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (timestamp_str, attacker_steam_id, victim_steam_id, weapon,
                           int(attacker_health), float(distance), headshot == 'Yes'))
                update_player(conn, attacker_steam_id, attacker_name, timestamp_str)
                update_player(conn, victim_steam_id, victim_name, timestamp_str)
                kill_message = generate_kill_message(attacker_name, victim_name, weapon)
                send_discord_notification(kill_message)
                continue

            map_change_match = MAP_CHANGE_RE.search(line)
            if map_change_match:
                map_name = map_change_match.group(1)
                c.execute("INSERT INTO map_changes VALUES (?, ?)", (timestamp_str, map_name))
                send_discord_notification(f"🗺️ Map changed to: {map_name}")
                continue

            logging.debug(f"Line {line_number} did not match any expected patterns")

        last_processed = timestamp

    conn.commit()
    save_last_processed_timestamp(last_processed)
    logging.info(f"Log processing completed. Last processed timestamp: {last_processed}")

def acquire_lock(lockfile):
    try:
        fd = open(lockfile, 'w')
        fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except IOError:
        return None

def release_lock(fd):
    fcntl.lockf(fd, fcntl.LOCK_UN)
    fd.close()

def main():
    logging.info("Script started")
    lock_file = '/tmp/hl2dm_log_processor.lock'
    lock = acquire_lock(lock_file)
    if not lock:
        logging.warning("Another instance is already running. Exiting.")
        sys.exit(0)

    try:
        conn = init_db()
        process_log(conn)
        conn.close()
        logging.info("Script completed successfully")
    except sqlite3.Error as e:
        logging.error(f"SQLite error occurred: {e}")
    except IOError as e:
        logging.error(f"I/O error occurred: {e}")
    except Exception as e:
        logging.exception("An unexpected error occurred during script execution")
    finally:
        release_lock(lock)
        os.unlink(lock_file)
        logging.info("Script execution finished")

if __name__ == "__main__":
    main()