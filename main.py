import json
import logging
import os
from datetime import datetime, timedelta
from config import LOG_FILE, LAST_PROCESSED_FILE
from log_parser import LogParser
from database_manager import DatabaseManager
from message_generator import MessageGenerator
from discord_notifier import DiscordNotifier
from openai_handler import OpenAIHandler

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler('hl2dm_log_processor.log'),
                        logging.StreamHandler()
                    ])

def get_last_processed_info():
    try:
        with open(LAST_PROCESSED_FILE, 'r') as f:
            data = json.load(f)
            return datetime.fromisoformat(data.get('last_processed_time', datetime.min.isoformat())), \
                   data.get('last_summary', '')
    except (FileNotFoundError, json.JSONDecodeError):
        return datetime.min, ''

def save_processed_info(processed_time, summary):
    with open(LAST_PROCESSED_FILE, 'w') as f:
        json.dump({
            'last_processed_time': processed_time.isoformat(),
            'last_summary': summary
        }, f)

def parse_log_timestamp(line):
    try:
        timestamp_str = line.split(': ', 1)[0][2:]  # Remove 'L ' prefix and split
        return datetime.strptime(timestamp_str, '%m/%d/%Y - %H:%M:%S')
    except (ValueError, IndexError):
        logging.warning(f"Failed to parse timestamp from line: {line}")
        return None

def main():
    logging.info("Script started")
    db_manager = DatabaseManager()
    ai = OpenAIHandler(os.environ.get("OPENAI_API_KEY"))
    last_processed_time, last_summary = get_last_processed_info()

    if not os.path.exists(LOG_FILE):
        logging.error(f"Log file {LOG_FILE} not found.")
        return

    new_events = []
    latest_timestamp = last_processed_time

    with open(LOG_FILE, 'r') as f:
        for line in f:
            line_timestamp = parse_log_timestamp(line)
            if line_timestamp is None:
                continue

            if line_timestamp > last_processed_time:
                event = LogParser.parse_line(line.strip())
                if event:
                    new_events.append(line.strip())
                    latest_timestamp = max(latest_timestamp, line_timestamp)

    if new_events:
        new_events_text = "\n".join(new_events)
        summary = ai.generate_summary(last_summary, new_events_text)
        DiscordNotifier.send_notification(summary)
        save_processed_info(latest_timestamp, summary)

        # Process events for database updates
        for event_line in new_events:
            event = LogParser.parse_line(event_line)
            if event['type'] == 'connect':
                db_manager.update_player(event['steam_id'], event['player_name'], event['timestamp'])
            elif event['type'] == 'disconnect':
                steam_id = db_manager.get_player_steam_id(event['player_name'])
                if steam_id:
                    db_manager.update_player(steam_id, event['player_name'], event['timestamp'])
            elif event['type'] == 'kill':
                db_manager.record_kill(event['timestamp'], event['attacker_steam_id'], event['victim_steam_id'],
                                       event['weapon'], event['attacker_health'], event['distance'], event['headshot'])
                db_manager.update_player(event['attacker_steam_id'], event['attacker_name'], event['timestamp'])
                db_manager.update_player(event['victim_steam_id'], event['victim_name'], event['timestamp'])
            elif event['type'] == 'map_change':
                db_manager.record_map_change(event['timestamp'], event['map_name'])

    db_manager.close()
    logging.info("Script execution finished")

if __name__ == "__main__":
    main()