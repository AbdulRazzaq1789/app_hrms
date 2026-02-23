from __future__ import annotations
import jdatetime
import datetime as dt
from dataclasses import dataclass

@dataclass(frozen=True)
class JalaliMonthRange:
    jy: int
    jm: int
    days: int
    g_start: dt.date
    g_end: dt.date

def jalali_month_range(jy: int, jm: int) -> JalaliMonthRange:
    """
    Returns:
      - number of days in Jalali month
      - Gregorian start and end dates
    """
    # first day
    j_start = jdatetime.date(jy, jm, 1)
    g_start = j_start.togregorian()

    # compute days: go to next month, subtract 1 day
    if jm == 12:
        j_next = jdatetime.date(jy + 1, 1, 1)
    else:
        j_next = jdatetime.date(jy, jm + 1, 1)

    g_end = (j_next.togregorian() - dt.timedelta(days=1))
    days = (g_end - g_start).days + 1

    return JalaliMonthRange(jy=jy, jm=jm, days=days, g_start=g_start, g_end=g_end)

def jalali_day_to_gregorian(jy: int, jm: int, jd: int) -> dt.date:
    return jdatetime.date(jy, jm, jd).togregorian()



JALALI_MONTHS_DARI = {
    1: "حمل",
    2: "ثور",
    3: "جوزا",
    4: "سرطان",
    5: "اسد",
    6: "سنبله",
    7: "میزان",
    8: "عقرب",
    9: "قوس",
    10: "جدی",
    11: "دلو",
    12: "حوت",
}


def get_jalali_month_name(jm: int) -> str:
    """
    Return Dari month name for Jalali month number
    """
    return JALALI_MONTHS_DARI.get(jm, str(jm))


WEEKDAY_NAMES_DARI = {
    0: "دوشنبه",
    1: "سه‌شنبه",
    2: "چهارشنبه",
    3: "پنج‌شنبه",
    4: "جمعه",
    5: "شنبه",
    6: "یکشنبه",
}

WEEKDAY_NAMES_EN = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday",
}


def get_weekday_names_from_gregorian(g_date):
    """
    Input: datetime.date (Gregorian)
    Output: (dari_name, english_name, weekday_index)
    """
    wd = g_date.weekday()
    return WEEKDAY_NAMES_DARI[wd], WEEKDAY_NAMES_EN[wd], wd


def get_weekday_names_from_jalali(jy: int, jm: int, jd: int):
    """
    Input: Jalali date
    Output: (dari_name, english_name, weekday_index)
    """
    import jdatetime

    g_date = jdatetime.date(jy, jm, jd).togregorian()
    return get_weekday_names_from_gregorian(g_date)

def get_full_jalali_date_label(jy: int, jm: int, jd: int):
    """
    Example output:
    "دوشنبه 15 حوت 1404"
    """
    dari_day, _, _ = get_weekday_names_from_jalali(jy, jm, jd)
    month_name = get_jalali_month_name(jm)
    return f"{dari_day} {jd} {month_name} {jy}"


def format_gregorian_to_jalali(g_date):
    """
    Input: datetime.date (Gregorian)
    Output: 'دوشنبه 15 حوت 1404'
    """
    if not g_date:
        return ""

    j = jdatetime.date.fromgregorian(date=g_date)

    dari_day, _, _ = get_weekday_names_from_gregorian(g_date)
    month_name = get_jalali_month_name(j.month)

    return f"{j.year}-{j.month}-{j.day}"


def format_gregorian_to_jalali_with_day(g_date):
    """
    Input: datetime.date (Gregorian)
    Output: 'دوشنبه 15 حوت 1404'
    """
    if not g_date:
        return ""

    j = jdatetime.date.fromgregorian(date=g_date)

    dari_day, _, _ = get_weekday_names_from_gregorian(g_date)

    return f"{j.year}-{j.month}-{j.day} {dari_day}"