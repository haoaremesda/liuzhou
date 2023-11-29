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
from hashlib import md5

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

# proxies = {"http": "http://127.0.0.1:4780", "https": "http://127.0.0.1:4780"}

tunnel = "f693.kdltps.com:15818"

proxies = {
    "http": "http://%(proxy)s/" % {"proxy": tunnel},
    "https": "http://%(proxy)s/" % {"proxy": tunnel}
}


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


@retry(wait_fixed=3000)
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
    status_code = response.status_code
    if status_code == 200:
        if "暂时没有上市公司发布" in response.text:
            come_to_an_end = True
        else:
            tree = etree.HTML(response.text)
            feed_details = tree.xpath('//div[@class="m_feed_detail"]')
            for feed_div in feed_details:
                company_names = feed_div.xpath('.//div[@class="m_feed_face"]/p/text()')
                file_urls = feed_div.xpath('.//div[@class="m_feed_txt"]/a/@href')
                file_names = feed_div.xpath('.//div[@class="m_feed_txt"]/a/text()')
                released_time = feed_div.xpath('.//div[@class="m_feed_from"]/span/text()')
                if company_names and file_urls and file_names and released_time:
                    released_time = [convert_to_datetime(item) for item in released_time]
                    # 命名：公司简称-公告标题-公告时间
                    d = file_names[0].split(".")
                    d.insert(0, company_names[0])
                    d.insert(-1, released_time[0])
                    d.insert(-1, md5(file_urls[0].encode()).hexdigest())
                    ks.append({"file_name": remove_special_characters("_".join(d[:-1])), "url": file_urls[0]})
    else:
        print(response.status_code, response.text)
    num = len(ks)
    return status_code, num, ks, come_to_an_end


@retry(wait_fixed=3000)
def save_pdf(pdf_ks: dict):
    global folder, fail_list
    file_path = f'{folder}/{pdf_ks["file_name"]}.{pdf_ks["url"].split(".")[-1]}'
    if not os.path.exists(file_path):
        resp = requests.get(url=pdf_ks["url"], proxies=proxies, stream=True)
        if resp.status_code == 200:
            with open(f'{file_path}', 'wb') as fd:
                for chunk in resp.iter_content(5120):
                    fd.write(chunk)
            print("爬取完成：", file_path)
        else:
            print(resp.status_code)
            fail_list[file_path] = pdf_ks["url"]


def get_sseinfo_pdf_links():
    page = 2242
    all_pdf_num = 0
    pdf_num_dict = {}
    while True:
        status_code, max_num, data, come_to_an_end = query_feeds(page, 10)
        if status_code != 200:
            continue
        print(max_num, come_to_an_end)
        # if come_to_an_end:
        #     break
        max_threads = 5
        with concurrent.futures.ThreadPoolExecutor(max_threads) as executor:
            futures = [executor.submit(save_pdf, value) for value in data]
            concurrent.futures.wait(futures)
        # time.sleep(2)
        if page >= 2466:
            break
        page += 1
        all_pdf_num += max_num
        pdf_num_dict[page] = max_num
    print("所有数量：", all_pdf_num)
    print("数量分布：", pdf_num_dict)


if __name__ == '__main__':
    fail_list = {}
    # 最大页数2452
    folder = "./上证e互动PDF"
    if not os.path.exists(folder):
        os.makedirs(folder)
    get_sseinfo_pdf_links()

