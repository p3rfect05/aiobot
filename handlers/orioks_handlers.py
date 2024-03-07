import datetime


from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, StatesGroup, State
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from sqlalchemy.ext.asyncio import async_sessionmaker
from models import UserModel, OrioksStudentsModel, OrioksGroupsModel
from external_services.orioks_api import (
    get_orioks_token,
    BadHttpRequest,
    get_student_info,
    get_group_id,
    get_group_timetable,
    get_week_type,
    get_full_time_table,
)

router = Router()


class FSMOrioksLogIn(StatesGroup):
    acquire_token = State()


NO_LUNCH_DAYS = [
    3,
    4,
]  # only considered for my group at the moment, will be added custom set for different groups


@router.message(Command(commands="orioks_login"), StateFilter(default_state))
async def process_orioks_login(
    message: Message, session_maker: async_sessionmaker, state: FSMContext
):
    async with session_maker.begin() as session:
        user = await session.get(UserModel, message.from_user.id)
        if not user.orioks_student:
            await state.set_state(FSMOrioksLogIn.acquire_token)
            await message.answer(
                "Enter your login and password of ORIOKS account: [login] [password]"
            )
        else:
            await message.answer("You are already logged in!")


@router.message(
    F.text,
    StateFilter(FSMOrioksLogIn.acquire_token),
    lambda message: len(message.text.split(" ")) == 2,
)
async def acquire_orioks_token(
    message: Message, session_maker: async_sessionmaker, state: FSMContext
):
    login, password = message.text.split(" ")
    try:
        token = await get_orioks_token(login, password)
        student_info = await get_student_info(token)

        group = OrioksGroupsModel(group_id=student_info["group"])  # noqa
        student = OrioksStudentsModel(
            group_fk=student_info["group"],
            user_fk=message.from_user.id,  # noqa
            access_token=token,
            full_name=student_info["full_name"],
        )  # noqa
        async with session_maker.begin() as session:
            if not (await session.get(OrioksGroupsModel, student_info["group"])):
                session.add(group)
            session.add(student)

        # print(f"Your token: {token}")
        await message.answer("You were logged in successfully!")
        await state.clear()
    except BadHttpRequest:
        await message.answer("Error occurred. Check your credentials and try again!")


@router.message(StateFilter(FSMOrioksLogIn.acquire_token))
async def process_invalid_credentials(message: Message):
    await message.answer("Invalid login and password. Try again.")


@router.message(Command(commands="today_class"), StateFilter(default_state))
async def process_today(message: Message, session_maker: async_sessionmaker):
    human_week_days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    today = datetime.datetime.now().weekday()
    async with session_maker.begin() as session:
        user = await session.get(UserModel, message.from_user.id)
        student = user.orioks_student
        if not student:
            await message.answer(
                "You are not logged in ORIOKS!\nType /orioks_login to enable the timetable features"
            )
        else:
            time_table_messages, week_type = await get_full_time_table(student)
            if today + 1 not in time_table_messages:
                await message.answer("You have <b>no</b> classes today!")
            else:
                today_date = datetime.datetime.now()
                date = datetime.datetime(
                    today_date.year, today_date.month, today_date.day
                ).strftime("%d.%m.%Y")

                await message.answer(
                    f"<b>{human_week_days[today]} {date}\n{week_type}</b>"
                    + "".join(time_table_messages[today + 1])
                )


@router.message(Command(commands="now_class"), StateFilter(default_state))
async def process_current_class(message: Message, session_maker: async_sessionmaker):
    human_week_days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    today = datetime.datetime.now().weekday()
    async with session_maker.begin() as session:
        user = await session.get(UserModel, message.from_user.id)
        student = user.orioks_student
        if not student:
            await message.answer(
                "You are not logged in ORIOKS!\nType /orioks_login to enable the timetable features"
            )

        else:
            time_table_messages, week_type = await get_full_time_table(student)
            if today + 1 not in time_table_messages:
                await message.answer("You have <b>no</b> classes today!")
            else:
                today_date = datetime.datetime.now()
                date = datetime.datetime(
                    today_date.year, today_date.month, today_date.day
                ).strftime("%d.%m.%Y")
                answer: str = ""
                class_found = False
                for s_class in time_table_messages[today + 1]:

                    start, end = s_class.split("|")[0].split("-")
                    start_hours, start_minutes = map(int, start.split(":"))
                    end_hours, end_minutes = map(int, end.split(":"))

                    start_time, end_time = datetime.time(
                        start_hours, start_minutes
                    ), datetime.time(end_hours, end_minutes)
                    current_time = datetime.time(
                        datetime.datetime.now().hour, datetime.datetime.now().minute
                    )

                    if start_time <= current_time <= end_time:
                        answer = (
                            f"<b>{human_week_days[today]} {date}\n{week_type}</b>"
                            + s_class
                        )
                        class_found = True
                        await message.answer(answer)

                    if not answer:
                        next_class_time = datetime.datetime.combine(
                            datetime.date(1, 1, 1), current_time
                        ) + datetime.timedelta(minutes=40)
                        if start_time <= next_class_time.time() <= end_time:
                            answer = (
                                "No class at the moment. Next class is:\n"
                                + f"<b>{human_week_days[today]} {date}\n{week_type}</b>"
                                + s_class
                            )
                            class_found = True
                            await message.answer(answer)

                if not class_found:
                    answer = (
                        f"<b>{human_week_days[today]} {date}\n{week_type}</b>"
                        + "No class at the moment!"
                    )
                    await message.answer(answer)


@router.message(Command(commands="week_class"), StateFilter(default_state))
async def process_current_week(message: Message, session_maker: async_sessionmaker):
    human_week_days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    today = datetime.datetime.now().weekday()
    async with session_maker.begin() as session:
        user = await session.get(UserModel, message.from_user.id)
        student = user.orioks_student
        if not student:
            await message.answer(
                "You are not logged in ORIOKS!\nType /orioks_login to enable the timetable features"
            )
        else:
            time_table_messages, week_type = await get_full_time_table(student)
            full_time_table_message: str = ""
            full_time_table_message += week_type
            today_date = datetime.datetime.now()
            for day in time_table_messages:
                day_date = datetime.datetime(
                    today_date.year,
                    today_date.month,
                    today_date.day - today_date.weekday() + day - 1,
                )
                week_day = human_week_days[day_date.weekday()]
                full_time_table_message += (
                    f'<b>{week_day} {day_date.strftime("%d.%m.%Y")}</b>\n'
                )
                for s_class in time_table_messages[day]:
                    full_time_table_message += s_class

            await message.answer(full_time_table_message)
