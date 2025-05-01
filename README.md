
# داکیومنت کد بات بله با قابلیت ارسال پیام به کانال‌ها

## هدف کد
این کد به عنوان یک ربات بله عمل می‌کند که به کاربران این امکان را می‌دهد که پیام‌ها یا محتواهایی مانند تصاویر، ویدیوها، فایل‌ها و غیره را به چندین کانال ارسال کنند. همچنین کاربران می‌توانند کانال‌ها را اضافه یا حذف کنند و لیست کانال‌های موجود خود را مشاهده نمایند.

## پیش‌نیازها
1. **کتابخانه‌ها و پکیج‌ها**:
   - `requests` برای ارسال درخواست‌ها به API.
   - `json` برای کار با داده‌های JSON.
   - `os` برای مدیریت متغیرهای محیطی.
   - `time` برای مدیریت تاخیرات زمانی (rate-limiting).
   - `dotenv` برای بارگذاری متغیرهای محیطی از فایل `.env`.
   - `collections` برای استفاده از `defaultdict`.
   - `re` برای بررسی اعتبار آیدی کانال‌ها.

2. **متغیرهای محیطی**:
   - `BOT_TOKEN`: توکن ربات بله.
   - `ALLOWED_USERS`: یک لیست از شناسه‌های کاربران مجاز برای استفاده از ربات.
   - `RATE_LIMIT`: زمان محدودیت درخواست‌ها (ثانیه).

## توضیحات کد

### بارگذاری متغیرهای محیطی
```python
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
USER_STATE = {}
USER_LAST_REQUEST = defaultdict(lambda: 0)
```
در اینجا، از `load_dotenv()` برای بارگذاری متغیرهای محیطی از فایل `.env` استفاده می‌شود. این توکن ربات (`BOT_TOKEN`) و تنظیمات مربوط به کاربران و محدودیت‌های زمانی (rate-limiting) را از فایل `.env` می‌خوانیم.

### تابع `allowed_users_check`
```python
def allowed_users_check(allowed: str):
    return set(map(int, allowed.split(',')))
```
این تابع یک رشته از شناسه‌های کاربران مجاز را می‌گیرد (مانند `"12345,67890"`) و آن‌ها را به یک مجموعه (`set`) از اعداد تبدیل می‌کند تا بررسی دسترسی برای ربات راحت‌تر باشد.

### بارگذاری و ذخیره کانال‌ها
```python
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
```
این دو تابع برای بارگذاری و ذخیره لیست کانال‌های مرتبط با هر کاربر به‌صورت محلی (در فایل JSON) استفاده می‌شوند.

### تابع `send_bale_request`
```python
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
```
این تابع برای ارسال درخواست‌های API به ربات بله از طریق `POST` استفاده می‌شود. اگر فایل‌هایی برای ارسال وجود داشته باشد، آن‌ها را به صورت `files` ارسال می‌کند و در غیر این صورت، داده‌ها به‌صورت JSON ارسال می‌شوند.

### تابع `send_message`
```python
def send_message(chat_id, text, keyboard=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
    }
    if keyboard:
        payload["reply_markup"] = keyboard
    send_bale_request("sendMessage", payload)
```
این تابع برای ارسال پیام متنی به چت خاصی (بر اساس شناسه `chat_id`) با استفاده از متد `sendMessage` در API ربات بله است. می‌تواند شامل یک صفحه کلید سفارشی نیز باشد.

### تابع `build_main_menu`
```python
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
```
این تابع یک صفحه کلید اصلی برای نمایش به کاربر می‌سازد که شامل گزینه‌های مختلفی مثل ارسال پیام به کانال‌ها، اضافه کردن کانال و غیره است.

### ارسال پیام به کانال‌ها
```python
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
```
این تابع پیام‌های ارسالی از طرف کاربر را به کانال‌های ذخیره‌شده برای آن کاربر ارسال می‌کند. هر نوع پیام (متن، عکس، ویدیو و ...) به روش مخصوص خود ارسال می‌شود و در نهایت نتیجه موفقیت‌آمیز یا ناموفق بودن ارسال پیام به هر کانال گزارش می‌شود.

### محدودیت نرخ درخواست‌ها
```python
def is_rate_limited(chat_id):
    now = time.time()
    if now - USER_LAST_REQUEST[chat_id] < int(os.getenv('RATE_LIMIT')):
        return True
    USER_LAST_REQUEST[chat_id] = now
    return False
```
این تابع بررسی می‌کند که آیا کاربر در زمان معین مجاز به ارسال درخواست جدید است یا خیر (برای جلوگیری از ارسال درخواست‌های متوالی و زیاد).

### مدیریت بروزرسانی‌ها
```python
def handle_update(update):
    # بررسی و پردازش بروزرسانی‌های دریافتی از کاربران
    # وضعیت‌های مختلف منو مانند ارسال پیام، اضافه کردن کانال و غیره مدیریت می‌شود.
```
این بخش شامل پردازش و مدیریت پیام‌های ورودی است که از بله دریافت می‌شود. طبق پیامی که از کاربر می‌آید، ربات به حالت‌های مختلفی وارد می‌شود (مانند ارسال پیام، اضافه کردن کانال و غیره).

### اجرای ربات
```python
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
```
این بخش به‌طور پیوسته به API بله متصل است و بروزرسانی‌ها را دریافت و پردازش می‌کند. پس از هر بروزرسانی، offset به‌روزرسانی می‌شود تا اطلاعات جدید دریافت شود.

## نحوه استفاده
1. **توکن ربات را در فایل `.env` قرار دهید.**
2. **محدودیت نرخ درخواست‌ها و کاربران مجاز را تنظیم کنید.**
3. **اجرا کردن ربات با دستور `python bot.py`.**
