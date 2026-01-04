from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
from states import AdminStates
from keyboards import admin_panel_keyboard, cancel_keyboard, admin_ad_keyboard, admin_menu_keyboard
from config import ADMIN_IDS, CATEGORIES

router = Router()


def is_admin(user_id: int) -> bool:
    """Проверка прав администратора"""
    return user_id in ADMIN_IDS


@router.message(F.text == "🔧 Админ-панель")
async def admin_panel(message: Message):
    """Открытие админ-панели"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён!")
        return
    
    await message.answer(
        "🔧 **Панель администратора**\n\n"
        "Выберите действие:",
        reply_markup=admin_panel_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.edit_text("📋 Главное меню:")
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=admin_menu_keyboard()
    )


# ========== ПОЛЬЗОВАТЕЛИ ==========

@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    """Список всех пользователей"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён!")
        return
    
    users = await db.get_all_users()
    
    if not users:
        await callback.answer("Пользователей нет")
        return
    
    text = "👥 **Список пользователей:**\n\n"
    
    for user in users[:50]:  # Ограничиваем 50 пользователями
        status = "🚫" if user['is_blocked'] else "✅"
        text += (
            f"{status} ID: `{user['telegram_id']}`\n"
            f"   Ник: {user['game_nick']} | Игр.ID: {user['game_id']}\n\n"
        )
    
    if len(users) > 50:
        text += f"_...и ещё {len(users) - 50} пользователей_"
    
    text += f"\n\n📊 **Всего:** {len(users)} пользователей"
    
    await callback.message.edit_text(
        text,
        reply_markup=admin_panel_keyboard(),
        parse_mode="Markdown"
    )


# ========== ОБЪЯВЛЕНИЯ ==========

@router.callback_query(F.data == "admin_ads")
async def admin_ads(callback: CallbackQuery, state: FSMContext):
    """Список всех объявлений"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён!")
        return
    
    ads = await db.get_all_ads()
    
    if not ads:
        await callback.message.edit_text(
            "📭 Объявлений нет.",
            reply_markup=admin_panel_keyboard()
        )
        return
    
    await state.update_data(admin_ads=ads, admin_ads_page=0)
    await show_admin_ad(callback, state)


async def show_admin_ad(callback: CallbackQuery, state: FSMContext):
    """Показ объявления для админа"""
    data = await state.get_data()
    ads = data['admin_ads']
    page = data['admin_ads_page']
    
    if page >= len(ads):
        page = 0
        await state.update_data(admin_ads_page=0)
    
    ad = ads[page]
    
    text = (
        f"📋 **Объявление #{ad['id']}** ({page + 1}/{len(ads)})\n\n"
        f"📦 **{ad['title']}**\n"
        f"📝 {ad['description']}\n\n"
        f"💰 Цена: {ad['price']}\n"
        f"📂 Категория: {CATEGORIES.get(ad['category'], ad['category'])}\n\n"
        f"👤 Продавец: {ad['game_nick']}\n"
        f"📞 Игр.ID: {ad['game_id']}\n"
        f"🆔 TG ID: `{ad['seller_id']}`"
    )
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    
    # Навигация
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data="admin_prev_ad"))
    nav_buttons.append(InlineKeyboardButton(text=f"{page + 1}/{len(ads)}", callback_data="admin_current"))
    if page < len(ads) - 1:
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data="admin_next_ad"))
    
    builder.row(*nav_buttons)
    builder.row(InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin_delete_ad_{ad['id']}"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel_back"))
    
    await callback.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "admin_next_ad")
async def admin_next_ad(callback: CallbackQuery, state: FSMContext):
    """Следующее объявление"""
    data = await state.get_data()
    page = data.get('admin_ads_page', 0) + 1
    await state.update_data(admin_ads_page=page)
    await show_admin_ad(callback, state)


@router.callback_query(F.data == "admin_prev_ad")
async def admin_prev_ad(callback: CallbackQuery, state: FSMContext):
    """Предыдущее объявление"""
    data = await state.get_data()
    page = max(0, data.get('admin_ads_page', 0) - 1)
    await state.update_data(admin_ads_page=page)
    await show_admin_ad(callback, state)


@router.callback_query(F.data.startswith("admin_delete_ad_"))
async def admin_delete_ad(callback: CallbackQuery, state: FSMContext):
    """Удаление объявления админом"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён!")
        return
    
    ad_id = int(callback.data.replace("admin_delete_ad_", ""))
    await db.delete_ad(ad_id)
    await callback.answer("✅ Объявление удалено!")
    
    # Обновляем список
    ads = await db.get_all_ads()
    if ads:
        await state.update_data(admin_ads=ads, admin_ads_page=0)
        await show_admin_ad(callback, state)
    else:
        await callback.message.edit_text(
            "📭 Объявлений больше нет.",
            reply_markup=admin_panel_keyboard()
        )


