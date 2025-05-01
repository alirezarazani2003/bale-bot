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
        
def send_bale_request(method, data, files=None):
    url = f"https://tapi.bale.ai/bot{BOT_TOKEN}/{method}"
    if files:
        response = requests.post(url, data=data, files=files)
    else:
        response = requests.post(url, json=data)
    try:
        return response.json()
    except Exception:
        return {"ok": False, "description": "Invalid response"}


def build_main_menu():
    return {
        "keyboard": [
            [{"text": "✉️ ارسال پیام به کانال‌ها"}],
            [{"text": "➕ اضافه کردن کانال"}],
            [{"text": "➖ حذف کانال"}],
            [{"text": "📜 دیدن لیست کانال‌ها"}],
            [{"text": "🔙 بازگشت به منوی اصلی"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }