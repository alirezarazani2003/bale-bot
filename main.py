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

def is_valid_channel_id(text):
    return bool(re.match(r"^@\w{5,}$", text))

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

def send_message(chat_id, text, keyboard=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
    }
    if keyboard:
        payload["reply_markup"] = keyboard
    send_bale_request("sendMessage", payload)

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


def forward_to_channels(message, chat_id):
    channels = load_channels(chat_id)
    success, failed = [], []
    caption = message.get('caption', '')

    for channel in channels:
        try:
            if 'text' in message:
                resp = send_bale_request("sendMessage", {"chat_id": channel, "text": message['text']})
            elif 'photo' in message:
                file_id = message['photo'][-1]['file_id']
                resp = send_bale_request("sendPhoto", {"chat_id": channel, "photo": file_id, "caption": caption})
            elif 'document' in message:
                file_id = message['document']['file_id']
                resp = send_bale_request("sendDocument", {"chat_id": channel, "document": file_id, "caption": caption})
            elif 'video' in message:
                file_id = message['video']['file_id']
                resp = send_bale_request("sendVideo", {"chat_id": channel, "video": file_id, "caption": caption})
            elif 'voice' in message:
                file_id = message['voice']['file_id']
                resp = send_bale_request("sendVoice", {"chat_id": channel, "voice": file_id, "caption": caption})
            else:
                failed.append(f"{channel} ➔ نوع پیام پشتیبانی نمی‌شود")
                continue

            if resp.get('ok'):
                success.append(channel)
            else:
                failed.append(f"{channel} ➔ {resp.get('description', 'خطای نامشخص')}")

        except Exception as e:
            failed.append(f"{channel} ➔ {str(e)}")

    return success, failed


def is_rate_limited(chat_id):
    now = time.time()
    if now - USER_LAST_REQUEST[chat_id] < int(os.getenv('RATE_LIMIT')):
        return True
    USER_LAST_REQUEST[chat_id] = now
    return False


def handle_update(update):
    message = update.get('message', {})
    chat_id = message.get('chat', {}).get('id')
    text = message.get('text', '')

    if not chat_id or message.get('from', {}).get('is_bot') or message.get('chat', {}).get('type') != 'private':
        return

    if ALLOWED_USERS and chat_id not in ALLOWED_USERS:
        send_message(chat_id, "⛔ شما مجاز به استفاده از این ربات نیستید.")
        return

    if is_rate_limited(chat_id):
        send_message(chat_id, "⏱ لطفاً چند لحظه صبر کنید و دوباره تلاش کنید.")
        return

    state = USER_STATE.get(chat_id)

    if text == '/start' or text == '🔙 بازگشت به منوی اصلی':
        send_message(chat_id, "👋 خوش اومدی! یکی از گزینه‌های زیر رو انتخاب کن:", keyboard=build_main_menu())
        USER_STATE[chat_id] = None

    elif text == "✉️ ارسال پیام به کانال‌ها":
        send_message(chat_id, "📝 لطفاً پیام یا محتوایی که می‌خوای به کانال‌ها بفرستی رو بفرست:")
        USER_STATE[chat_id] = 'waiting_for_message'

    elif text == "➕ اضافه کردن کانال":
        send_message(chat_id, "📥 لطفاً آیدی کانال (مثل @mychannel) رو بفرست:")
        USER_STATE[chat_id] = 'waiting_for_channel'

    elif text == "➖ حذف کانال":
        send_message(chat_id, "🗑 آیدی کانالی که می‌خوای حذف بشه رو بفرست:")
        USER_STATE[chat_id] = 'removing_channel'

    elif text == "📜 دیدن لیست کانال‌ها":
        channels = load_channels(chat_id)
        channels_text = '\n'.join(channels) if channels else '❌ هنوز کانالی اضافه نکردی'
        send_message(chat_id, f"🔹 لیست کانال‌ها:\n{channels_text}")

    elif state == 'waiting_for_message':
        channels = load_channels(chat_id)
        if not channels:
            send_message(chat_id, "❌ هنوز کانالی اضافه نکردی. اول کانال اضافه کن.", keyboard=build_main_menu())
            USER_STATE[chat_id] = None
            return

        success, failed = forward_to_channels(message, chat_id)
        result_text = ""
        if success:
            result_text += "✅ پیام با موفقیت به این کانال‌ها ارسال شد:\n" + "\n".join(success)
        if failed:
            if result_text:
                result_text += "\n\n"
            result_text += "⚠️ خطا در ارسال به این کانال‌ها:\n" + "\n".join(failed)

        send_message(chat_id, result_text, keyboard=build_main_menu())
        USER_STATE[chat_id] = None

    elif state == 'waiting_for_channel':
        if is_valid_channel_id(text):
            channels = load_channels(chat_id)
            if text not in channels:
                channels.append(text)
                save_channels(chat_id, channels)
                send_message(chat_id, f"✅ کانال {text} اضافه شد.", keyboard=build_main_menu())
            else:
                send_message(chat_id, "ℹ️ این کانال قبلاً اضافه شده.", keyboard=build_main_menu())
        else:
            send_message(chat_id, "❌ آیدی معتبر نیست. باید با @ و حداقل ۵ حرف باشد.")
        USER_STATE[chat_id] = None

    elif state == 'removing_channel':
        channels = load_channels(chat_id)
        if text in channels:
            channels.remove(text)
            save_channels(chat_id, channels)
            send_message(chat_id, f"✅ کانال {text} حذف شد.", keyboard=build_main_menu())
        else:
            send_message(chat_id, "⚠️ چنین کانالی پیدا نشد.", keyboard=build_main_menu())
        USER_STATE[chat_id] = None

    else:
        send_message(chat_id, "❓ لطفاً یکی از گزینه‌های منو رو انتخاب کن.", keyboard=build_main_menu())


def get_updates(offset=None):
    url = f"https://tapi.bale.ai/bot{BOT_TOKEN}/getUpdates"
    payload = {"timeout": 10}
    if offset:
        payload["offset"] = offset
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except:
        return {}
    
def main():
    offset = None
    while True:
        try:
            updates = get_updates(offset)
            for update in updates.get('result', []):
                handle_update(update)
                offset = update['update_id'] + 1
        except Exception as e:
            print(f"[ERROR] {e}")
        time.sleep(1)

if __name__ == "__main__":
    main()