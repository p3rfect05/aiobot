import datetime

from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, StatesGroup, State
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from sqlalchemy.ext.asyncio import async_sessionmaker
from models import UserModel, OrioksStudentsModel, OrioksGroupsModel
from external_services.orioks_api import get_orioks_token, BadHttpRequest, \
    get_student_info, get_group_id, get_group_timetable, get_week_type

router = Router()


class FSMOrioksLogIn(StatesGroup):
    acquire_token = State()

NO_LUNCH_DAYS = [3, 4] # only considered for my group at the moment, will be added custom set for different groups

@router.message(Command(commands='orioks_login'), StateFilter(default_state))
async def process_orioks_login(message: Message, session_maker: async_sessionmaker, state: FSMContext):
    async with session_maker.begin() as session:
        user = await session.get(UserModel, message.from_user.id)
        if not user.orioks_student:
            await state.set_state(FSMOrioksLogIn.acquire_token)
            await message.answer("Enter your login and password of ORIOKS account: [login] [password]")
        else:
            await message.answer("You are already logged in!")


@router.message(F.text, StateFilter(FSMOrioksLogIn.acquire_token), lambda message: len(message.text.split(' ')) == 2)
async def acquire_orioks_token(message: Message, session_maker: async_sessionmaker, state: FSMContext):
    login, password = message.text.split(' ')
    try:
        token = await get_orioks_token(login, password)
        student_info = await get_student_info(token)

        group = OrioksGroupsModel(group_id=student_info['group']) # noqa
        student = OrioksStudentsModel(group_fk=student_info['group'], user_fk=message.from_user.id, # noqa
                                      access_token=token, full_name=student_info['full_name']) # noqa
        async with session_maker.begin() as session:
            session.add(group)
            session.add(student)


        #print(f"Your token: {token}")
        await message.answer("You were logged in successfully!")
        await state.clear()
    except BadHttpRequest:
        await message.answer("Error occurred. Check your credentials and try again!")


@router.message(StateFilter(FSMOrioksLogIn.acquire_token))
async def process_invalid_credentials(message: Message):
    await message.answer("Invalid login and password. Try again.")


@router.message(Command(commands='today_class'), StateFilter(default_state))
async def process_today(message: Message, session_maker: async_sessionmaker):
    async with session_maker.begin() as session:
        user = await session.get(UserModel, message.from_user.id)
        if not user:
            await message.answer('You are not logged in ORIOKS!\nType /orioks_login to enable the timetable features')
        else:
            student = user.orioks_student
            stud_group, token = student.group.group_id, student.access_token
            #print(await get_week_type(token))
            time_table = await get_group_timetable(stud_group, token)
            today = datetime.datetime.today().weekday()
            time_table_message: str = ''
            #print(today, time_table.keys())
            week_type = await get_week_type(token)
            for day in time_table[week_type]:
                #print(subject, type(subject))
                time, class_order, class_type, class_name, class_cabinet, week_type, day_number = day
                if day_number == today + 1:
                    if type(time[0]) == list:
                        time = time[day_number in NO_LUNCH_DAYS]
                    if not time_table_message:
                        time_table_message = f'<b>{week_type}</b>\n'

                    subj_msg = '|'.join([f'{time[0]}-{time[1]}', f'{class_type} {class_name}',
                                         class_cabinet]) + '\n'
                    time_table_message += subj_msg

            if not time_table_message:
                await message.answer("You have <b>no</b> classes today!")
            else:
                await message.answer(time_table_message)




