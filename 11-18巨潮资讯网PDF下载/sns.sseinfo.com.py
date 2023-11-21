import os
import time

import requests
import concurrent.futures
import pandas as pd
from datetime import datetime, timedelta
from retrying import retry
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# 禁用安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

headers = {
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
}


def remove_special_characters(strings):
    special_characters = "|\:*<>?./\""
    return "".join([string for string in strings if not any(char in special_characters for char in string)])


@retry(wait_fixed=5000)
def query_feeds() -> tuple:
    num = 0
    ks = []
    params = {
        'rnd': '0.2540704981254671',
        'type': '30',
        'pageSize': '10',
        'lastid': '-1',
        'show': '1',
        'page': '8',
    }
    response = requests.get('https://sns.sseinfo.com/ajax/feeds.do', params=params, headers=headers, verify=False)
    if response.status_code == 200:
        json_data = response.json()
        if json_data["announcements"]:
            print(response.status_code, page, pageSize, seDate, response.text)
            for item in json_data["announcements"]:
                d = []
                for k in ["secCode", "secName", "announcementTitle"]:
                    d.append(remove_special_characters(item[k]))
                datetime_object = datetime.utcfromtimestamp(item["announcementTime"] / 1000)
                # Format the datetime object as a string
                formatted_time = datetime_object.strftime('%Y-%m-%d %H：%M：%S')
                d.append(formatted_time)
                try:
                    ks.append({"file_name": "_".join(d), "url": f"http://static.cninfo.com.cn/{item['adjunctUrl']}"})
                except:
                    print(item)
            num = json_data["totalAnnouncement"]
    else:
        print(response.status_code, response.text)
    return num, ks


@retry(wait_fixed=5000)
def save_pdf(pdf_ks: dict):
    global folder
    file_path = f'{folder}/{pdf_ks["file_name"]}.{pdf_ks["url"].split(".")[-1]}'
    if not os.path.exists(file_path):
        resp = requests.get(url=pdf_ks["url"], stream=True)
        if resp.status_code == 200:
            with open(f'{file_path}', 'wb') as fd:
                for chunk in resp.iter_content(5120):
                    fd.write(chunk)


def get_cninfo_pdf_links() -> list:
    likes = []
    PageSize = 30
    # 定义起始日期和结束日期
    start_date = datetime(2012, 7, 1)
    end_date = datetime(2023, 10, 31)
    # 初始化一个空列表来存储日期字符串
    date_strings = []
    # 生成在指定范围内的每个半个月的日期字符串范围
    current_date = start_date
    while current_date <= end_date:
        # 计算每个半个月的结束日期
        interval_end_date = current_date + timedelta(days=15)
        # 如果结束日期超过了结束日期范围，则修正为结束日期
        if interval_end_date > end_date:
            interval_end_date = end_date
        # 添加日期范围字符串到列表
        date_strings.append(f"{current_date.strftime('%Y-%m-%d')}~{interval_end_date.strftime('%Y-%m-%d')}")
        # 更新当前日期为下一个半个月的起始日期
        current_date = interval_end_date + timedelta(days=1)
    all_pdf_num = 0
    pdf_num_dict = {}
    for index, i in enumerate(date_strings):
        page = 1
        max_num = 0
        while True:
            print(index, page, PageSize, i)
            max_num, data = query_announcements(page, PageSize, i)
            # for x in data:
            #     save_pdf(x)
            #     time.sleep(0.5)
            max_threads = 5
            with concurrent.futures.ThreadPoolExecutor(max_threads) as executor:
                futures = [executor.submit(save_pdf, value) for value in data]
                concurrent.futures.wait(futures)
            if not max_num:
                break
            # likes.extend(data)
            if max_num < page * PageSize:
                all_pdf_num += max_num
                pdf_num_dict[i] = max_num
                break
            time.sleep(0.5)
            page += 1
    print("所有数量：", all_pdf_num)
    print("数量分布：", pdf_num_dict)
    print(likes)
    return likes



if __name__ == '__main__':
    # 命名：公司简称-公告标题-公告时间
    # 公司简称：//div[@class="m_feed_face"]/p/text()
    # 公告文件url：//div[@class="m_feed_txt"]/a/@href
    # 公告标题：//div[@class="m_feed_txt"]/a/text()
    # 公告时间：//div[@class="m_feed_from"]/span/text()
    query_feeds()
    folder = "./巨潮资讯网PDF"
    if not os.path.exists(folder):
        os.makedirs(folder)
    likes = get_cninfo_pdf_links()

