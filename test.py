import requests
from dotenv import load_dotenv
import os

load_dotenv()

def send_to_telegram_channel():
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("Error: Telegram bot token not found. Please set TELEGRAM_BOT_TOKEN in your .env file.")
        return
    
    channel_username = os.getenv('CHANNEL_USERNAME')
    if not channel_username:
        print("Error: Telegram channel username not found. Please set CHANNEL_USERNAME in your .env file.")
        return

    # Message to send, any text or html formt 
    message = """<b>New Stock Update</b>
    <i>We have just received a new shipment of medicines!</i>"""
    
    # Telegram API endpoint
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    # Required parameters, the chat_id and the message
    params = {
    'chat_id': channel_username,
    'text': message,
    'parse_mode': 'HTML',  # support HTML formatting
}
    
    try:
        response = requests.post(url, data=params)
        response_data = response.json()
        
        if response_data.get('ok'):
            print("Message successfully sent to channel!")
            print("Message ID:", response_data['result']['message_id'])
        else:
            print("Failed to send message")
            print("Error:", response_data.get('description'))
    
    except Exception as e:
        print("An error occurred:", str(e))


send_to_telegram_channel()