import re

import requests
from lxml import etree
import os
import pandas as pd


req_session = requests.session()
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'iframe',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

req_session.headers = headers


# 定义一个函数，用于提取行业标准编码
def extract_standard_code(text):
    # 使用正则表达式匹配带斜杠的标准编码模式
    pattern = r'[A-Z]+[/A-Z\s\d-]+'
    match = re.search(pattern, text)
    if match:
        return match.group()
    else:
        return None


def get_file_names() -> dict:
    # 获取用户输入的目录路径
    directory = input("请输入目录路径: ")
    file_names_without_extension = {}
    # 检查输入路径是否存在
    if os.path.exists(directory) and os.path.isdir(directory):
        # 使用os库列出目录下的所有文件和子目录
        entries = os.listdir(directory)
        # 仅获取文件名并过滤掉子目录
        for entry in entries:
            entry_path = os.path.join(directory, entry)
            if os.path.isfile(entry_path):  # 仅包括文件，不包括子目录
                file_name = os.path.splitext(entry)[0]  # 获取文件名（不包括后缀）
                file_names_without_extension[file_name] = ""
        print(f"该目录下有文件数量 {len(file_names_without_extension)}")
    else:
        print("指定的目录路径不存在或不是目录。")
    return file_names_without_extension


def query_state(old_keywords: str):
    global file_names
    keywords = extract_standard_code(old_keywords).strip()
    if not keywords:
        return False
    params = {
        'q': keywords,
        'tid': '',
    }
    try:
        response = req_session.get('https://std.samr.gov.cn/search/stdPage', params=params)
        if response.status_code == 200:
            tree = etree.HTML(response.text)
            # 使用XPath表达式选择所有class为s-title的表格
            tables = tree.xpath('//div[@class="post-head"]/table')
            if not tables:
                file_names[old_keywords] = "未查询到"
            # 遍历每个表格
            for table in tables:
                rows = table.xpath('.//tr')
                # 假设每个表格都有相同数量的行
                for i in rows:
                    tds = i.xpath('.//td')
                    if len(tds) == 2:
                        standard_numbe = tds[0].xpath('./a//text()')
                        standard_numbe = "".join(standard_numbe).replace("\xa0", "").replace(" ", "").replace("/", "")
                        keywords_strip = keywords.replace(" ", "").replace("/", "")
                        state = tds[1].xpath('./span/text()')
                        if keywords_strip in standard_numbe:
                            file_names[old_keywords] = "|".join(state)
                            print(keywords, state)
                    else:
                        file_names[old_keywords] = "未查询到"
                        print("未查询到结果")
        else:
            print(keywords, "    查询失败")
    except Exception as e:
        print(e)


file_names = get_file_names()
# file_names = {"GB/T 40373-2021": "", "GB 8921-2011": "", "GB 6763-2000": ""}
for i in file_names.items():
    query_state(i[0])
df = pd.DataFrame(list(file_names.items()), columns=['标准编号', '状态'])

# 保存数据框为 Excel 文件
excel_file = 'special_characters.xlsx'
df.to_excel(excel_file, index=False, engine='openpyxl')
# 等待用户输入以结束程序
input("结果保存成功按Enter键以结束程序...")
