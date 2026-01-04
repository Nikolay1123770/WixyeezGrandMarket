from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from config import CATEGORIES


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📢 Разместить объявление"),
        KeyboardButton(text="🔍 Смотреть объявления")
    )
    builder.row(
        KeyboardButton(text="👤 Мой профиль"),
        KeyboardButton(text="📋 Мои объявления")
    )
    return builder.as_markup(resize_keyboard=True)


def admin_menu_keyboard() -> ReplyKeyboardMarkup:
    """Меню администратора"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📢 Разместить объявление"),
        KeyboardButton(text="🔍 Смотреть объявления")
    )
    builder.row(
        KeyboardButton(text="👤 Мой профиль"),
        KeyboardButton(text="📋 Мои объявления")
    )
    builder.row(
        KeyboardButton(text="🔧 Админ-панель")
    )
    return builder.as_markup(resize_keyboard=True)


def admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура админ-панели"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👥 Все пользователи", callback_data="admin_users")
    )
    builder.row(
        InlineKeyboardButton(text="📋 Все объявления", callback_data="admin_ads")
    )
    builder.row(
        InlineKeyboardButton(text="🚫 Заблокировать", callback_data="admin_block"),
        InlineKeyboardButton(text="✅ Разблокировать", callback_data="admin_unblock")
    )
    builder.row(
        InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")
    )
    return builder.as_markup()


def categories_keyboard(for_create: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура выбора категории"""
    builder = InlineKeyboardBuilder()
    prefix = "create_cat_" if for_create else "view_cat_"
    
    for cat_id, cat_name in CATEGORIES.items():
        builder.row(
            InlineKeyboardButton(text=cat_name, callback_data=f"{prefix}{cat_id}")
        )
    
    if not for_create:
        builder.row(
            InlineKeyboardButton(text="🔙 В меню", callback_data="back_menu")
        )
    else:
        builder.row(
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_create")
        )
    
    return builder.as_markup()


def cancel_keyboard() -> InlineKeyboardMarkup:
    """Кнопка отмены"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_create")
    )
    return builder.as_markup()


def confirm_ad_keyboard() -> InlineKeyboardMarkup:
    """Подтверждение создания объявления"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Опубликовать", callback_data="confirm_ad"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_create")
    )
    return builder.as_markup()


def done_photos_keyboard() -> InlineKeyboardMarkup:
    """Кнопка завершения загрузки фото"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Готово", callback_data="photos_done")
    )
    builder.row(
        InlineKeyboardButton(text="⏭ Пропустить", callback_data="photos_skip")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_create")
    )
    return builder.as_markup()


def ad_navigation_keyboard(category: str, current: int, total: int, ad_id: int, 
                           seller_username: str = None, seller_id: int = None) -> InlineKeyboardMarkup:
    """Навигация по объявлениям"""
    builder = InlineKeyboardBuilder()
    
    # Навигация
    nav_buttons = []
    if current > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"nav_{category}_{current - 1}")
        )
    nav_buttons.append(
        InlineKeyboardButton(text=f"{current + 1}/{total}", callback_data="current_page")
    )
    if current < total - 1:
        nav_buttons.append(
            InlineKeyboardButton(text="➡️", callback_data=f"nav_{category}_{current + 1}")
        )
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    # Связь с продавцом
    if seller_username:
        builder.row(
            InlineKeyboardButton(
                text="📩 Связаться с продавцом", 
                url=f"https://t.me/{seller_username}"
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="📩 Написать продавцу", 
                callback_data=f"contact_{seller_id}_{ad_id}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="🔙 К категориям", callback_data="back_categories")
    )
    
    return builder.as_markup()


def my_ads_keyboard(ads: list) -> InlineKeyboardMarkup:
    """Список объявлений пользователя"""
    builder = InlineKeyboardBuilder()
    
    for ad in ads:
        builder.row(
            InlineKeyboardButton(
                text=f"📦 {ad['title'][:30]}... - {ad['price']}",
                callback_data=f"my_ad_{ad['id']}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="🔙 В меню", callback_data="back_menu")
    )
    
    return builder.as_markup()


def manage_ad_keyboard(ad_id: int) -> InlineKeyboardMarkup:
    """Управление объявлением"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_ad_{ad_id}")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_ad_{ad_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 К моим объявлениям", callback_data="back_my_ads")
    )
    return builder.as_markup()


def edit_ad_keyboard(ad_id: int) -> InlineKeyboardMarkup:
    """Выбор поля для редактирования"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📌 Название", callback_data=f"edit_field_title_{ad_id}")
    )
    builder.row(
        InlineKeyboardButton(text="📝 Описание", callback_data=f"edit_field_desc_{ad_id}")
    )
    builder.row(
        InlineKeyboardButton(text="💰 Цена", callback_data=f"edit_field_price_{ad_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🖼 Фото", callback_data=f"edit_field_photos_{ad_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data=f"my_ad_{ad_id}")
    )
    return builder.as_markup()


def confirm_delete_keyboard(ad_id: int) -> InlineKeyboardMarkup:
    """Подтверждение удаления"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_{ad_id}"),
        InlineKeyboardButton(text="❌ Отмена", callback_data=f"my_ad_{ad_id}")
    )
    return builder.as_markup()


def profile_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура профиля"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✏️ Изменить ник", callback_data="edit_profile_nick")
    )
    builder.row(
        InlineKeyboardButton(text="📞 Изменить игровой номер", callback_data="edit_profile_game_id")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 В меню", callback_data="back_menu")
    )
    return builder.as_markup()


def admin_ad_keyboard(ad_id: int) -> InlineKeyboardMarkup:
    """Управление объявлением для админа"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin_delete_ad_{ad_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_ads")
    )
    return builder.as_markup()