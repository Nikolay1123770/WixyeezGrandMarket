from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
from states import EditProfile, EditAd
from keyboards import (
    profile_keyboard, my_ads_keyboard, manage_ad_keyboard,
    edit_ad_keyboard, confirm_delete_keyboard, cancel_keyboard,
    main_menu_keyboard, done_photos_keyboard
)
from config import CATEGORIES, ADMIN_IDS, MAX_PHOTOS

router = Router()


# ========== ПРОФИЛЬ ==========

@router.message(F.text == "👤 Мой профиль")
async def show_profile(message: Message):
    """Показ профиля"""
    user = await db.get_user(message.from_user.id)
    
    if not user:
        await message.answer("❌ Сначала пройдите регистрацию: /start")
        return
    
    text = (
        "👤 **Ваш профиль**\n\n"
        f"🕹 **Игровой ник:** {user['game_nick']}\n"
        f"📞 **Игровой номер:** {user['game_id']}\n"
        f"📱 **Telegram ID:** `{user['telegram_id']}`"
    )
    
    await message.answer(
        text,
        reply_markup=profile_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "edit_profile_nick")
async def edit_nick_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования ника"""
    await callback.message.edit_text(
        "🕹 Введите новый **игровой ник**:",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(EditProfile.edit_nick)


@router.message(EditProfile.edit_nick)
async def process_new_nick(message: Message, state: FSMContext):
    """Сохранение нового ника"""
    new_nick = message.text.strip()
    
    if len(new_nick) < 2 or len(new_nick) > 32:
        await message.answer("❌ Ник должен быть от 2 до 32 символов.")
        return
    
    await db.update_user(message.from_user.id, game_nick=new_nick)
    
    keyboard = main_menu_keyboard()
    if message.from_user.id in ADMIN_IDS:
        from keyboards import admin_menu_keyboard
        keyboard = admin_menu_keyboard()
    
    await message.answer(f"✅ Ник изменён на **{new_nick}**", parse_mode="Markdown")
    await message.answer("📋 Главное меню:", reply_markup=keyboard)
    await state.clear()


@router.callback_query(F.data == "edit_profile_game_id")
async def edit_game_id_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования игрового ID"""
    await callback.message.edit_text(
        "📞 Введите новый **игровой номер (ID)**:",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(EditProfile.edit_game_id)


@router.message(EditProfile.edit_game_id)
async def process_new_game_id(message: Message, state: FSMContext):
    """Сохранение нового игрового ID"""
    new_id = message.text.strip()
    
    if len(new_id) < 1 or len(new_id) > 20:
        await message.answer("❌ ID должен быть от 1 до 20 символов.")
        return
    
    await db.update_user(message.from_user.id, game_id=new_id)
    
    keyboard = main_menu_keyboard()
    if message.from_user.id in ADMIN_IDS:
        from keyboards import admin_menu_keyboard
        keyboard = admin_menu_keyboard()
    
    await message.answer(f"✅ Игровой номер изменён на **{new_id}**", parse_mode="Markdown")
    await message.answer("📋 Главное меню:", reply_markup=keyboard)
    await state.clear()


# ========== МОИ ОБЪЯВЛЕНИЯ ==========

@router.message(F.text == "📋 Мои объявления")
async def show_my_ads(message: Message):
    """Показ объявлений пользователя"""
    user_id = message.from_user.id
    
    if not await db.user_exists(user_id):
        await message.answer("❌ Сначала пройдите регистрацию: /start")
        return
    
    ads = await db.get_user_ads(user_id)
    
    if not ads:
        await message.answer(
            "📭 У вас пока нет объявлений.\n\n"
            "Нажмите **📢 Разместить объявление**, чтобы создать первое!",
            parse_mode="Markdown"
        )
        return
    
    await message.answer(
        f"📋 **Ваши объявления** ({len(ads)} шт.):\n\n"
        "Выберите объявление для управления:",
        reply_markup=my_ads_keyboard(ads),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "back_my_ads")
async def back_to_my_ads(callback: CallbackQuery):
    """Возврат к списку объявлений"""
    ads = await db.get_user_ads(callback.from_user.id)
    
    if not ads:
        await callback.message.edit_text("📭 У вас нет объявлений.")
        return
    
    await callback.message.edit_text(
        f"📋 **Ваши объявления** ({len(ads)} шт.):\n\n"
        "Выберите объявление для управления:",
        reply_markup=my_ads_keyboard(ads),
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("my_ad_"))
async def show_my_ad(callback: CallbackQuery):
    """Показ конкретного объявления"""
    ad_id = int(callback.data.replace("my_ad_", ""))
    ad = await db.get_ad(ad_id)
    
    if not ad:
        await callback.answer("❌ Объявление не найдено")
        return
    
    text = (
        f"📦 **{ad['title']}**\n\n"
        f"📝 {ad['description']}\n\n"
        f"💰 **Цена:** {ad['price']}\n"
        f"📂 **Категория:** {CATEGORIES.get(ad['category'], ad['category'])}\n"
        f"🖼 **Фото:** {len(ad.get('photos', []))} шт."
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=manage_ad_keyboard(ad_id),
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("edit_ad_"))
async def edit_ad_menu(callback: CallbackQuery):
    """Меню редактирования объявления"""
    ad_id = int(callback.data.replace("edit_ad_", ""))
    
    await callback.message.edit_text(
        "✏️ **Редактирование объявления**\n\n"
        "Выберите, что хотите изменить:",
        reply_markup=edit_ad_keyboard(ad_id),
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("edit_field_title_"))
async def edit_title_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования названия"""
    ad_id = int(callback.data.replace("edit_field_title_", ""))
    await state.update_data(editing_ad_id=ad_id)
    
    await callback.message.edit_text(
        "📌 Введите новое **название**:",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(EditAd.edit_title)


@router.message(EditAd.edit_title)
async def process_edit_title(message: Message, state: FSMContext):
    """Сохранение нового названия"""
    data = await state.get_data()
    ad_id = data['editing_ad_id']
    new_title = message.text.strip()
    
    if len(new_title) < 3 or len(new_title) > 100:
        await message.answer("❌ Название должно быть от 3 до 100 символов.")
        return
    
    await db.update_ad(ad_id, title=new_title)
    await message.answer("✅ Название обновлено!")
    
    # Показываем объявление заново
    ad = await db.get_ad(ad_id)
    text = (
        f"📦 **{ad['title']}**\n\n"
        f"📝 {ad['description']}\n\n"
        f"💰 **Цена:** {ad['price']}\n"
        f"📂 **Категория:** {CATEGORIES.get(ad['category'], ad['category'])}"
    )
    await message.answer(text, reply_markup=manage_ad_keyboard(ad_id), parse_mode="Markdown")
    await state.clear()


@router.callback_query(F.data.startswith("edit_field_desc_"))
async def edit_desc_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования описания"""
    ad_id = int(callback.data.replace("edit_field_desc_", ""))
    await state.update_data(editing_ad_id=ad_id)
    
    await callback.message.edit_text(
        "📝 Введите новое **описание**:",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(EditAd.edit_description)


@router.message(EditAd.edit_description)
async def process_edit_desc(message: Message, state: FSMContext):
    """Сохранение нового описания"""
    data = await state.get_data()
    ad_id = data['editing_ad_id']
    new_desc = message.text.strip()
    
    if len(new_desc) < 10 or len(new_desc) > 1000:
        await message.answer("❌ Описание должно быть от 10 до 1000 символов.")
        return
    
    await db.update_ad(ad_id, description=new_desc)
    await message.answer("✅ Описание обновлено!")
    
    ad = await db.get_ad(ad_id)
    text = (
        f"📦 **{ad['title']}**\n\n"
        f"📝 {ad['description']}\n\n"
        f"💰 **Цена:** {ad['price']}\n"
        f"📂 **Категория:** {CATEGORIES.get(ad['category'], ad['category'])}"
    )
    await message.answer(text, reply_markup=manage_ad_keyboard(ad_id), parse_mode="Markdown")
    await state.clear()


@router.callback_query(F.data.startswith("edit_field_price_"))
async def edit_price_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования цены"""
    ad_id = int(callback.data.replace("edit_field_price_", ""))
    await state.update_data(editing_ad_id=ad_id)
    
    await callback.message.edit_text(
        "💰 Введите новую **цену**:",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(EditAd.edit_price)


@router.message(EditAd.edit_price)
async def process_edit_price(message: Message, state: FSMContext):
    """Сохранение новой цены"""
    data = await state.get_data()
    ad_id = data['editing_ad_id']
    new_price = message.text.strip()
    
    if len(new_price) > 50:
        await message.answer("❌ Цена слишком длинная (макс. 50 символов).")
        return
    
    await db.update_ad(ad_id, price=new_price)
    await message.answer("✅ Цена обновлена!")
    
    ad = await db.get_ad(ad_id)
    text = (
        f"📦 **{ad['title']}**\n\n"
        f"📝 {ad['description']}\n\n"
        f"💰 **Цена:** {ad['price']}\n"
        f"📂 **Категория:** {CATEGORIES.get(ad['category'], ad['category'])}"
    )
    await message.answer(text, reply_markup=manage_ad_keyboard(ad_id), parse_mode="Markdown")
    await state.clear()


@router.callback_query(F.data.startswith("edit_field_photos_"))
async def edit_photos_start(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования фото"""
    ad_id = int(callback.data.replace("edit_field_photos_", ""))
    await state.update_data(editing_ad_id=ad_id, new_photos=[])
    
    await callback.message.edit_text(
        f"🖼 Отправьте новые фотографии (до {MAX_PHOTOS} шт.)\n"
        "Старые фото будут заменены.\n\n"
        "Нажмите **Готово** когда закончите.",
        reply_markup=done_photos_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(EditAd.edit_photos)


@router.message(EditAd.edit_photos, F.photo)
async def process_edit_photos(message: Message, state: FSMContext):
    """Обработка новых фото"""
    data = await state.get_data()
    photos = data.get('new_photos', [])
    
    if len(photos) >= MAX_PHOTOS:
        await message.answer(f"❌ Максимум {MAX_PHOTOS} фотографий.")
        return
    
    photo_id = message.photo[-1].file_id
    photos.append(photo_id)
    
    await state.update_data(new_photos=photos)
    await message.answer(
        f"✅ Фото добавлено ({len(photos)}/{MAX_PHOTOS})",
        reply_markup=done_photos_keyboard()
    )


@router.callback_query(EditAd.edit_photos, F.data == "photos_done")
async def edit_photos_done(callback: CallbackQuery, state: FSMContext):
    """Сохранение новых фото"""
    data = await state.get_data()
    ad_id = data['editing_ad_id']
    new_photos = data.get('new_photos', [])
    
    if not new_photos:
        await callback.answer("❌ Добавьте хотя бы одно фото!")
        return
    
    await db.update_ad(ad_id, photos=new_photos)
    await callback.message.edit_text("✅ Фотографии обновлены!")
    
    ad = await db.get_ad(ad_id)
    text = (
        f"📦 **{ad['title']}**\n\n"
        f"📝 {ad['description']}\n\n"
        f"💰 **Цена:** {ad['price']}\n"
        f"📂 **Категория:** {CATEGORIES.get(ad['category'], ad['category'])}\n"
        f"🖼 **Фото:** {len(ad.get('photos', []))} шт."
    )
    await callback.message.answer(text, reply_markup=manage_ad_keyboard(ad_id), parse_mode="Markdown")
    await state.clear()


# ========== УДАЛЕНИЕ ОБЪЯВЛЕНИЯ ==========

@router.callback_query(F.data.startswith("delete_ad_"))
async def delete_ad_confirm(callback: CallbackQuery):
    """Подтверждение удаления"""
    ad_id = int(callback.data.replace("delete_ad_", ""))
    
    await callback.message.edit_text(
        "⚠️ **Вы уверены, что хотите удалить это объявление?**\n\n"
        "Это действие нельзя отменить!",
        reply_markup=confirm_delete_keyboard(ad_id),
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("confirm_delete_"))
async def delete_ad_final(callback: CallbackQuery):
    """Удаление объявления"""
    ad_id = int(callback.data.replace("confirm_delete_", ""))
    
    await db.delete_ad(ad_id)
    await callback.message.edit_text("✅ Объявление удалено!")
    
    # Показываем список оставшихся объявлений
    ads = await db.get_user_ads(callback.from_user.id)
    
    if ads:
        await callback.message.answer(
            f"📋 **Ваши объявления** ({len(ads)} шт.):",
            reply_markup=my_ads_keyboard(ads),
            parse_mode="Markdown"
        )
    else:
        keyboard = main_menu_keyboard()
        if callback.from_user.id in ADMIN_IDS:
            from keyboards import admin_menu_keyboard
            keyboard = admin_menu_keyboard()
        await callback.message.answer("📭 Объявлений больше нет.", reply_markup=keyboard)