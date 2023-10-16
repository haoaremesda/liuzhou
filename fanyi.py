import requests
import time

cookies = {
    'Hm_lvt_f30c9520ba88c3ba32d724111afb8682': '1697433064',
    'authtoken': '0809c0ade29c18883a2d3414f23deaf6079da3cc',
    'Hm_lpvt_f30c9520ba88c3ba32d724111afb8682': '1697433379',
}

headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json;charset=UTF-8',
    'Origin': 'https://fanyi.atman360.com',
    'Pragma': 'no-cache',
    'Referer': 'https://fanyi.atman360.com/text',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}


def translate_function(keyword):
    params = {
        't':  str(int(time.time()*1e3)),
        'team_id': '56221',
    }
    json_data = {
        'source': 'en',
        'target': 'zh',
        'domain': 'medical',
        'lines': [
            {
                'id': 0,
                'text': keyword,
                'layer': keyword,
                'br': False,
                'style': {
                    'min-height': 'auto',
                },
            },
        ],
        'tm_ids': [],
        'tb_ids': [],
    }
    response = requests.post('https://fanyi.atman360.com/api/trans/batch/', params=params, cookies=cookies, headers=headers, json=json_data)
    if response.status_code == 200:
        j = response.json()
        if j["errcode"] == 0:
            text = j["data"][0]["text"]
            return text
    print(response.text)
    return ""


import os
import re
# 定义一个函数，用于检查文本是否为英文
def is_english(text):
    return re.match(r'^[a-zA-Z\s]+$', text) is not None


# 定义一个递归函数，用于遍历文件夹结构并翻译文件名
def translate_folder_contents(folder):
    for root, dirs, files in os.walk(folder):
        # 遍历当前文件夹的文件夹名称
        for subfolder in dirs:
            print(subfolder)
            if is_english(subfolder[0]):
                # 如果文件夹名称为英文，进行翻译
                translated_name = translate_function(subfolder)
                new_subfolder = os.path.join(root, translated_name)
                os.rename(os.path.join(root, subfolder), new_subfolder)

        # 遍历当前文件夹的文件名称
        for filename in files:
            print(filename)
            if is_english(filename[0]):
                # 如果文件名称为英文，进行翻译
                x = filename.split(".")
                translated_name = translate_function(x[0])
                new_filename = os.path.join(root, translated_name)
                os.rename(os.path.join(root, filename), f"{new_filename}.{x[1]}")

# 使用示例：传入要遍历的根文件夹
root_folder = './books'
translate_folder_contents(root_folder)
