import asyncio
import os.path
import re

from aiogram.enums import ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State, default_state
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command, CommandStart, StateFilter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import selectinload

from models import UserModel, StorageModel
from external_services import get_student_info, doc_to_pdf_converter
from keyboards import create_inline_keyboard

router = Router()
FILES_PER_PAGE = 5


class FSMFileSaving(StatesGroup):
    acquire_file = State()


@router.message(CommandStart())
async def start_processing(message: Message, session_maker: async_sessionmaker):
    async with session_maker() as session:
        result = await session.get(UserModel, message.from_user.id)
        if not result:
            new_user = UserModel(user_id=message.from_user.id)  # noqa
            session.add(new_user)
            await session.commit()
    await message.answer('hello!')


@router.message(Command(commands=['get_orioks_info']))
async def get_orioks_info(message: Message):
    result = await get_student_info()
    str_res = ''
    for key, value in result.items():
        str_res += f'{key}:{value}\n'
    await message.answer(str_res)


# @router.message(F.document, lambda message: re.search(r'[.]doc|[.]docx', message.document.file_name))
# async def process_photo(message: Message, bot: Bot):
#     print(message.document.file_name)
#     ext = message.document.file_name.split('.')[-1]
#     file_info = await bot.get_file(message.document.file_id)
#     dest = os.path.abspath(f'external_services/new_image/{message.document.file_name}')
#     await bot.download_file(file_path=file_info.file_path, destination=dest)
#     convert(dest)
#     await bot.send_document(message.chat.id, document=FSInputFile(dest.replace(ext, 'pdf')))


@router.message(Command(commands='save'), StateFilter(default_state))
async def process_saving_file(message: Message, state: FSMContext):
    await message.answer('Send me your file!')
    await state.set_state(FSMFileSaving.acquire_file)


@router.message(F.content_type.in_(['photo', 'video', 'audio', 'document']), F.content_type.as_('file_type'),
                StateFilter(FSMFileSaving.acquire_file))
async def save_file(message: Message, state: FSMContext, session_maker: async_sessionmaker, file_type: str):
    file = list(filter(lambda x: x, [message.document, message.video, message.audio, message.photo]))[0]
    if file_type == ContentType.PHOTO:
        file_id = file[-1].file_id
        file_name = f'Photo #{file_id}'
    else:
        file_id = file.file_id
        file_name = file.file_name
    async with session_maker.begin() as session:
        new_file = StorageModel(file_id=file_id, file_type=file_type,  # noqa
                                file_name=file_name, user_fk=message.from_user.id)  # noqa
        session.add(new_file)
    await message.answer("File was saved!")
    await state.clear()


@router.message(StateFilter(FSMFileSaving.acquire_file))
async def invalid_type_save_file(message: Message):
    await message.answer("The type of the message is not supported")


@router.message(Command(commands='files'))
async def show_saved_files(message: Message):
    await message.answer("Choose a folder!",
                         reply_markup=create_inline_keyboard(1, **{'storage:photo:1': 'Photos',
                                                                   'storage:document:1': 'Documents',
                                                                   'storage:audio:1': 'Audios',
                                                                   'storage:video:1': 'Videos'}))


@router.callback_query(lambda callback: 'storage' in callback.data)
async def show_folder(callback: CallbackQuery, session_maker: async_sessionmaker):
    _, file_type, page = callback.data.split(':')
    page = int(page)
    async with session_maker.begin() as session:
        user = await session.get(UserModel, callback.from_user.id)
        files = user.files
        files = list(filter(lambda file: file.file_type == file_type, files))
        print(files)
        start = FILES_PER_PAGE * (page - 1)  # define files on the page
        display_files = files[start: start + FILES_PER_PAGE]
        buttons = {f'download:{file.id}:{file_type}': file.file_name for file in display_files}


        precise_pages = len(files) // FILES_PER_PAGE
        total_pages = precise_pages + 1 if len(files) % FILES_PER_PAGE else precise_pages
        if not total_pages: total_pages = 1
        forward_backward_buttons: list[InlineKeyboardButton] = []
        if page > 1:
            forward_backward_buttons.append(InlineKeyboardButton(text='<<',
                                                                 callback_data=f'storage:{file_type}:{page - 1}'))
        forward_backward_buttons.append(InlineKeyboardButton(text=f'{page}/{total_pages}',
                                                             callback_data=f'{page}/{total_pages}'))
        if start + FILES_PER_PAGE < len(files):
            forward_backward_buttons.append(InlineKeyboardButton(text='>>',
                                                                 callback_data=f'storage:{file_type}:{page + 1}'))
        keyboard = create_inline_keyboard(1, **buttons).inline_keyboard
        keyboard.append(forward_backward_buttons)

    await callback.message.edit_text(text='Choose a file!',
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))


@router.callback_query(lambda callback: 'download' in callback.data)
async def download_file(callback: CallbackQuery, session_maker: async_sessionmaker):
    _, file_id, file_type = callback.data.split(':')
    async with session_maker() as session:
        stmt = select(StorageModel).where(StorageModel.id == int(file_id))
        file = (await session.execute(stmt)).one()[0]
        print(file)
        tg_file_id = file.file_id

    if not tg_file_id:
        await callback.message.answer("File does not exist!")
    else:
        match file_type:
            case 'photo':
                await callback.message.answer_photo(tg_file_id)
            case 'document':
                await callback.message.answer_document(tg_file_id)
            case 'audio':
                await callback.message.answer_audio(tg_file_id)
            case 'video':
                await callback.message.answer_video(tg_file_id)
    await callback.message.delete()
    await callback.answer()