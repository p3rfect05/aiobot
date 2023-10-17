import datetime

import asyncio
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from handlers.schedule_handlers import send_reminder
from models import ReminderModel, UserModel

#, chat_id: int, user_id: int,
                        # scheduler: AsyncIOScheduler, bot: Bot
async def load_reminders(session_maker: async_sessionmaker,
                         scheduler: AsyncIOScheduler, bot: Bot):
    async with session_maker.begin() as session:
        stmt = select(UserModel)
        users = await session.execute(stmt)
        for user in users.scalars().all():
            user: UserModel
            reminders = user.reminders
            for reminder in reminders:
                reminder: ReminderModel
                time_triggers = reminder.time_triggers
                if datetime.datetime.now() <= time_triggers:
                    rem_type, rem_desc = reminder.reminder_type, reminder.reminder_desc
                    scheduler.add_job(send_reminder, trigger=rem_type, run_date=time_triggers,
                                           kwargs={'bot': bot,
                                                   'chat_id': user.user_id,
                                                   'description': rem_desc})

