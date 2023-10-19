import base64
import datetime
from copy import deepcopy
import aiohttp
import asyncio
from environs import Env

from models import OrioksStudentsModel

env: Env = Env()
env.read_env()
base_url = 'https://orioks.miet.ru'
#base_headers = {'Authorization' : f'Bearer orioks_token', 'Accept': 'application/json'}
time_table = {
    "1": ["09:00", "10:20"],
    "2": ["10:30", "11:50"],
    "3": [["12:30", "13:50"], ["12:00", "13:20"]],
    "4": ["14:00", "15:20"],
    "5": ["15:30", "16:50"],
    "6": ["17:00", "18:20"],
    "7": ["18:30", "19:50"],
    "8" : ["20:00", "21:20"]
}

NO_LUNCH_DAYS = [3, 4] # only considered for my group at the moment, will be added custom set for different groups


class GroupNotExists(BaseException):
    pass


class BadHttpRequest(BaseException):
    pass


async def get_orioks_token(login, password) -> str:
    method_url = '/api/v1/auth'
    b = base64.b64encode(bytes(f'{login}:{password}', 'utf-8'))  # bytes
    token = b.decode('utf-8')  # convert bytes to string
    headers = {'Authorization': f'Basic {token}', 'Accept': 'application/json'}
    async with aiohttp.ClientSession() as session:
        async with session.get(base_url + method_url, headers=headers) as response:
            print(await response.json())
            if response.status == 200:
                return (await response.json())['token']
            else:
                raise BadHttpRequest


async def get_student_info(token: str):
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    method_url = '/api/v1/student'
    async with aiohttp.ClientSession() as session:
        async with session.get(base_url + method_url, headers=headers) as response:
            result = await response.json()

    return result


async def get_group_timetable(student_group: str, token: str) -> dict:
    headers = {'Authorization' : f'Bearer {token}', 'Accept' : 'application/json'}
    full_time_table: dict = {}
    group_id = await get_group_id(student_group, token)
    if group_id == -1:
        raise GroupNotExists
    method_url = f'/api/v1/schedule/groups/{group_id}'
    async with aiohttp.ClientSession() as session:
        async with session.get(url=base_url + method_url, headers=headers) as response:
            day_timetable = await response.json()
    sorted_timetable = sorted(day_timetable,
                              key=lambda subject: (subject['week'], subject['day'], subject['class']))
    for index, item in enumerate(sorted_timetable):
        if '2 пары' in item['name']:
            item['name'] = item['name'].replace(' (2 пары)', '')
            second_item = deepcopy(item)
            second_item['class'] = item['class'] + 1
            sorted_timetable[index:index + 1] = [item, second_item]

    # previous_week = ''
    # previous_day = -1
    for item in sorted_timetable:
        type_of_week = f'знаменатель' if item['week'] % 2 else f'числитель'
        number_of_type_of_week = 'I' if item['week'] < 2 else 'II'
        week_and_number = number_of_type_of_week + ' ' + type_of_week
        day = item['day']

        # if week_and_number != previous_week:
        #     previous_week = week_and_number
        #     print(week_and_number)
        # if day != previous_day:
        #     previous_day = day
        #     print(f'{day + 1} день: ')
        class_information = [time_table[str(item["class"])], item["class"],
                             item['type'], item['name'], item['location'], week_and_number, day + 1]
        week_type = item['week']
        if week_type in full_time_table:
            full_time_table[week_type].append(class_information)
        else:
            full_time_table[week_type] = [class_information]
        # print(f'{item["class"]} пара: ', item['name'], item['type'], item['location'])
        #print(class_information)

    return full_time_table


async def get_group_id(student_group: str, token: str) -> int:
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    method_url = '/api/v1/schedule/groups'
    async with aiohttp.ClientSession() as session:
        async with session.get(url=base_url + method_url, headers=headers) as response:
            groups = await response.json()
            for group in groups:
                if student_group.lower() in group['name'].split(' ')[0].lower():
                    print(group['name'], group['id'])
                    return group['id']
    return -1


async def get_week_type(token: str):
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    method_url = '/api/v1/schedule'
    async with aiohttp.ClientSession() as session:
        async with session.get(url=base_url + method_url, headers=headers) as response:
            semester_start = (await response.json())['semester_start']
            print(semester_start)

    semester_start = datetime.datetime.fromisoformat(semester_start)
    timedelta = datetime.datetime.now() - semester_start
    current_week = (timedelta.days // 7) + 1
    week_type = (current_week - 1) % 4
    return week_type


async def get_full_time_table(student: OrioksStudentsModel) -> tuple[dict[int, list[str]], str]:
    stud_group, token = student.group.group_id, student.access_token
    time_table = await get_group_timetable(stud_group, token)
    today = datetime.datetime.today().weekday()

    time_table_messages: dict = {}
    week_type = await get_week_type(token)
    for day in time_table[week_type]:
        time, class_order, class_type, class_name, class_cabinet, week_type, day_number = day
        #if day_number == today + 1:
        if type(time[0]) == list:
            time = time[day_number in NO_LUNCH_DAYS]
        subj_msg = '|'.join([f'{time[0]}-{time[1]}', f'{class_type} {class_name}',
                             class_cabinet]) + '\n'


        if day_number in time_table_messages:
            time_table_messages[day_number].append(subj_msg)
        else:
            time_table_messages[day_number] = [subj_msg]
    return time_table_messages, f'<b>{week_type}</b>\n'
