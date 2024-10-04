import re
from datetime import datetime

class LogParser:
    CONNECT_RE = re.compile(r'\[event_logger\.smx\] Player connected: (.+) \(Steam ID: (.+)\)')
    DISCONNECT_RE = re.compile(r'\[event_logger\.smx\] Player disconnected: (.+)')
    KILL_RE = re.compile(r'\[event_logger\.smx\] Kill: (.+) \((.+)\) killed (.+) \((.+)\) \| Weapon: (.+) \| Attacker Health: (\d+) \| Distance: ([\d.]+) \| Headshot: (.+)')
    MAP_CHANGE_RE = re.compile(r'\[event_logger\.smx\] Map changed to: (.+)')

    @staticmethod
    def parse_line(line):
        timestamp = datetime.now().strftime('%m/%d/%Y - %H:%M:%S')
        
        connect_match = LogParser.CONNECT_RE.search(line)
        if connect_match:
            return {'type': 'connect', 'timestamp': timestamp, 'player_name': connect_match.group(1), 'steam_id': connect_match.group(2)}

        disconnect_match = LogParser.DISCONNECT_RE.search(line)
        if disconnect_match:
            return {'type': 'disconnect', 'timestamp': timestamp, 'player_name': disconnect_match.group(1)}

        kill_match = LogParser.KILL_RE.search(line)
        if kill_match:
            return {
                'type': 'kill',
                'timestamp': timestamp,
                'attacker_name': kill_match.group(1),
                'attacker_steam_id': kill_match.group(2),
                'victim_name': kill_match.group(3),
                'victim_steam_id': kill_match.group(4),
                'weapon': kill_match.group(5),
                'attacker_health': int(kill_match.group(6)),
                'distance': float(kill_match.group(7)),
                'headshot': kill_match.group(8) == 'Yes'
            }

        map_change_match = LogParser.MAP_CHANGE_RE.search(line)
        if map_change_match:
            return {'type': 'map_change', 'timestamp': timestamp, 'map_name': map_change_match.group(1)}

        return None