import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import (TimeoutException, JavascriptException,
                                        NoSuchElementException)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from time import sleep
from re import search

#DEL
from pprint import pprint


class Service:
    HEADERS = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/98.0.4758.132 YaBrowser/22.3.1.892 '
                      'Yowser/2.5 Safari/537.36',
        'accept': '*/*'
    }

    def __init__(self, server=None):
        if server is not None:
            self.SERVER = server


# class Kinopoisk(Service):
#     SERVER = "https://ggkinopoisk.ru"
#     KINOPOISK = "https://www.kinopoisk.ru"
#
#     def get(self, url):
#         url = url.replace(self.KINOPOISK, self.SERVER)
#         driver = webdriver.Chrome()
#         driver.get(url)
#         WebDriverWait(driver, 200).until(
#             EC.presence_of_element_located((By.CLASS_NAME, 'video')))
#         soup = BeautifulSoup(driver.page_source, 'html.parser')
#         # req = requests.get(url=url, headers=self.HEADERS)
#         # soup = BeautifulSoup(req.text, 'html.parser')
#         # script = soup.find("script").text
#         # re = r'var redirectUrl = "(\S+)";'
#         # pprint(soup)
#         # redirect_url = search(re, script).group(1)
#         # req = requests.get(url=redirect_url, headers=self.HEADERS)
#         # soup = BeautifulSoup(req.text, 'html.parser')
#         # iframe = soup.find(id="playerFrame")
#         return soup
#
# if __name__ == '__main__':
#     kinopoisk = Kinopoisk()
#     pprint(kinopoisk.get("https://www.kinopoisk.ru/series/5304403/"))