@router.callback_query(F.data == "admin_panel_back")
async def admin_panel_back(callback: CallbackQuery, state: FSMContext):
    """Возврат в админ-панель"""
    await state.clear()
    await callback.message.edit_text(
        "🔧 **Панель администратора**\n\n"
        "Выберите действие:",
        reply_markup=admin_panel_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "admin_current")
async def admin_current(callback: CallbackQuery):
    """Заглушка для кнопки номера страницы"""
    await callback.answer()


# ========== БЛОКИРОВКА ==========

@router.callback_query(F.data == "admin_block")
async def admin_block_start(callback: CallbackQuery, state: FSMContext):
    """Начало блокировки пользователя"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён!")
        return
    
    await callback.message.edit_text(
        "🚫 Введите **Telegram ID** пользователя для блокировки:",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(AdminStates.block_user_id)
    await state.update_data(block_action="block")


@router.callback_query(F.data == "admin_unblock")
async def admin_unblock_start(callback: CallbackQuery, state: FSMContext):
    """Начало разблокировки пользователя"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён!")
        return
    
    await callback.message.edit_text(
        "✅ Введите **Telegram ID** пользователя для разблокировки:",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(AdminStates.block_user_id)
    await state.update_data(block_action="unblock")


@router.message(AdminStates.block_user_id)
async def process_block_user(message: Message, state: FSMContext):
    """Обработка блокировки/разблокировки"""
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите корректный числовой ID")
        return
    
    user = await db.get_user(user_id)
    if not user:
        await message.answer("❌ Пользователь не найден в базе")
        await state.clear()
        return
    
    data = await state.get_data()
    action = data.get('block_action', 'block')
    
    if action == "block":
        await db.block_user(user_id, block=True)
        await message.answer(f"🚫 Пользователь `{user_id}` ({user['game_nick']}) заблокирован!", parse_mode="Markdown")
    else:
        await db.block_user(user_id, block=False)
        await message.answer(f"✅ Пользователь `{user_id}` ({user['game_nick']}) разблокирован!", parse_mode="Markdown")
    
    await message.answer(
        "🔧 **Панель администратора**",
        reply_markup=admin_panel_keyboard(),
        parse_mode="Markdown"
    )
    await state.clear()


# ========== РАССЫЛКА ==========

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    """Начало рассылки"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён!")
        return
    
    await callback.message.edit_text(
        "📢 Введите **сообщение для рассылки** всем пользователям:",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(AdminStates.broadcast_message)


@router.message(AdminStates.broadcast_message)
async def process_broadcast(message: Message, state: FSMContext, bot: Bot):
    """Отправка рассылки"""
    broadcast_text = message.text
    users = await db.get_all_users()
    
    success = 0
    failed = 0
    
    status_msg = await message.answer("📤 Начинаю рассылку...")
    
    for user in users:
        if user['is_blocked']:
            continue
        
        try:
            await bot.send_message(
                user['telegram_id'],
                f"📢 **Объявление от администрации:**\n\n{broadcast_text}",
                parse_mode="Markdown"
            )
            success += 1
        except Exception:
            failed += 1
    
    await status_msg.edit_text(
        f"✅ **Рассылка завершена!**\n\n"
        f"📨 Успешно: {success}\n"
        f"❌ Не доставлено: {failed}",
        parse_mode="Markdown"
    )
    
    await message.answer(
        "🔧 **Панель администратора**",
        reply_markup=admin_panel_keyboard(),
        parse_mode="Markdown"
    )
    await state.clear()