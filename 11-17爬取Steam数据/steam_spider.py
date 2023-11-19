import json
import os
import time
from io import BytesIO

import pandas as pd
import requests
from lxml import etree
from openpyxl.utils import get_column_letter
from openpyxl.workbook import Workbook
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from bs4 import BeautifulSoup
from openpyxl import load_workbook
from openpyxl.drawing.image import Image
import concurrent.futures

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

heads = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}

proxies = {"http": "http://127.0.0.1:4780", "https": "http://127.0.0.1:4780"}


# 自定义比较函数，将百分比字符串转换为浮点数进行比较
def custom_sort(item):
    return float(item['value'].strip('%'))


def get_steam_scout(app_id, language: str):
    url = f"https://www.togeproductions.com/SteamScout/a.php?appID={app_id}&language={language}&purchase_type=all"
    resp = requests.get(url=url, headers=heads, proxies=proxies)
    if resp.status_code == 200:
        json_data = resp.json()
        print(url)
        if json_data["query_summary"]:
            return json_data["query_summary"]
    return {}


def get_steam_img(app_id) -> list:
    movie_img_list = []
    url = f"https://store.steampowered.com/app/{app_id}"
    resp = requests.get(url=url, headers=heads, proxies=proxies)
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.content, 'html.parser')
        soup = soup.select("div[id='highlight_strip_scroll']")
        if not soup:
            return movie_img_list
        print(url, soup)
        for child in soup[0].contents:
            if child == "\n" or child.img == None:
                continue
            elif "thumb_movie" in child.get("id"):
                movie_id = child.get("id").split("thumb_movie_")[1]
                movie_url = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{movie_id}/movie_max.mp4?t={int(time.time())}"
                movie_img_list.append(movie_url)
            elif "thumb_screenshot" in child.get("id") and child.img:
                img_url = child.img.get("src")
                img_url = img_url.replace("116x65", "600x338")
                movie_img_list.append(img_url)
            if len(movie_img_list) == 4:
                break
    print(movie_img_list)
    return movie_img_list


