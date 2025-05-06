from requests import get

APIKEY = ""

params = {
    "type": "serial",
    "server": "kinovod",
    "code": "231675",
    "season": 1,
    "episode": 3,
    "apikey": APIKEY,
}

response = get("http://localhost:8080/api", params=params).text
print(response)