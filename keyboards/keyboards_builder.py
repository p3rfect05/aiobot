from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def create_link_inline_keyboard(width: int, *args: str, **kwargs: str) -> InlineKeyboardMarkup:
    kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    buttons: list[InlineKeyboardButton] = []

    if args:
        for url in args:
            buttons.append(InlineKeyboardButton(text=url, url=url))
    if kwargs:
        for text, url in kwargs.items():
            buttons.append(InlineKeyboardButton(text=text, url=url))

    kb_builder.row(*buttons)

    return kb_builder.as_markup(resize_keyboard=True)


def create_inline_keyboard(width: int, *args: str, **kwargs: str) -> InlineKeyboardMarkup:
    kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()

    buttons: list[InlineKeyboardButton] = []

    if args:
        for button in args:
            buttons.append(InlineKeyboardButton(text=button, callback_data=button))
    if kwargs:
        for button, text in kwargs.items():
            buttons.append(InlineKeyboardButton(text=text, callback_data=button))

    kb_builder.row(*buttons)

    return kb_builder.as_markup(resize_keyboard=True)