if __name__ == '__main__':
    datas = []
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
    for app_id in column_data:
        all_data = {}
        data = [str(app_id)]
        portions = []
        for key in keys:
            d = get_steam_scout(app_id, key)
            if key == "all":
                all_data = d
                continue
            if d["total_reviews"] == 0:
                portion = "0.00%"
            else:
                portion = round(d["total_reviews"]/all_data["total_reviews"]*100, 2)
                portion = f"{portion}%"
            portions.append({"name": key, "value": portion})
            time.sleep(0.5)
        portions = sorted(portions, key=custom_sort, reverse=True)
        for p in portions[:3]:
            data.append(languages[p["name"]])
            data.append(p["value"])
        url_list = get_steam_img(app_id)
        data.extend(url_list)
        datas.append(data)
        time.sleep(0.5)
    # 打印列数据
    print(column_data)
    # 列名
    # datas = [['简体中文', '8.26%', '保加利亚语', '0.03%', '阿拉伯语', '0.00%', 'https://cdn.cloudflare.steamstatic.com/steam/apps/256970996/movie_max.mp4?t=1700397246', 'https://cdn.cloudflare.steamstatic.com/steam/apps/714010/ss_85f1fa0f47a568297ae65a37450bdbbe06ca88cf.600x338.jpg?t=1695340445', 'https://cdn.cloudflare.steamstatic.com/steam/apps/714010/ss_a456640ad0687e8e5fa13b0729f54efcf5ab994a.600x338.jpg?t=1695340445', 'https://cdn.cloudflare.steamstatic.com/steam/apps/714010/ss_90dc622d806092e52ffa966e027fccf463b846b3.600x338.jpg?t=1695340445'], ['简体中文', '9.52%', '保加利亚语', '0.06%', '阿拉伯语', '0.00%', 'https://cdn.cloudflare.steamstatic.com/steam/apps/256932123/movie_max.mp4?t=1700397255', 'https://cdn.cloudflare.steamstatic.com/steam/apps/256880856/movie_max.mp4?t=1700397255', 'https://cdn.cloudflare.steamstatic.com/steam/apps/1326470/ss_e6e3ab1badfb287a77fb6eef7b1589a35371496b.600x338.jpg?t=1697048131', 'https://cdn.cloudflare.steamstatic.com/steam/apps/1326470/ss_4fa5d260318f0aa37754b00c5dc10d1b7b9b9b1d.600x338.jpg?t=1697048131'], ['简体中文', '7.6%', '保加利亚语', '0.02%', '阿拉伯语', '0.00%', 'https://cdn.cloudflare.steamstatic.com/steam/apps/256930504/movie_max.mp4?t=1700397263', 'https://cdn.cloudflare.steamstatic.com/steam/apps/990080/ss_725bf58485beb4aa37a3a69c1e2baa69bf3e4653.600x338.jpg?t=1699983982', 'https://cdn.cloudflare.steamstatic.com/steam/apps/990080/ss_df93b5e8a183f7232d68be94ae78920a90de1443.600x338.jpg?t=1699983982', 'https://cdn.cloudflare.steamstatic.com/steam/apps/990080/ss_94058497bf0f8fabdde17ee8d59bece609a60663.600x338.jpg?t=1699983982'], ['简体中文', '3.77%', '阿拉伯语', '0.00%', '保加利亚语', '0.0%', 'https://cdn.cloudflare.steamstatic.com/steam/apps/256951968/movie_max.mp4?t=1700397272', 'https://cdn.cloudflare.steamstatic.com/steam/apps/256951780/movie_max.mp4?t=1700397272', 'https://cdn.cloudflare.steamstatic.com/steam/apps/671860/ss_08558f0aa02d2c03c47971cfb39e4af207ac18ff.600x338.jpg?t=1686877598', 'https://cdn.cloudflare.steamstatic.com/steam/apps/671860/ss_b4175c430cc50636e44a9e6f07fa3a91bfe01548.600x338.jpg?t=1686877598'], ['简体中文', '96.36%', '阿拉伯语', '0.00%', '保加利亚语', '0.0%', 'https://cdn.cloudflare.steamstatic.com/steam/apps/256947330/movie_max.mp4?t=1700397280', 'https://cdn.cloudflare.steamstatic.com/steam/apps/256849529/movie_max.mp4?t=1700397280', 'https://cdn.cloudflare.steamstatic.com/steam/apps/1468810/ss_7c70bc3bdba8adca87c229ed1a2ad15a36ec2573.600x338.jpg?t=1689733570', 'https://cdn.cloudflare.steamstatic.com/steam/apps/1468810/ss_200cb2792ed1a75d17dc2d3be788a8ccaff402e4.600x338.jpg?t=1689733570']]
    # 创建一个 DataFrame
    # Excel 文件路径
    excel_file_path = '清单表 - 测试.xlsx'
    # 创建一个 Excel 工作簿
    wb = Workbook()
    ws = wb.active
    # 遍历数据并将其写入Excel文件
    for row_index, row_data in enumerate(datas, start=1):
        for col_index, link in enumerate(row_data, start=1):
            # 如果是图片链接，则下载图片并插入单元格
            if '.jpg' in link or '.png' in link:
                # 处理图片
                response = requests.get(link)
                if response.status_code == 200:
                    # 将图片字节数据保存到 BytesIO 对象
                    img = Image(BytesIO(response.content))
                    ws.add_image(img, f"{get_column_letter(col_index)}{row_index}")
                else:
                    print(f"Failed to download image for link {link}")
            else:
                # 其他情况直接插入数据
                ws.cell(row=row_index, column=col_index, value=link)
    # 保存 Excel 文件
    wb.save(excel_file_path)
