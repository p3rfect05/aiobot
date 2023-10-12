import json
from aiogram import Router, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, InputFile, FSInputFile
from aiogram.filters import Command, CommandObject
import aiohttp
from aiohttp_socks import ProxyType, ProxyConnector
from environs import Env
from html2image import Html2Image


router = Router()


env: Env = Env()
env.read_env()


BAN_IMAGE_SECRET_KEY = env('BAN_IMAGE_SECRET_KEY')
service_url = 'https://api.imageban.ru/v1'

#UNDER CONSTRUCTION
# async def use_proxy(page_url, enable_proxy=False):
#     proxy_connector: ProxyConnector | None = None
#     if enable_proxy:
#         proxy_host = '37.19.220.129'
#         proxy_port = '8443'
#         proxy_connector = ProxyConnector(proxy_type=ProxyType.HTTP,
#                                          host=proxy_host, port=proxy_port)
#
#
#     headers = {"User-Agent": getuseragent.UserAgent("desktop+chrome").Random()}
#     async with aiohttp.ClientSession(connector=proxy_connector) as session:
#         async with session.get(page_url, headers=headers) as response:
#             print(headers)
#             html = await response.text()
#     return html

@router.message(Command(commands=['screenshot']))
async def upload_and_get_picture(message: Message, command: CommandObject, bot: Bot):
    hti = Html2Image(size=(1200, 1200), output_path='external_services/temp_pictures')
    command_args = command.args.split(' ')
    page_url = command_args[0]
    hti.screenshot(url=page_url, save_as='temp.png')
    photo_url = 'external_services/temp_pictures/temp.png'
    try:
        await bot.send_photo(chat_id=message.chat.id, photo=FSInputFile(photo_url))
    except TelegramBadRequest:
        await message.answer("Invalid URL")

