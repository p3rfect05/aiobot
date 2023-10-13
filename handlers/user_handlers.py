import asyncio
import os.path
import re
from docx2pdf import convert
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.filters import Command, CommandStart
from external_services import get_student_info, doc_to_pdf_converter
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


@router.message(F.document, lambda message: re.search(r'[.]doc|[.]docx', message.document.file_name))
async def process_photo(message: Message, bot: Bot):
    print(message.document.file_name)
    ext = message.document.file_name.split('.')[-1]
    file_info = await bot.get_file(message.document.file_id)
    dest = os.path.abspath(f'external_services/new_image/{message.document.file_name}')
    await bot.download_file(file_path=file_info.file_path, destination=dest)
    convert(dest)
    await bot.send_document(message.chat.id, document=FSInputFile(dest.replace(ext, 'pdf')))

    #downloaded_photo = await bot.download_file(file_info.file_path)