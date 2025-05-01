import time
import requests
import json
import os
from dotenv import load_dotenv
from collections import defaultdict
import re

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
USER_STATE = {}
USER_LAST_REQUEST = defaultdict(lambda: 0)
ALLOWED_USERS = os.getenv('ALLOWED_USER')

def load_channels(chat_id):
    user_channels_file = f'{chat_id}_channels.json'
    if os.path.exists(user_channels_file):
        with open(user_channels_file, 'r') as f:
            return json.load(f)
    else:
        return []
    
def save_channels(chat_id, channels):
    user_channels_file = f'{chat_id}_channels.json'
    with open(user_channels_file, 'w') as f:
        json.dump(channels, f)
