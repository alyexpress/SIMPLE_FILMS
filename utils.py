from PIL import Image
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