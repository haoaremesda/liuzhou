import requests
from lxml import etree

heads = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}

proxies = {"http": "http://127.0.0.1:4780", "https": "http://127.0.0.1:4780"}

def get_free_resources(url):
    resp = requests.get(url=url, headers=heads, proxies=proxies)
    print(resp.text)


if __name__ == '__main__':
    url = "https://www.collegeessayguy.com"
    get_free_resources(url)