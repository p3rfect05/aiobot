import asyncio
from config_data.config import load_config, Config
from aiogram import Dispatcher, Bot
from handlers import user_handlers
from middlewares import service_middleware

async def main():
    config: Config = load_config()

    bot: Bot = Bot(token=config.tg_bot.token)
    admin_list: list = config.tg_bot.admin_ids
    dp = Dispatcher(bot=bot)
    dp.message.middleware.register(service_middleware.UserAllowanceMiddleware(admin_list))
    dp.include_router(user_handlers.router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())