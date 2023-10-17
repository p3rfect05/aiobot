import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from external_services import vk_api
from aiogram.fsm.state import State, StatesGroup, default_state
from keyboards import create_inline_keyboard, create_link_inline_keyboard
router = Router()



class FSMVKLogin(StatesGroup):
    acquire_token = State()


@router.message(Command(commands=['vk_auth']), StateFilter(default_state))
async def process_vk_auth(message: Message, state: FSMContext):
    auth_link: str = vk_api.get_vk_auth_link()
    await message.answer(text='<b>Click the link to authorize:</b>',
                         reply_markup=create_link_inline_keyboard(1, **{'Authorize' : auth_link}))
    await state.set_state(FSMVKLogin.acquire_token)

@router.message(StateFilter(FSMVKLogin.acquire_token), lambda message: 'access_token' in message.text)
async def process_vk_token(message: Message, state: FSMContext):
    access_token = re.search(r'access_token=(?P<access_token>.+?)&', message.text)['access_token']
    await message.answer('Your VK token was saved!')
    await state.clear()

@router.message(StateFilter(FSMVKLogin.acquire_token))
async def process_vk_token(message: Message, state: FSMContext):
    await message.answer("Given string does not contain access_token")

