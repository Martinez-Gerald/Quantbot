import requests
import os
from dotenv import load_dotenv

load_dotenv()

def send_discord_alert(message):
    url = os.getenv("DISCORD_WEBHOOK")
    if not url: return
    
    data = {"content": message}
    try:
        requests.post(url, json=data)
    except:
        pass