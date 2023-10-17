import asyncio
import datetime
import os.path
import re

from aiogram.enums import ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State, default_state
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command, CommandStart, StateFilter, CommandObject
from deep_translator import GoogleTranslator
from docx2pdf import convert
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import async_sessionmaker
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram3_calendar import simple_cal_callback
from external_services.simple_calendar import SimpleCalendar
from models import UserModel, StorageModel, ReminderModel
from external_services import get_student_info, doc_to_pdf_converter
from keyboards import create_inline_keyboard
from services import *
from .schedule_handlers import *
router = Router()
FILES_PER_PAGE = 5


class FSMFileSaving(StatesGroup):
    acquire_file = State()

class FSMReminder(StatesGroup):
    choose_date = State()
    choose_time = State()
    set_description = State()
@router.message(CommandStart(), StateFilter(default_state))
async def start_processing(message: Message, session_maker: async_sessionmaker):
    async with session_maker() as session:
        result = await session.get(UserModel, message.from_user.id)
        if not result:
            new_user = UserModel(user_id=message.from_user.id)  # noqa
            session.add(new_user)
            await session.commit()
    await message.answer('hello!')


@router.message(Command(commands=['get_orioks_info']), StateFilter(default_state))
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


@router.message(Command(commands='files'), StateFilter(default_state))
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
        buttons.update({'choose_delete_file' : 'Delete file'})
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


@router.callback_query(F.data == 'choose_delete_file') # ❌
async def choose_file_to_delete(callback: CallbackQuery):
    keyboard = callback.message.reply_markup.inline_keyboard
    for i in keyboard:
        for j in i:
            if 'download' in j.callback_data:
                j.text = '❌' + j.text
                j.callback_data = j.callback_data.replace('download', 'delete')
    await callback.message.edit_text(text='Choose file to delete',
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))


@router.callback_query(lambda callback: 'delete' in callback.data)
async def delete_file(callback: CallbackQuery, session_maker: async_sessionmaker):
    _, file_id, _ = callback.data.split(':')
    try:
        async with session_maker() as session:
            stmt = delete(StorageModel).where(StorageModel.id == int(file_id))
            await session.execute(stmt)
            await session.commit()
        await callback.answer(text='File was successfully deleted!')
    except:
        await callback.message.answer("Nothing to delete! (must be a bug then! report pls.)")
    await callback.answer()
    await callback.message.delete()


@router.message(Command(commands='calendar'), StateFilter(default_state))
async def display_calendar(message: Message, state: FSMContext):
    await message.answer("Please select a date: ", reply_markup=await SimpleCalendar().start_calendar())
    await state.set_state(FSMReminder.choose_date)

@router.callback_query(simple_cal_callback.filter(), StateFilter(FSMReminder.choose_date))
async def process_date_selection(callback: CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(callback, callback_data)

    if selected and check_reminder_date(date):
        await callback.message.delete()
        # await callback.message.answer(
        #     f'You selected {date.strftime("%d/%m/%Y")}',
        # )
        await callback.message.answer("Now enter time in the 24h format(for example 19:30)")
        await state.set_state(FSMReminder.choose_time)
        await state.update_data({'date' : date})
    elif selected:
        await callback.answer(show_alert=True, text='You cannot set the reminder in the past')

@router.message(F.text, StateFilter(FSMReminder.choose_time))
async def process_time_selection(message: Message, state: FSMContext):
    text = message.text.split(':')
    try:
        hours, minutes = int(text[0]), int(text[1])
        date = (await state.get_data())['date']
        if check_reminder_time(hours, minutes, date):
            await message.answer(f"Now set the description for the reminder (not exceeding 100 symbols)")
            await state.update_data({'time' : [hours, minutes]})
            await state.set_state(FSMReminder.set_description)
        else:
            raise ValueError
    except ValueError:
        await message.answer('Invalid format for the time (or you set the reminder in the past)!')

@router.message(F.text.as_('desc'), F.text.len() < 100, StateFilter(FSMReminder.set_description))
async def process_desc_setting(message: Message, state: FSMContext, session_maker: async_sessionmaker,
                               desc: str, bot: Bot, apscheduler: AsyncIOScheduler):
    date: datetime.datetime = (await state.get_data())['date']
    hours, minutes = (await state.get_data())['time']
    await message.answer(f"Reminder:{message.text}\nSet on <b><i>{date.strftime('%d/%m/%Y')}</i></b>, "
                         f"at <b><i>{str(hours).rjust(2, '0')}:{str(minutes).rjust(2, '0')}</i></b> set successfully!")
    date_with_time = date.replace(hour=hours, minute=minutes)
    async with session_maker.begin() as session:
        new_reminder = ReminderModel(reminder_type='date', reminder_desc=desc, # noqa
                                     user_fk = message.from_user.id, time_triggers=date_with_time) # noqa
        session.add(new_reminder)
    apscheduler.add_job(send_reminder, trigger='date', run_date=date_with_time,
                      kwargs={'bot' : bot, 'chat_id' : message.chat.id, 'description' : desc})
    await state.clear()


@router.message(StateFilter(FSMReminder.set_description))
async def process_invalid_desc_setting(message: Message):
    await message.answer("Invalid description: it must be a string not exceeding 100 symbols!")


@router.message(F.text, Command(commands='to_rus'))
async def translate_text(message: Message, command: CommandObject, en_to_ru_translator: GoogleTranslator):
    text = command.args
    if not text:
        await message.answer("Text to translate should not be <b>empty</b>.")
    else:
        translated = en_to_ru_translator.translate(text)
        await message.answer(translated)

@router.message(F.text, Command(commands='to_eng'))
async def translate_text(message: Message, command: CommandObject, ru_to_en_translator: GoogleTranslator):
    text = command.args
    if not text:
        await message.answer("Text to translate should not be <b>empty</b>.")
    else:
        translated = ru_to_en_translator.translate(text)
        await message.answer(translated)
