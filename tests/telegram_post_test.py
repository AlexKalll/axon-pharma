#telegram_post.py

import requests
from dotenv import load_dotenv
import os

load_dotenv()

channel = os.getenv('CHANNEL_USERNAME')
group = os.getenv('GROUP_USERNAME')

def send_to_telegram_channel(message):
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("Error: Telegram bot token not found. Please set TELEGRAM_BOT_TOKEN in your .env file.")
        return
    
    if not channel:
        print("Error: Telegram username username not found. Please set CHANNEL_USERNAME in your .env file.")
        return
    
    if not group:
        print("Error: Telegram group username not found. Please set GROUP_USERNAME in your .env file.")
        return

    # Telegram API endpoint
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    # Required parameters, the chat_id and the message
    usernames = [channel, group]
    for username in usernames:
        params = {
            'chat_id': username,
            'text': message,
            'parse_mode': 'HTML',  # support HTML formatting
        }
        try:
            response = requests.post(url, data=params)
            response_data = response.json()
            
            if response_data.get('ok'):
                print(f"Message sent to {username}")
                print("Message ID:", response_data['result']['message_id'])
            else:
                print(f"Failed to send to {username}")
                print("Error:", response_data.get('description'))
        
        except Exception as e:
            print(f"Error sending to {username}:", str(e))


# Message to send, any text or html formt 
message = """'<b> New Stock Alert!</b> \n\nWe have imported new <b>Amoxicillin tablets</b> from a certified supplier! \n Rest assured of the highest quality and effectiveness. Stay healthy with Axon Pharmacy! '
"""
    
send_to_telegram_channel(message)