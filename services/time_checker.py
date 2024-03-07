import datetime


def check_reminder_date(date: datetime.datetime) -> bool:
    current_date = datetime.datetime.date(datetime.datetime.now())
    return datetime.datetime.date(date) >= current_date


def check_reminder_time(hours: int, minutes: int, date: datetime.datetime) -> bool:
    if hours not in range(24) or minutes not in range(60):
        return False

    current_time = datetime.datetime.now()
    current_hours, current_minutes = current_time.hour, current_time.minute
    current_date = datetime.datetime.date(datetime.datetime.now())
    if datetime.datetime.date(date) == current_date:  # if the day is the same,
        if hours < current_hours:  # check that the time is not in the past
            return False
        if hours == current_hours and minutes <= current_minutes:
            return False
    return True
