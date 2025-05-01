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


