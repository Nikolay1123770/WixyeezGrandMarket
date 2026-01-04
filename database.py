import aiosqlite
from datetime import datetime
from typing import Optional, List, Dict, Any

DATABASE = "grand_mobile.db"


async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect(DATABASE) as db:
        # Таблица пользователей
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                game_nick TEXT NOT NULL,
                game_id TEXT NOT NULL,
                is_blocked INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица объявлений
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                price TEXT NOT NULL,
                category TEXT NOT NULL,
                photos TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (telegram_id)
            )
        """)
        
        await db.commit()


def parse_photos(photos_str: str) -> List[str]:
    """Безопасный парсинг строки с фотографиями"""
    if not photos_str or photos_str.strip() == "":
        return []
    # Фильтруем пустые строки
    return [p.strip() for p in photos_str.split(',') if p.strip()]


def photos_to_string(photos: List[str]) -> str:
    """Преобразование списка фото в строку"""
    if not photos:
        return ""
    # Фильтруем пустые значения
    valid_photos = [p for p in photos if p and p.strip()]
    return ",".join(valid_photos)


# ========== ПОЛЬЗОВАТЕЛИ ==========

async def user_exists(telegram_id: int) -> bool:
    """Проверка существования пользователя"""
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.execute(
            "SELECT 1 FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        return await cursor.fetchone() is not None


async def add_user(telegram_id: int, username: str, game_nick: str, game_id: str):
    """Добавление нового пользователя"""
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute(
            """INSERT INTO users (telegram_id, username, game_nick, game_id) 
               VALUES (?, ?, ?, ?)""",
            (telegram_id, username, game_nick, game_id)
        )
        await db.commit()


async def get_user(telegram_id: int) -> Optional[Dict]:
    """Получение данных пользователя"""
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_user(telegram_id: int, game_nick: str = None, game_id: str = None):
    """Обновление данных пользователя"""
    async with aiosqlite.connect(DATABASE) as db:
        if game_nick:
            await db.execute(
                "UPDATE users SET game_nick = ? WHERE telegram_id = ?",
                (game_nick, telegram_id)
            )
        if game_id:
            await db.execute(
                "UPDATE users SET game_id = ? WHERE telegram_id = ?",
                (game_id, telegram_id)
            )
        await db.commit()


async def is_user_blocked(telegram_id: int) -> bool:
    """Проверка блокировки пользователя"""
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.execute(
            "SELECT is_blocked FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()
        return row[0] == 1 if row else False


async def block_user(telegram_id: int, block: bool = True):
    """Блокировка/разблокировка пользователя"""
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute(
            "UPDATE users SET is_blocked = ? WHERE telegram_id = ?",
            (1 if block else 0, telegram_id)
        )
        await db.commit()


async def get_all_users() -> List[Dict]:
    """Получение всех пользователей"""
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


# ========== ОБЪЯВЛЕНИЯ ==========

async def add_ad(user_id: int, title: str, description: str, 
                 price: str, category: str, photos: List[str]) -> int:
    """Создание нового объявления"""
    async with aiosqlite.connect(DATABASE) as db:
        photos_str = photos_to_string(photos)
        cursor = await db.execute(
            """INSERT INTO ads (user_id, title, description, price, category, photos) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, title, description, price, category, photos_str)
        )
        await db.commit()
        return cursor.lastrowid


async def get_ad(ad_id: int) -> Optional[Dict]:
    """Получение объявления по ID"""
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT ads.*, users.game_nick, users.game_id, users.username, users.telegram_id as seller_id
               FROM ads 
               JOIN users ON ads.user_id = users.telegram_id 
               WHERE ads.id = ? AND ads.is_active = 1""",
            (ad_id,)
        )
        row = await cursor.fetchone()
        if row:
            data = dict(row)
            data['photos'] = parse_photos(data.get('photos', ''))
            return data
        return None


async def get_ads_by_category(category: str, offset: int = 0, limit: int = 1) -> List[Dict]:
    """Получение объявлений по категории"""
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT ads.*, users.game_nick, users.game_id, users.username, users.telegram_id as seller_id
               FROM ads 
               JOIN users ON ads.user_id = users.telegram_id 
               WHERE ads.category = ? AND ads.is_active = 1 AND users.is_blocked = 0
               ORDER BY ads.created_at DESC
               LIMIT ? OFFSET ?""",
            (category, limit, offset)
        )
        rows = await cursor.fetchall()
        result = []
        for row in rows:
            data = dict(row)
            data['photos'] = parse_photos(data.get('photos', ''))
            result.append(data)
        return result


async def count_ads_by_category(category: str) -> int:
    """Подсчёт объявлений в категории"""
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.execute(
            """SELECT COUNT(*) FROM ads 
               JOIN users ON ads.user_id = users.telegram_id
               WHERE ads.category = ? AND ads.is_active = 1 AND users.is_blocked = 0""",
            (category,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0


async def get_user_ads(user_id: int) -> List[Dict]:
    """Получение объявлений пользователя"""
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT * FROM ads WHERE user_id = ? AND is_active = 1 
               ORDER BY created_at DESC""",
            (user_id,)
        )
        rows = await cursor.fetchall()
        result = []
        for row in rows:
            data = dict(row)
            data['photos'] = parse_photos(data.get('photos', ''))
            result.append(data)
        return result


async def update_ad(ad_id: int, **kwargs):
    """Обновление объявления"""
    async with aiosqlite.connect(DATABASE) as db:
        for key, value in kwargs.items():
            if key == 'photos':
                value = photos_to_string(value)
            await db.execute(
                f"UPDATE ads SET {key} = ? WHERE id = ?",
                (value, ad_id)
            )
        await db.commit()


async def delete_ad(ad_id: int):
    """Удаление объявления (мягкое)"""
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute(
            "UPDATE ads SET is_active = 0 WHERE id = ?", (ad_id,)
        )
        await db.commit()


async def get_all_ads() -> List[Dict]:
    """Получение всех активных объявлений (для админа)"""
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT ads.*, users.game_nick, users.game_id, users.username, users.telegram_id as seller_id
               FROM ads 
               JOIN users ON ads.user_id = users.telegram_id 
               WHERE ads.is_active = 1
               ORDER BY ads.created_at DESC"""
        )
        rows = await cursor.fetchall()
        result = []
        for row in rows:
            data = dict(row)
            data['photos'] = parse_photos(data.get('photos', ''))
            result.append(data)
        return result