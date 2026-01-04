from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

import database as db
from states import CreateAd, ViewAds, ContactSeller
from keyboards import (
    categories_keyboard, cancel_keyboard, done_photos_keyboard,
    confirm_ad_keyboard, ad_navigation_keyboard, main_menu_keyboard
)
from config import CATEGORIES, MAX_PHOTOS, ADMIN_IDS
import logging

logger = logging.getLogger(__name__)

router = Router()


# ========== MIDDLEWARE ДЛЯ ПРОВЕРКИ ==========

async def check_user(message: Message) -> bool:
    """Проверка регистрации и блокировки"""
    user_id = message.from_user.id
    
    if await db.is_user_blocked(user_id):
        await message.answer("🚫 Вы заблокированы.")
        return False
    
    if not await db.user_exists(user_id):
        await message.answer("❌ Сначала пройдите регистрацию: /start")
        return False
    
    return True


# ========== СОЗДАНИЕ ОБЪЯВЛЕНИЯ ==========

@router.message(F.text == "📢 Разместить объявление")
async def create_ad_start(message: Message, state: FSMContext):
    """Начало создания объявления"""
    if not await check_user(message):
        return
    
    await message.answer(
        "📢 **Создание объявления**\n\n"
        "📌 Введите **название товара**:",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(CreateAd.title)


@router.message(CreateAd.title)
async def process_title(message: Message, state: FSMContext):
    """Обработка названия"""
    title = message.text.strip()
    
    if len(title) < 3 or len(title) > 100:
        await message.answer("❌ Название должно быть от 3 до 100 символов.")
        return
    
    await state.update_data(title=title)
    await message.answer(
        "📝 Введите **подробное описание** товара:",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(CreateAd.description)


@router.message(CreateAd.description)
async def process_description(message: Message, state: FSMContext):
    """Обработка описания"""
    description = message.text.strip()
    
    if len(description) < 10 or len(description) > 1000:
        await message.answer("❌ Описание должно быть от 10 до 1000 символов.")
        return
    
    await state.update_data(description=description)
    await message.answer(
        "💰 Введите **цену**\n_(например: 100.000$ или Договорная)_:",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(CreateAd.price)


@router.message(CreateAd.price)
async def process_price(message: Message, state: FSMContext):
    """Обработка цены"""
    price = message.text.strip()
    
    if len(price) > 50:
        await message.answer("❌ Цена слишком длинная (макс. 50 символов).")
        return
    
    await state.update_data(price=price)
    await message.answer(
        "📂 Выберите **категорию**:",
        reply_markup=categories_keyboard(for_create=True),
        parse_mode="Markdown"
    )
    await state.set_state(CreateAd.category)


@router.callback_query(CreateAd.category, F.data.startswith("create_cat_"))
async def process_category(callback: CallbackQuery, state: FSMContext):
    """Обработка категории"""
    category = callback.data.replace("create_cat_", "")
    
    await state.update_data(category=category, photos=[])
    await callback.message.edit_text(
        f"🖼 Отправьте **фотографии** товара (до {MAX_PHOTOS} шт.)\n\n"
        "Можете отправлять по одной или альбомом.\n"
        "Когда закончите - нажмите **Готово**.",
        reply_markup=done_photos_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(CreateAd.photos)


@router.message(CreateAd.photos, F.photo)
async def process_photos(message: Message, state: FSMContext):
    """Обработка фотографий"""
    data = await state.get_data()
    photos = data.get('photos', [])
    
    if len(photos) >= MAX_PHOTOS:
        await message.answer(f"❌ Максимум {MAX_PHOTOS} фотографий.")
        return
    
    # Берём фото лучшего качества
    photo_id = message.photo[-1].file_id
    
    # Проверяем, что file_id не пустой
    if photo_id and photo_id.strip():
        photos.append(photo_id)
        await state.update_data(photos=photos)
        await message.answer(
            f"✅ Фото добавлено ({len(photos)}/{MAX_PHOTOS})",
            reply_markup=done_photos_keyboard()
        )
    else:
        await message.answer("❌ Ошибка загрузки фото. Попробуйте ещё раз.")


@router.callback_query(CreateAd.photos, F.data == "photos_done")
async def photos_done(callback: CallbackQuery, state: FSMContext):
    """Завершение загрузки фото"""
    data = await state.get_data()
    photos = data.get('photos', [])
    
    # Фильтруем пустые значения
    photos = [p for p in photos if p and p.strip()]
    
    if not photos:
        await callback.answer("❌ Добавьте хотя бы одно фото!", show_alert=True)
        return
    
    await state.update_data(photos=photos)
    await show_ad_preview(callback, state, data)


@router.callback_query(CreateAd.photos, F.data == "photos_skip")
async def photos_skip(callback: CallbackQuery, state: FSMContext):
    """Пропуск загрузки фото"""
    data = await state.get_data()
    await state.update_data(photos=[])
    data['photos'] = []
    await show_ad_preview(callback, state, data)


async def show_ad_preview(callback: CallbackQuery, state: FSMContext, data: dict):
    """Показ превью объявления"""
    user = await db.get_user(callback.from_user.id)
    
    photos = data.get('photos', [])
    photos = [p for p in photos if p and p.strip()]  # Фильтруем пустые
    
    preview = (
        "📋 **Проверьте объявление:**\n\n"
        f"📌 **Название:** {data['title']}\n"
        f"📝 **Описание:** {data['description']}\n"
        f"💰 **Цена:** {data['price']}\n"
        f"📂 **Категория:** {CATEGORIES.get(data['category'], data['category'])}\n"
        f"🖼 **Фото:** {len(photos)} шт.\n"
        f"📞 **Игровой номер:** {user['game_id']}\n\n"
        "Всё верно?"
    )
    
    await callback.message.edit_text(
        preview,
        reply_markup=confirm_ad_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(CreateAd.confirm)


@router.callback_query(CreateAd.confirm, F.data == "confirm_ad")
async def confirm_ad(callback: CallbackQuery, state: FSMContext):
    """Публикация объявления"""
    data = await state.get_data()
    user_id = callback.from_user.id
    
    # Фильтруем пустые фото
    photos = [p for p in data.get('photos', []) if p and p.strip()]
    
    ad_id = await db.add_ad(
        user_id=user_id,
        title=data['title'],
        description=data['description'],
        price=data['price'],
        category=data['category'],
        photos=photos
    )
    
    from keyboards import admin_menu_keyboard
    keyboard = admin_menu_keyboard() if user_id in ADMIN_IDS else main_menu_keyboard()
    
    await callback.message.edit_text(
        f"✅ **Объявление #{ad_id} опубликовано!**\n\n"
        "Его увидят все пользователи бота.",
        parse_mode="Markdown"
    )
    await callback.message.answer(
        "📋 Главное меню:",
        reply_markup=keyboard
    )
    await state.clear()


# ========== ПРОСМОТР ОБЪЯВЛЕНИЙ ==========

@router.message(F.text == "🔍 Смотреть объявления")
async def view_ads_start(message: Message, state: FSMContext):
    """Начало просмотра объявлений"""
    if not await check_user(message):
        return
    
    await message.answer(
        "📂 Выберите **категорию**:",
        reply_markup=categories_keyboard(for_create=False),
        parse_mode="Markdown"
    )
    await state.set_state(ViewAds.browsing)


@router.callback_query(F.data.startswith("view_cat_"))
async def view_category(callback: CallbackQuery, state: FSMContext):
    """Просмотр категории"""
    category = callback.data.replace("view_cat_", "")
    await show_ad_page(callback, category, 0, state)


@router.callback_query(F.data.startswith("nav_"))
async def navigate_ads(callback: CallbackQuery, state: FSMContext):
    """Навигация по объявлениям"""
    parts = callback.data.split("_")
    category = parts[1]
    page = int(parts[2])
    await show_ad_page(callback, category, page, state)


async def show_ad_page(callback: CallbackQuery, category: str, page: int, state: FSMContext):
    """Показ страницы объявления"""
    total = await db.count_ads_by_category(category)
    
    if total == 0:
        await callback.message.edit_text(
            f"📭 В категории **{CATEGORIES.get(category, category)}** пока нет объявлений.",
            reply_markup=categories_keyboard(for_create=False),
            parse_mode="Markdown"
        )
        return
    
    ads = await db.get_ads_by_category(category, offset=page, limit=1)
    
    if not ads:
        await callback.answer("Объявления не найдены")
        return
    
    ad = ads[0]
    
    text = (
        f"📦 **{ad['title']}**\n\n"
        f"📝 {ad['description']}\n\n"
        f"💰 **Цена:** {ad['price']}\n"
        f"📂 **Категория:** {CATEGORIES.get(ad['category'], ad['category'])}\n"
        f"🕹 **Продавец:** {ad['game_nick']}\n"
        f"📞 **Игровой номер:** {ad['game_id']}"
    )
    
    keyboard = ad_navigation_keyboard(
        category=category,
        current=page,
        total=total,
        ad_id=ad['id'],
        seller_username=ad.get('username'),
        seller_id=ad['seller_id']
    )
    
    # Удаляем предыдущее сообщение
    try:
        await callback.message.delete()
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение: {e}")
    
    # Получаем и фильтруем фото
    photos = ad.get('photos', [])
    photos = [p for p in photos if p and p.strip()]  # Убираем пустые строки
    
    if photos:
        try:
            if len(photos) == 1:
                await callback.message.answer_photo(
                    photo=photos[0],
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            else:
                # Отправляем альбом
                media = [InputMediaPhoto(media=photos[0], caption=text, parse_mode="Markdown")]
                for photo in photos[1:]:
                    if photo and photo.strip():  # Дополнительная проверка
                        media.append(InputMediaPhoto(media=photo))
                
                await callback.message.answer_media_group(media)
                await callback.message.answer(
                    "👆 Фото объявления",
                    reply_markup=keyboard
                )
        except TelegramBadRequest as e:
            # Если фото невалидные, отправляем без них
            logger.error(f"Ошибка отправки фото: {e}")
            await callback.message.answer(
                text + "\n\n⚠️ _Фото недоступны_",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
    else:
        await callback.message.answer(
            text + "\n\n📷 _Без фото_",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    await state.update_data(current_ad=ad, category=category, page=page)


@router.callback_query(F.data == "back_categories")
async def back_to_categories(callback: CallbackQuery, state: FSMContext):
    """Возврат к категориям"""
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    await callback.message.answer(
        "📂 Выберите **категорию**:",
        reply_markup=categories_keyboard(for_create=False),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "current_page")
async def current_page_callback(callback: CallbackQuery):
    """Заглушка для кнопки номера страницы"""
    await callback.answer()


# ========== СВЯЗЬ С ПРОДАВЦОМ ==========

@router.callback_query(F.data.startswith("contact_"))
async def contact_seller_start(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Начало связи с продавцом"""
    parts = callback.data.split("_")
    seller_id = int(parts[1])
    ad_id = int(parts[2])
    
    if seller_id == callback.from_user.id:
        await callback.answer("Это ваше объявление 😊", show_alert=True)
        return
    
    await state.update_data(seller_id=seller_id, ad_id=ad_id)
    await callback.message.answer(
        "📝 Напишите сообщение для продавца:",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(ContactSeller.message)


@router.message(ContactSeller.message)
async def send_message_to_seller(message: Message, state: FSMContext, bot: Bot):
    """Отправка сообщения продавцу"""
    data = await state.get_data()
    seller_id = data['seller_id']
    ad_id = data['ad_id']
    
    buyer = await db.get_user(message.from_user.id)
    ad = await db.get_ad(ad_id)
    
    if not ad:
        await message.answer("❌ Объявление не найдено.")
        await state.clear()
        return
    
    seller_message = (
        f"📩 **Новое сообщение по объявлению!**\n\n"
        f"📦 **Объявление:** {ad['title']}\n"
        f"👤 **От:** {buyer['game_nick']}\n"
        f"📞 **Игровой номер:** {buyer['game_id']}\n\n"
        f"💬 **Сообщение:**\n{message.text}"
    )
    
    try:
        # Отправляем продавцу
        if message.from_user.username:
            seller_message += f"\n\n📱 Telegram: @{message.from_user.username}"
        
        await bot.send_message(seller_id, seller_message, parse_mode="Markdown")
        await message.answer("✅ Сообщение отправлено продавцу!")
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения продавцу: {e}")
        await message.answer("❌ Не удалось отправить сообщение. Продавец заблокировал бота.")
    
    from keyboards import admin_menu_keyboard
    keyboard = admin_menu_keyboard() if message.from_user.id in ADMIN_IDS else main_menu_keyboard()
    await message.answer("📋 Главное меню:", reply_markup=keyboard)
    await state.clear()