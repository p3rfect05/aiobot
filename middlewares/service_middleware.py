from typing import Awaitable, Any, Dict, Callable
from aiogram.types import Message, CallbackQuery

from aiogram import BaseMiddleware


class UserAllowanceMiddleware(BaseMiddleware):
    def __init__(self, admin_list: list):
        self.admin_list = admin_list
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: Dict[str, Any],
    ) -> Any:
        print(event.from_user.id)
        if event.from_user.id not in self.admin_list:
            await event.answer("Sorry, you are not in the admins\' list:(")
        else:
            return await handler(event, data)