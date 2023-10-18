# import datetime
# from copy import deepcopy
#
# import aiohttp
# import asyncio
# from environs import Env
#
# env: Env = Env()
# env.read_env()
# base_url = 'https://orioks.miet.ru'
# base_headers = {'Authorization' : f'Bearer {env("ORIOKS_TOKEN")}', 'Accept': 'application/json'}
# time_table = {
#     "1": ["09:00", "10:20"],
#     "2": ["10:30", "11:50"],
#     "3": [["12:00", "13:20"],["12:30", "13:50"]],
#     "4": ["14:00", "15:20"],
#     "5": ["15:30", "16:50"],
#     "6": ["17:00", "18:20"],
#     "7": ["18:30", "19:50"],
#     "8" : ["20:00", "21:20"]
# }
#
#
# class GroupNotExists(BaseException):
#     pass
#
#
# async def get_week_type():
#     async with aiohttp.ClientSession() as session:
#         async with session.get(base_url + '/api/v1/schedule', headers=base_headers) as response:
#             json_response = await response.json()
#             semester_start = datetime.datetime.fromisoformat(json_response['semester_start'])
#             timedelta = datetime.datetime.now() - semester_start
#             current_week = (timedelta.days // 7) + 1
#             n = (current_week - 1) % 4
#             print(n)
#
#
# async def get_group_timetable(student_group: str) -> list:
#     full_time_table = []
#     group_id = await get_group_id(student_group)
#     if group_id == -1:
#         raise GroupNotExists
#     method_url = f'/api/v1/schedule/groups/{group_id}'
#     async with aiohttp.ClientSession() as session:
#         async with session.get(url=base_url+method_url, headers=base_headers) as response:
#             day_timetable = await response.json()
#     sorted_timetable = sorted(day_timetable,
#                               key= lambda subject: (subject['week'], subject['day'], subject['class']))
#     for index, item in enumerate(sorted_timetable):
#         if '2 пары' in item['name']:
#             item['name'] = item['name'].replace(' (2 пары)', '')
#             second_item = deepcopy(item)
#             second_item['class'] = item['class'] + 1
#             sorted_timetable[index:index + 1] = [item, second_item]
#
#     previous_week = ''
#     previous_day = -1
#     for item in sorted_timetable:
#         type_of_week = f'знаменатель' if item['week'] % 2 else f'числитель'
#         number_of_type_of_week = 'I' if item['week'] < 2 else 'II'
#         week_and_number = number_of_type_of_week + ' ' + type_of_week
#         day = item['day']
#
#         if week_and_number != previous_week:
#             previous_week = week_and_number
#             print(week_and_number)
#         if day != previous_day:
#             previous_day = day
#             print(f'{day + 1} день: ')
#         class_information = [time_table[str(item["class"])], item["class"],
#                              item['type'], item['name'], item['location'], week_and_number, day + 1]
#         #print(f'{item["class"]} пара: ', item['name'], item['type'], item['location'])
#         print(class_information)
#         full_time_table.append(class_information)
#
#     return full_time_table
#
#
# async def get_group_id(student_group: str) -> int:
#     method_url = '/api/v1/schedule/groups'
#     async with aiohttp.ClientSession() as session:
#         async with session.get(url=base_url+method_url, headers=base_headers) as response:
#             groups = await response.json()
#             for group in groups:
#                 if student_group.lower() == group['name'].split(' ')[0].lower():
#                     print(group['name'], group['id'])
#                     return group['id']
#     return -1
#
# asyncio.run(get_group_timetable('пм-21'))