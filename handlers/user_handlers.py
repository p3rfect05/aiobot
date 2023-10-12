import asyncio

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command, CommandStart
from external_services import get_student_info
import json


router = Router()
@router.message(CommandStart())
async def start_processing(message: Message):
    await message.answer('hello!')

@router.message(Command(commands=['get_orioks_info']))
async def get_orioks_info(message: Message):
    result = await get_student_info()
    str_res = ''
    for key, value in result.items():
        str_res += f'{key}:{value}\n'
    await message.answer(str_res)