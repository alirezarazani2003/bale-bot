import requests
import time
from dotenv import load_dotenv
import os


load_dotenv()



BOT_TOKEN = os.getenv('CHAT_ID_FOUNDER_BOT_TOKEN')

def send_bale_request(method, data):
    url = f"https://tapi.bale.ai/bot{BOT_TOKEN}/{method}"
    response = requests.post(url, json=data)
    try:
        return response.json()
    except:
        return {}

def send_message(chat_id, text):
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    send_bale_request("sendMessage", payload)

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
        updates = get_updates(offset)
        for update in updates.get('result', []):
            message = update.get('message', {})
            chat = message.get('chat', {})
            chat_id = chat.get('id')
            if chat_id:
                print(f"User chat_id: {chat_id}")
                send_message(chat_id, f"آیدی شما: {chat_id}")
            offset = update['update_id'] + 1
        time.sleep(1)

if __name__ == "__main__":
    main()
