from PIL import Image
from re import sub
import hashlib


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
        r'([пП])[иИеЕ][зЗ][дД]': r'\1***',
        r'([еЕёЁ])[бБ][аАоОуУиИлЛ]': r'\1**',
        r'([хХ])[уУ][йЙеЕёЁяЯюЮ]': r'\1**',
        r'([бБ])[лЛ][яЯ]': r'\1**',
        r'([гГ])[аА][нН][дД]': r'\1***',
        r'([мМ])[уУ][дД][аАоО]': r'\1***',
        r'([жЖ])[оО][пП]': r'\1**',
        r'([сС])[уУ][кКчЧ]': r'\1**',
        r'([дД])[оО][лЛ][бБ]': r'\1***',
        r'([зЗ])[аА][лЛ][уУ]([пП])': r'\1***\2',
        r'([пП])[иИ][дД][оОаА]([рР])': r'\1***\2'
    }
    for dirty, censored in dirty_words.items():
        text = sub(dirty, censored, text)
    return text