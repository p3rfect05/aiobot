import aiohttp
import base64
import asyncio
from environs import Env

env: Env = Env()
env.read_env()
async def get_student_info():
    auth_token = env('ORIOKS_TOKEN')
    headers = {'Authorization' : f"Bearer {auth_token}",
              'Accept' : 'application/json',
              'User-Agent' : 'orioks_api_test/0.1 GNU/Linux 4.17.2-1-ARCH'}
    async with aiohttp.ClientSession() as session:
        async with session.get('https://orioks.miet.ru/api/v1/student', headers=headers) as response:
            result = await response.json()

    return result




    #async with aiohttp.ClientSession() as session:

#asyncio.run(get_token('8221664', 'q7ntx2Ge84'))