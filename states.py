from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    """Состояния регистрации"""
    game_nick = State()
    game_id = State()


class CreateAd(StatesGroup):
    """Состояния создания объявления"""
    title = State()
    description = State()
    price = State()
    category = State()
    photos = State()
    confirm = State()


class EditAd(StatesGroup):
    """Состояния редактирования объявления"""
    select_ad = State()
    select_field = State()
    edit_title = State()
    edit_description = State()
    edit_price = State()
    edit_photos = State()


class EditProfile(StatesGroup):
    """Состояния редактирования профиля"""
    edit_nick = State()
    edit_game_id = State()


class ViewAds(StatesGroup):
    """Состояния просмотра объявлений"""
    browsing = State()


class AdminStates(StatesGroup):
    """Состояния админ-панели"""
    broadcast_message = State()
    block_user_id = State()
    view_ads = State()


class ContactSeller(StatesGroup):
    """Состояние отправки сообщения продавцу"""
    message = State()