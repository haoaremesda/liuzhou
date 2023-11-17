import json
import os
import pandas as pd
import requests
from lxml import etree
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from bs4 import BeautifulSoup
import concurrent.futures

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

heads = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}

proxies = {"http": "http://127.0.0.1:4780", "https": "http://127.0.0.1:4780"}


def get_steam_scout(app_id, language: str):
    url = f"https://www.togeproductions.com/SteamScout/a.php?appID={app_id}&language={language}&purchase_type=all"
    resp = requests.get(url=url, headers=heads, proxies=proxies)
    if resp.status_code == 200:
        json_data = resp.json()
        if json_data["query_summary"]:
            return json_data["query_summary"]
    return {}


if __name__ == '__main__':
    languages = {
        'all': '所有',
        'arabic': '阿拉伯语',
        'bulgarian': '保加利亚语',
        'schinese': '简体中文',
        'tchinese': '繁体中文',
        'czech': '捷克语',
        'danish': '丹麦语',
        'dutch': '荷兰语',
        'english': '英语',
        'finnish': '芬兰语',
        'french': '法语',
        'german': '德语',
        'greek': '希腊语',
        'hungarian': '匈牙利语',
        'indonesian': '印尼语',
        'italian': '意大利语',
        'japanese': '日语',
        'koreana': '韩语',
        'norwegian': '挪威语',
        'polish': '波兰语',
        'portuguese': '葡萄牙语',
        'brazilian': '巴西葡萄牙语',
        'romanian': '罗马尼亚语',
        'russian': '俄语',
        'spanish': '西班牙语',
        'latam': '拉丁美洲西班牙语',
        'swedish': '瑞典语',
        'thai': '泰语',
        'turkish': '土耳其语',
        'ukrainian': '乌克兰语',
        'vietnamese': '越南语'
    }
    # 读取 Excel 文件
    file_path = './清单表.xlsx'  # 替换为你的文件路径
    column_name = 'SteamID'  # 替换为你想要获取的列名
    df = pd.read_excel(file_path, converters={column_name: int})
    # 获取某一列的数据
    column_data = df[column_name][1:].tolist()
    keys = list(languages.keys())
    for app_id in column_data[:5]:
        all_data = {}
        for key in keys:
            d = get_steam_scout(app_id, key)
            if key == "all":
                all_data = d
                continue
            portion = round(all_data["total_reviews"]/d["total_reviews"]*100, 2)
        print(app_id)

    # 打印列数据
    print(column_data)
