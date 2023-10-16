from aiogram import Bot


async def send_reminder(bot: Bot, chat_id: int, description: str):
    description = '<b>REMINDER!⚠️</b>\n' + description
    await bot.send_message(chat_id, text=description, parse_mode='html')
