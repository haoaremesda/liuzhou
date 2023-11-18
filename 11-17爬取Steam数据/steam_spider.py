import json
import os
import time
from io import BytesIO

import pandas as pd
import requests
from lxml import etree
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
    for app_id in column_data[:5]:
        all_data = {}
        data = []
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
    # 打印列数据
    print(column_data)
    # 列名
    new_columns = ['M1', '百分比', 'M2', '百分比', 'M3', '百分比', 'P1', 'P2', 'P3', 'P4']

    # 创建一个 DataFrame
    df = pd.DataFrame(datas, columns=new_columns)

    # Excel 文件路径
    excel_file_path = '清单表 - 测试.xlsx'

    # 打开现有的 Excel 文件
    book = load_workbook(excel_file_path)

    # 创建一个 ExcelWriter 对象，指定打开已有文件的模式
    with pd.ExcelWriter(excel_file_path, engine='openpyxl', mode='a') as writer:
        # 选择已存在的 sheet
        writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
        ws = writer.sheets['Steam主机市场（2023.1-2023.6）']  # 将 'YourSheetName' 替换为你的实际表格名

        # 获取已有数据的最后一行的索引
        start_row = ws.max_row + 1

        # 写入新数据和图片
        for index, row in df.iterrows():
            # 写入数据
            ws.append(row.tolist())

            # 下载图片并添加到单元格
            image_url = row['ImagePath']
            response = requests.get(image_url)

            # 检查请求是否成功
            if response.status_code == 200:
                # 将图片字节数据保存到 BytesIO 对象
                img = Image(BytesIO(response.content))

                # 添加图片到单元格
                cell = 'D{}'.format(start_row + index)  # 第四列以后的列
                ws.add_image(img, cell)
            else:
                print(f"Failed to download image for row {start_row + index}")

        # 保存 Excel 文件
        writer.save()
