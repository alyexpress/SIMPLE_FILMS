from PIL import Image
from re import sub
import hashlib
import datetime


def hashing(data):
    salt = "92vALen3n"
    hashed = hashlib.md5((data + salt).encode())
    return hashed.hexdigest()

def square_pic(path):
    img = Image.open(path)
    x, y = img.size
    if x != y:
        if x > y:
            u, b = 0, y
            l = (x - y) // 2
            r = y + l
        else:
            l, r = 0, x
            u = (y - x) // 2
            b = x + u
        img = img.crop((l, u, r, b))
        img.save(path)

def censored_text(text):
    dirty_words = {
        r'([пП])[иИеЕ][зЗ][дД]': r'\1###',
        r'([еЕёЁ])[бБ][аАоОуУиИлЛ]': r'\1##',
        r'([хХ])[уУ][йЙеЕёЁяЯюЮ]': r'\1##',
        r'([бБ])[лЛ][яЯ]': r'\1##',
        r'([гГ])[аА][нН][дД]': r'\1###',
        r'([мМ])[уУ][дД]([аАоО])': r'\1##\2',
        r'([жЖ])[оО][пП]': r'\1##',
        r'([сС])[уУ][кКчЧ]': r'\1##',
        r'([дД])[оО][лЛ][бБ]': r'\1###',
        r'([зЗ])[аА][лЛ][уУ]([пП])': r'\1###\2',
        r'([пП])[иИ][дД][оОаА]([рР])': r'\1###\2',
        r'([гГ])[аА][вВ]([нН])': r'\1##\2'
    }
    for dirty, censored in dirty_words.items():
        text = sub(dirty, censored, text)
    return text


def string_date(key, num):
    words = {'year': ['год', 'года', 'лет'],
             'month': ['месяц', 'месяца', 'месяцев'],
             'week': ['неделю', 'недели', 'недель'],
             'day': ['день', 'дня', 'дней'],
             'hour': ['час', 'часа', 'часов'],
             'minute': ['минуту', 'минуты', 'минут']}
    if num % 10 == 0 or num % 10 >= 5 or 10 < num < 20:
        return f"{num} {words[key][2]} назад"
    elif num % 10 == 1:
        return f"{num} {words[key][0]} назад"
    return f"{num} {words[key][1]} назад"


def time_ago(date):
    delta = datetime.datetime.now() - date
    if delta.days >= 365:
        return string_date('year', delta.days // 365)
    if delta.days >= 30:
        return string_date('month', delta.days // 30)
    if delta.days >= 7:
        return string_date('week', delta.days // 7)
    if delta.days >= 1:
        return string_date('day', delta.days)
    if delta.seconds // 3600 >= 1:
        return string_date('hour', delta.seconds // 3600)
    if delta.seconds // 60 >= 1:
        return string_date('minute', delta.seconds // 60)
    return "только что"
