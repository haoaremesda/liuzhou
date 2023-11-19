import time

import requests
import concurrent.futures
import pandas as pd
from datetime import datetime, timedelta

headers = {
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Origin': 'http://www.cninfo.com.cn',
    'Pragma': 'no-cache',
    'Referer': 'http://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search&lastPage=index',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
}


def query_announcements(page, pageSize, seDate) -> tuple:
    num = 0
    ks = []
    data = {
        'pageNum': page,
        'pageSize': pageSize,
        'column': 'szse',
        'tabName': 'relation',
        'plate': '',
        'stock': '',
        'searchkey': '',
        'secid': '',
        'category': '',
        'trade': '',
        'seDate': seDate,
        'sortName': '',
        'sortType': '',
        'isHLtitle': 'true',
    }
    response = requests.post(
        'http://www.cninfo.com.cn/new/hisAnnouncement/query',
        headers=headers,
        data=data,
        verify=False,
    )
    if response.status_code == 200:
        json_data = response.json()
        if json_data["announcements"]:
            print(response.status_code, page, pageSize, seDate, response.text)
            for item in json_data["announcements"]:
                d = []
                for k in ["secCode", "secName", "announcementTitle"]:
                    d.append(item[k])
                datetime_object = datetime.utcfromtimestamp(item["announcementTime"] / 1000)
                # Format the datetime object as a string
                formatted_time = datetime_object.strftime('%Y-%m-%d %H:%M:%S')
                d.append(formatted_time)
                try:
                    ks.append({"_".join(d): f"http://static.cninfo.com.cn/{item['adjunctUrl']}"})
                except:
                    print(item)
            num = json_data["totalAnnouncement"]
    return num, ks


if __name__ == '__main__':
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
    for i in date_strings:
        page = 1
        max_num = 0
        while True:
            max_num, data = query_announcements(page, PageSize, i)
            if not max_num:
                break
            likes.extend(data)
            if max_num < page * PageSize:
                break
            time.sleep(0.5)
            page += 1

    print(likes)