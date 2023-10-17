import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from deep_translator import GoogleTranslator
from sqlalchemy import URL

from config_data.config import load_config, Config
from config_data import get_session_maker
from aiogram import Dispatcher, Bot

from config_data.config_functions import load_reminders
from handlers import user_handlers, vk_api_handlers
from middlewares import service_middleware, schedule_middleware
from external_services import page_preview

async def main():
    config: Config = load_config()

    bot: Bot = Bot(token=config.tg_bot.token, parse_mode='html')
    admin_list: list = config.tg_bot.admin_ids

    dp = Dispatcher(bot=bot)

    scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
    scheduler.start() ### need to fix loading of reminders set before the bot's reboot!!!
    dp.update.middleware.register(schedule_middleware.SchedulerMiddleware(scheduler))
    dp.message.middleware.register(service_middleware.UserAllowanceMiddleware(admin_list))

    dp.include_routers(user_handlers.router, page_preview.router, vk_api_handlers.router)

    postgres_engine_url: URL = URL.create(
        drivername='postgresql+asyncpg',
        username=config.db.db_user,
        host=config.db.db_host,
        database=config.db.database,
        port=config.db.db_port,
        password=config.db.db_password
    )
    session_maker = get_session_maker(postgres_engine_url)
    await load_reminders(session_maker, scheduler, bot)
    en_to_ru_translator = GoogleTranslator(source='en', target='ru')
    ru_to_en_translator = GoogleTranslator(source='ru', target='en')
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, session_maker=session_maker,
                           en_to_ru_translator=en_to_ru_translator, ru_to_en_translator=ru_to_en_translator)

if __name__ == '__main__':
    asyncio.run(main())