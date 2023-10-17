import datetime
from typing import Awaitable, Any, Dict, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from handlers.schedule_handlers import send_reminder
from models import UserModel, ReminderModel


class SchedulerMiddleware(BaseMiddleware):
    def __init__(self, scheduler: AsyncIOScheduler): # to load reminders set before the bot reboot
        self.scheduler = scheduler
        self.just_started = True
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery | Update,
            data: Dict[str, Any],
    ) -> Any:
        data['apscheduler'] = self.scheduler
        return await handler(event, data)