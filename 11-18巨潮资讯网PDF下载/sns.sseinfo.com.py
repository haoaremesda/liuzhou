import os
import random
import time

import requests
import concurrent.futures
import pandas as pd
from lxml import etree
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

proxies = {"http": "http://127.0.0.1:4780", "https": "http://127.0.0.1:4780"}


def remove_special_characters(strings):
    special_characters = "|\:*<>?./\""
    return "".join([string for string in strings if not any(char in special_characters for char in string)])


from datetime import datetime, timedelta


def convert_to_datetime(original_str):
    now = datetime.now()

    if '分钟前' in original_str:
        minutes_ago = int(original_str.split('分钟前')[0])
        timestamp = now - timedelta(minutes=minutes_ago)
    elif '小时前' in original_str:
        hours_ago = int(original_str.split('小时前')[0])
        timestamp = now - timedelta(hours=hours_ago)
    elif '昨天' in original_str:
        time_str = original_str.replace('昨天 ', '')
        timestamp = datetime.strptime(time_str, '%H:%M')
        timestamp = timestamp.replace(year=now.year, month=now.month, day=now.day) - timedelta(days=1)
    else:
        timestamp = datetime.strptime(original_str, '%Y年%m月%d日 %H:%M')

    return timestamp.strftime('%Y-%m-%d %H：%M：%S')


@retry(wait_fixed=5000)
def query_feeds(page: int, page_size: int) -> tuple:
    num = 0
    ks = []
    come_to_an_end = False
    params = {
        'rnd': random.random(),
        'type': '30',
        'pageSize': page_size,
        'lastid': '-1',
        'show': '1',
        'page': page,
    }
    response = requests.get('https://sns.sseinfo.com/ajax/feeds.do', params=params, headers=headers, proxies=proxies, verify=False)
    if response.status_code == 200:
        if "暂时没有上市公司发布" in response.text:
            come_to_an_end = True
        else:
            tree = etree.HTML(response.text)
            company_names = tree.xpath('//div[@class="m_feed_face"]/p/text()')
            file_urls = tree.xpath('//div[@class="m_feed_txt"]/a/@href')
            file_names = tree.xpath('//div[@class="m_feed_txt"]/a/text()')
            released_time = tree.xpath('//div[@class="m_feed_from"]/span/text()')
            released_time = [convert_to_datetime(item) for item in released_time]
            if company_names and file_urls and file_names and released_time:
                for i in range(len(company_names)):
                    if not file_urls[i]:
                        continue
                    # 命名：公司简称-公告标题-公告时间
                    d = file_names[i].split(".")
                    d.insert(0, company_names[i])
                    d.insert(-1, released_time[i])
                    ks.append({"file_name": "_".join(d[:-1]), "url": file_urls[i]})
    else:
        print(response.status_code, response.text)
    num = len(ks)
    return num, ks, come_to_an_end


@retry(wait_fixed=5000)
def save_pdf(pdf_ks: dict):
    global folder
    file_path = f'{folder}/{pdf_ks["file_name"]}.{pdf_ks["url"].split(".")[-1]}'
    if not os.path.exists(file_path):
        resp = requests.get(url=pdf_ks["url"], proxies=proxies, stream=True)
        if resp.status_code == 200:
            with open(f'{file_path}', 'wb') as fd:
                for chunk in resp.iter_content(5120):
                    fd.write(chunk)
        print("爬取完成：", file_path)


def get_sseinfo_pdf_links():
    page = 1
    all_pdf_num = 0
    pdf_num_dict = {}
    while True:
        max_num, data, come_to_an_end = query_feeds(page, 10)
        print(max_num, come_to_an_end)
        if come_to_an_end:
            break
        max_threads = 3
        with concurrent.futures.ThreadPoolExecutor(max_threads) as executor:
            futures = [executor.submit(save_pdf, value) for value in data]
            concurrent.futures.wait(futures)
        time.sleep(2)
        page += 1
        all_pdf_num += max_num
        pdf_num_dict[page] = max_num
    print("所有数量：", all_pdf_num)
    print("数量分布：", pdf_num_dict)


if __name__ == '__main__':
    # 最大页数2452
    folder = "./上证e互动PDF"
    if not os.path.exists(folder):
        os.makedirs(folder)
    get_sseinfo_pdf_links()

