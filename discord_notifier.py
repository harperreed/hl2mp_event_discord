import requests
import logging
from config import DISCORD_WEBHOOK_URL

class DiscordNotifier:
    @staticmethod
    def send_notification(content):
        logging.info(f"Attempting to send Discord notification: {content}")
        try:
            response = requests.post(DISCORD_WEBHOOK_URL, json={"content": content})
            if response.status_code == 204:
                logging.info("Discord notification sent successfully")
            else:
                logging.error(f"Failed to send Discord notification. Status code: {response.status_code}")
        except requests.RequestException as e:
            logging.error(f"Error sending Discord notification: {str(e)}")