class Kinovod(Service):
    SERVER = "https://kinovod.pro"
    NEW_PLAYER = {'name': 'player_settings', 'value': 'new|mp4|1'}
    OLD_PLAYER = {'name': 'player_settings', 'value': 'old|mp4|1'}
    FULL_HD = "window.localStorage.setItem('pljsquality', '1080p')"
    HD = "window.localStorage.setItem('pljsquality', '720p')"

    def film(self, code):
        try:
            driver = webdriver.Chrome()
            driver.get(f"{self.SERVER}/film/{code}")
            driver.find_element(By.ID, "info")
            driver.add_cookie(self.NEW_PLAYER)
            driver.execute_script(self.FULL_HD)
            driver.refresh()
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'video')))
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            driver.quit()
            video = soup.find('video')['src']
            return {'src': video}
        except NoSuchElementException:
            return {'error': '404 Not Found', 'src': ''}
        except TimeoutException:
            return {'error': '524 A Timeout Occurred', 'src': ''}
        except (TypeError, KeyError):
            return {'error': '502 Bad Gateway', 'src': ''}
        except Exception:
            return {'error': '520 Unknown Error', 'src': ''}

    def serial(self, code, s=1, e=1):
        try:
            driver = webdriver.Chrome()
            driver.get(f"{self.SERVER}/serial/{code}")
            driver.find_element(By.ID, "info")
            driver.add_cookie(self.OLD_PLAYER)
            driver.refresh()
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'select')))
            options = ".uppod-control_hd_select > select > option"
            quality = f"if (document.querySelectorAll('{options}').length"
            quality += f"< 3) {self.HD}; else {self.FULL_HD};"
            driver.execute_script(quality)
            driver.refresh()
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'video')))
            xpath = "uppod_player_div.uppod-playlist > uppod_player_div > *"
            first = "getElementsByClassName('uppod-playlist-0_text')[0]"
            js = f"""let seasons = document.querySelectorAll('{xpath}');
            let first = seasons[0].{first}.textContent;
            if (first.includes("серия")) {{ seasons[{e - 1}].click();
                return {{"seasons": 0, "episodes": seasons.length}};
            }} else {{ seasons[{s - 1}].click();
                let episodes = document.querySelectorAll('{xpath}');
                episodes[{e}].click(); return {{"seasons": seasons.length,
                "episodes": episodes.length - 1}}; }}"""
            parts = driver.execute_script(js)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'video')))
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            driver.quit()
            video = soup.find('video').find('source')['src']
            return dict([('src', video)] + list(parts.items()))
        except NoSuchElementException:
            return {'error': '404 Not Found', 'src': ''}
        except JavascriptException:
            return {'error': '400 Bad Request', 'src': ''}
        except TimeoutException:
            return {'error': '524 A Timeout Occurred', 'src': ''}
        except (TypeError, KeyError):
            return {'error': '502 Bad Gateway', 'src': ''}
        except Exception:
            return {'error': '520 Unknown Error', 'src': ''}

    def info(self, code):
        try:
            url = f"{self.SERVER}/film/{code}"
            req = requests.get(url=url, headers=self.HEADERS)
            soup = BeautifulSoup(req.text, 'html.parser')
            if not soup.find(id='info'):
                raise NoSuchElementException
            preview = soup.select_one('.poster > img')['src']
            title = soup.select_one('#title > h1').get_text()
            div = soup.select_one("div[itemprop=description]")
            description = "" if div is None else div.get_text()
            span = soup.select_one("span.rating_site")
            rating = 0 if span is None else span.parent.get_text()
            meta = soup.find('meta', property="og:url").get("content")
            serial = meta.split("/")[-2] == "serial"
            data = {'preview': self.SERVER + preview,
                    'title': title, 'rating': float(rating),
                    'serial': serial, 'description': description}
            for item in soup.select('.info_items > .info_item'):
                key = item.select_one('.key').get_text()
                value = item.select_one('.value')
                links = value.select('a')
                data[key] = (value.get_text() if not links else
                             list(map(lambda x: x.get_text(), links)))
            del data['']
            return data
        except NoSuchElementException:
            return {'error': '404 Not Found'}
        except Exception:
            return {'error': '502 Bad Gateway'}

    def search(self, query):
        query = query.replace(' ', '+')
        url = f"{self.SERVER}/search?query={query}"
        req = requests.get(url=url, headers=self.HEADERS)
        soup = BeautifulSoup(req.text, 'html.parser')
        items = soup.find_all("li", class_='item')
        results = []
        for item in items:
            preview = self.SERVER + item.find('img')['src']
            title = item.select_one('div.title > a').get_text()
            year = item.select_one('span.year').get_text().split(',')[0]
            rating = item.select_one('span.rating')
            rating = 0. if rating is None else float(rating.get_text())
            link = item.select_one('div.title > a')['href']
            data = {'preview': preview, 'title': title, 'year': year,
                    'rating': rating, 'link': self.SERVER + link,
                    'code': link.split('-')[0].lstrip('/film/')}
            results.append(data)
        return {'results': results}

    def get_items(self, url, count=12):
        req = requests.get(url=url, headers=self.HEADERS)
        soup = BeautifulSoup(req.text, 'html.parser')
        items = soup.find_all("li", class_='item')[:count]
        results = []
        for item in items:
            preview = self.SERVER + item.find('img')['src']
            title = item.select_one('div.title > a').get_text()
            year = item.select_one('span.year').get_text().split(',')[0]
            rating = item.select_one('span.rating')
            rating = 0. if rating is None else float(rating.get_text())
            link = item.select_one('div.title > a')['href']
            data = {'preview': preview, 'title': title, 'year': year,
                    'rating': rating, 'link': self.SERVER + link,
                    'code': link.split('-')[0].lstrip('/film/')}
            results.append(data)
        return {'results': results}

    def films(self, count=12):
        url = self.SERVER + "/films"
        return self.get_items(url, count)

    def serials(self, count=12):
        url = self.SERVER + "/serials"
        return self.get_items(url, count)


