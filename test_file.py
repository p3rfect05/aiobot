import aiohttp
import asyncio

async def send_post_request():
    # Заголовки для запроса
    headers = {'Content-Type': 'application/json', 'User-Agent': 'my-app/0.0.1'}

    # Инициализация сессии
    async with aiohttp.ClientSession() as session:
        # Отправка POST-запроса с JSON и заголовками
        response = await session.post('https://httpbin.org/post', json={'key': 'value'}, headers=headers)

        # Чтение ответа как текст
        text_response = await response.text()
        print("Text Response:", text_response)

        # Чтение ответа как JSON
        json_response = await response.json()
        print("JSON Response:", json_response)

# Запуск асинхронной функции
asyncio.run(send_post_request())