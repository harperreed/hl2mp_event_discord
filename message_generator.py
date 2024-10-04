import random

class MessageGenerator:
    @staticmethod
    def generate_connect_message(player_name):
        return f"🟢 {player_name} joined the server"

    @staticmethod
    def generate_disconnect_message(player_name):
        return f"🔴 {player_name} left the server"

    @staticmethod
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
        }

        for weapon_type, messages in weapon_messages.items():
            if weapon_type in weapon.lower():
                return f"💀 {random.choice(messages)}"

        return f"💀 {attacker} eliminated {victim} with a {weapon}"

    @staticmethod
    def generate_map_change_message(map_name):
        return f"🗺️ Map changed to: {map_name}"