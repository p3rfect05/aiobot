import time

import aiohttp
import asyncio
import requests

access_token = "vk1.a.jMb5Tyf392UMxk_hunDi99boAs4juMj92E_vsAZ29Ct-bsgvgngaV7LtOALBVOlvsBdlLH-SubuLZjJ5-1DZFwP61S3858kwiib7o6SPcDR7CBur4BKAOiXzse3iYaSEOeepgZsJZG8Mi8efILbq16Bh9D4OUJHpwCZzkXGNu9zMHY5XPF8vbvveGziUaf7yuW3fx-SWBMntCvhHz8bhqQ"
base = "https://api.vk.com/method/"


def user_groups(user_id):
    user_id = get_id(user_id)
    params = {"access_token": access_token, "v": "5.313", "user_id": user_id}
    try:
        response = requests.post(
            base + "users.getSubscriptions?", params=params
        ).json()["response"]["users"]["items"]

        return response
    except Exception:
        return "Could not access groups"


def whole_group_analysis(group_id, if_user_in):
    initial_user_id = if_user_in
    if_user_in = get_id(if_user_in)
    checked = 0
    members_number = 0
    params = {
        "access_token": access_token,
        "v": "5.313",
        "group_id": group_id,
        "offset": 0,
    }
    while True:
        try:
            response = requests.post(base + "groups.getMembers?", params=params)
        except:
            return (
                f"Something went wrong with group {group_id} and user {initial_user_id}"
            )
        time.sleep(0.5)
        response = response.json()["response"]
        if not members_number:
            members_number = response["count"]
        for user in response["items"]:
            if user == if_user_in:
                return True

        if checked + 1000 >= members_number:
            return False
        checked += 1000
        params["offset"] += 1000


def get_id(user_id):
    try:
        params = {"access_token": access_token, "v": "5.313", "user_ids": user_id}

        response = requests.post(base + "users.get?", params=params).json()["response"][
            0
        ]["id"]
    except:
        return f"Could not get an id of {user_id}"
    return response


groups = {
    "miet_one",
    "sno_miet",
    "sport.miet",
    "studcitymiet",
    "spintech_news",
    "en_miet",
    "nmst_miet",
    "mpsumiet",
    "bms_miet",
    "design_miet",
    "miet_inyaz",
    "dobromiet",
    "barter_miet",
    "so_vkusom_miet",
}


def check_miet_groups(user_id=None):
    initial_id = user_id
    if user_id is None:
        user_id = input("Enter user id: ")
    print(user_id)
    for group in list(groups):
        res = whole_group_analysis(group, get_id(user_id))
        print(f"{group}: {res}")


def check_if_friends(first_id=None, second_id=None):
    initial_first_id = first_id
    initial_second_id = second_id
    if first_id is None:
        first_id = input("Enter first id: ")
    first_id = get_id(first_id)
    if second_id is None:
        second_id = input("Enter second id: ")
    second_id = get_id(second_id)
    first_friends = get_friends(first_id)
    second_friends = get_friends(second_id)
    if first_friends is None and second_friends is None:
        return "Unable to access neither of friends' list"
    elif first_friends is None and second_friends is not None:
        return first_id in second_friends
    elif second_friends is None and first_friends is not None:
        return second_id in first_friends
    else:
        return (second_id in first_friends) or (first_id in second_friends)


async def get_friends(user_id) -> list[int] | None:
    async with aiohttp.ClientSession() as session:
        initial_id = user_id
        user_id = get_id(user_id)
        params = {"access_token": access_token, "v": "5.313", "user_id": user_id}
        try:
            async with session.post(base + "friends.get?", params=params) as response:
                friends_list = await response.json()
                print(friends_list)
        except:
            return None
        return friends_list


asyncio.run(get_friends("smoky_yo"))