class FilmParse:
    RUTUBE_SERVER = "https://rutube.ru"
    KINOVOD_SERVER = "https://kinovod.pro"
    ZONA_SERVER = "https://w140.zona.plus"
    HEADERS = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/98.0.4758.132 YaBrowser/22.3.1.892 '
                      'Yowser/2.5 Safari/537.36',
        'accept': '*/*'
    }
    def __init__(self):
        pass

    def get_rutube(self, url):
        film_code = url.split('/')[-2]
        url = f'{self.RUTUBE_SERVER}/api/play/options/{film_code}'
        url += '/?no_404=true&referer=https%3A%2F%2Frutube.ru'
        req = requests.get(url, headers=self.HEADERS)
        video_data = req.json()
        video_author = video_data['author']['name']
        video_title = video_data['title']
        video_title = video_title.replace(" ", "_")
        video_author = video_author.replace(" ", "_")
        video_m3u8 = video_data['video_balancer']
        return video_author, video_title, video_m3u8


    @staticmethod
    def get_kinovod(url):
        driver = webdriver.Chrome()
        driver.get(url)
        driver.add_cookie({'name': 'player_settings', 'value': 'new|mp4|1'})
        js = "window.localStorage.setItem('pljsquality', '1080p');"
        driver.execute_script(js)
        driver.refresh()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'video')))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()
        video = soup.find('video')['src']
        return video

    @staticmethod
    def get_kinovod_serials(url, s=1, e=5):
        driver = webdriver.Chrome()
        driver.get(url)
        driver.add_cookie({'name': 'player_settings', 'value': 'old|mp4|1'})
        js = "window.localStorage.setItem('pljsquality', '1080p');"
        driver.execute_script(js)
        driver.refresh()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'video')))
        xpath = "uppod_player_div.uppod-playlist > uppod_player_div > *"
        js = f"""let s = document.querySelectorAll('{xpath}');
        s[{s - 1}].click(); let e = document.querySelectorAll('{xpath}');
        e[{e}].click(); return [s.length, e.length - 1]"""
        seasons, episodes = driver.execute_script(js)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'video')))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()
        video = soup.find('video').find('source')['src']
        return video, seasons, episodes


    def get_info_kinovod(self, url):
        req = requests.get(url=url, headers=self.HEADERS)
        soup = BeautifulSoup(req.text, 'html.parser')
        preview = soup.select_one('.poster > img')['src']
        title = soup.select_one('#title > h1').get_text()
        description = soup.select_one("div[itemprop=description]")
        rating = soup.select_one("span.rating_site").parent.get_text()
        data = {'preview': self.KINOVOD_SERVER + preview, 'title': title,
            'rating': float(rating), 'description': description.get_text()}
        meta = soup.find('meta', property="og:url").get("content")
        serial = meta.split("/")[-2] == "serial"
        for item in soup.select('.info_items > .info_item'):
            key = item.select_one('.key').get_text()
            value = item.select_one('.value')
            if value.select('a'):
                info = map(lambda x: x.get_text(), value.select('a'))
                data[key] = list(info)
            else:
                data[key] = value.get_text()
        del data['']

        return data, serial
        # genres = soup.select("span[itemprop=genre]")[:3]
        # genres = list(map(lambda x: x.get_text(), genres))
        # producer = soup.select_one("span[itemprop=name]").get_text()
        # # rating = item.select_one('span.rating').get_text()
        # # link = item.select_one('div.title > a')['href']
        #
        #         'genres': genres, "producer": producer}
        # print(genres)
        # return data


    def search_kinovod(self, query):
        query = query.replace(' ', '+')
        url = f"{self.KINOVOD_SERVER}/search?query={query}"
        req = requests.get(url=url, headers=self.HEADERS)
        soup = BeautifulSoup(req.text, 'html.parser')
        items = soup.find_all("li", class_='item')
        results = []
        for item in items:
            preview = self.KINOVOD_SERVER + item.find('img')['src']
            title = item.select_one('div.title > a').get_text()
            year = item.select_one('span.year').get_text().split(',')[0]
            rating = item.select_one('span.rating').get_text()
            link = item.select_one('div.title > a')['href']
            data = {'preview': preview, 'title': title, 'year': year,
                    'rating': rating, 'link': self.KINOVOD_SERVER + link}
            results.append(data)
        return results

    def films_kinovod(self, count=12):
        url = self.KINOVOD_SERVER + "/films"
        req = requests.get(url=url, headers=self.HEADERS)
        soup = BeautifulSoup(req.text, 'html.parser')
        items = soup.find_all("li", class_='item')[:count]
        results = []
        for item in items:
            preview = self.KINOVOD_SERVER + item.find('img')['src']
            title = item.select_one('div.title > a').get_text()
            year = item.select_one('span.year').get_text().split(',')[0]
            rating = item.select_one('span.rating').get_text()
            link = item.select_one('div.title > a')['href']
            data = {'preview': preview, 'title': title, 'year': year,
                    'rating': rating, 'link': self.KINOVOD_SERVER + link}
            results.append(data)
        return results

    def serials_kinovod(self, count=12):
        url = self.KINOVOD_SERVER + "/serials"
        req = requests.get(url=url, headers=self.HEADERS)
        soup = BeautifulSoup(req.text, 'html.parser')
        items = soup.find_all("li", class_='item')[:count]
        results = []
        for item in items:
            preview = self.KINOVOD_SERVER + item.find('img')['src']
            title = item.select_one('div.title > a').get_text()
            year = item.select_one('span.year').get_text().split(',')[0]
            rating = item.select_one('span.rating').get_text()
            link = item.select_one('div.title > a')['href']
            data = {'preview': preview, 'title': title, 'year': year,
                    'rating': rating, 'link': self.KINOVOD_SERVER + link}
            results.append(data)
        return results

    @staticmethod
    def get_zona(url):
        driver = webdriver.Chrome()
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'video')))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()
        video = soup.find('video')['src']
        return video

    def get_info_zona(self, url):
        req = requests.get(url=url, headers=self.HEADERS)
        soup = BeautifulSoup(req.text, 'html.parser')
        title = soup.select_one('span.js-title').get_text()
        adult = False
        if title.endswith('18+'):
            title, adult = title[:-4], True
        rating = soup.select_one('span.entity-rating-mobi').get_text()
        preview = soup.select_one('.entity-desc-poster > meta').get('content')
        description = soup.select_one('.entity-desc-description').get_text()
        data = {'title': title, 'adult': adult, 'rating': rating,
                'preview': preview, 'description': description}
        xpath = '.entity-desc-table > dl.entity-desc-item-wrap'
        for item in soup.select(xpath):
            key = item.select_one('.entity-desc-item').get_text()
            value = item.select_one('.entity-desc-value')
            if value.select('*'):
                if value.select('a > span'):
                    spans = value.select('a > span')
                elif value.select('span > span'):
                    spans = value.select('span > span')
                else:
                    spans = value.select('*')
                info = map(lambda x: x.get_text().strip('\n'), spans)
                data[key] = list(info)
            else:
                data[key] = value.get_text()
        return data


    @staticmethod
    def get_zona_serials(url, s=1, e=1):
        driver = webdriver.Chrome()
        driver.get(url + f"/season-{s}")
        js = 'document.getElementsByClassName("entity-episode-link")'
        driver.execute_script(js + f"[{e - 1}].click()")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'video')))
        sleep(1)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()
        video = soup.find('video')['src']
        return video


    def search_zona(self, query):
        url = f"{self.ZONA_SERVER}/search/{query}"
        req = requests.get(url=url, headers=self.HEADERS)
        soup = BeautifulSoup(req.text, 'html.parser')
        items = soup.find_all("li", class_='results-item-wrap')
        results = []
        for item in items:
            preview = item.find('meta')['content']
            title = item.select_one('div > .results-item-title').get_text()
            year = item.select_one('div > .results-item-year').get_text()
            rating = item.select_one(
                'div > .results-item-rating > span').get_text()
            link = self.ZONA_SERVER + item.find('a')['href']
            data = {'preview': preview, 'title': title, 'year': year,
                    'rating': rating, 'link': link}
            results.append(data)
        return results


    def get_film(self, server, url):
        match server:
            case 'rutube':
                return self.get_rutube(url)
            case 'kinovod':
                return self.get_kinovod(url)
            case 'zona':
                return self.get_zona(url)