import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]

# Категории объявлений
CATEGORIES = {
    "auto": "🚗 Авто",
    "realty": "🏠 Недвижимость",
    "business": "💼 Бизнес",
    "other": "📦 Прочее"
}

MAX_PHOTOS = 10
ADS_PER_PAGE = 1