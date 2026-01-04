from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

import database as db
from states import Registration
from keyboards import main_menu_keyboard, admin_menu_keyboard, cancel_keyboard
from config import ADMIN_IDS

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработка команды /start"""
    await state.clear()
    user_id = message.from_user.id
    
    # Проверка блокировки
    if await db.is_user_blocked(user_id):
        await message.answer("🚫 Вы заблокированы и не можете использовать бот.")
        return
    
    # Проверка регистрации
    if await db.user_exists(user_id):
        user = await db.get_user(user_id)
        keyboard = admin_menu_keyboard() if user_id in ADMIN_IDS else main_menu_keyboard()
        await message.answer(
            f"👋 С возвращением, **{user['game_nick']}**!\n\n"
            "🎮 Это бот для торговли в Grand Mobile.\n"
            "Выберите действие:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "👋 **Добро пожаловать в Grand Mobile Market!**\n\n"
            "🎮 Здесь вы можете покупать и продавать игровое имущество.\n\n"
            "📝 Для начала нужно пройти регистрацию.\n\n"
            "🕹 Введите ваш **игровой ник**:",
            parse_mode="Markdown",
            reply_markup=cancel_keyboard()
        )
        await state.set_state(Registration.game_nick)


@router.message(Registration.game_nick)
async def process_game_nick(message: Message, state: FSMContext):
    """Обработка игрового ника"""
    game_nick = message.text.strip()
    
    if len(game_nick) < 2 or len(game_nick) > 32:
        await message.answer(
            "❌ Ник должен быть от 2 до 32 символов.\n"
            "Попробуйте снова:"
        )
        return
    
    await state.update_data(game_nick=game_nick)
    await message.answer(
        f"✅ Отлично, **{game_nick}**!\n\n"
        "📞 Теперь введите ваш **игровой номер (ID)**\n"
        "_(используется для связи с покупателями)_:",
        parse_mode="Markdown"
    )
    await state.set_state(Registration.game_id)


@router.message(Registration.game_id)
async def process_game_id(message: Message, state: FSMContext):
    """Обработка игрового ID"""
    game_id = message.text.strip()
    
    if len(game_id) < 1 or len(game_id) > 20:
        await message.answer(
            "❌ ID должен быть от 1 до 20 символов.\n"
            "Попробуйте снова:"
        )
        return
    
    data = await state.get_data()
    game_nick = data['game_nick']
    user_id = message.from_user.id
    username = message.from_user.username or ""
    
    # Сохранение в БД
    await db.add_user(user_id, username, game_nick, game_id)
    
    keyboard = admin_menu_keyboard() if user_id in ADMIN_IDS else main_menu_keyboard()
    
    await message.answer(
        f"🎉 **Регистрация завершена!**\n\n"
        f"🕹 Игровой ник: **{game_nick}**\n"
        f"📞 Игровой ID: **{game_id}**\n\n"
        "Теперь вы можете размещать и просматривать объявления!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await state.clear()


@router.callback_query(F.data == "cancel_create")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    """Отмена действия"""
    await state.clear()
    user_id = callback.from_user.id
    keyboard = admin_menu_keyboard() if user_id in ADMIN_IDS else main_menu_keyboard()
    
    await callback.message.edit_text("❌ Действие отменено.")
    await callback.message.answer(
        "📋 Главное меню:",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "back_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    user_id = callback.from_user.id
    keyboard = admin_menu_keyboard() if user_id in ADMIN_IDS else main_menu_keyboard()
    
    await callback.message.edit_text("📋 Главное меню:")
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=keyboard
    )