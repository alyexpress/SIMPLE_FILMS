from requests import get

response = get("http://127.0.0.1:8080/api/film/k38298/p7Kwv6z7y4MX2i0LaCxl")
print(response.text)