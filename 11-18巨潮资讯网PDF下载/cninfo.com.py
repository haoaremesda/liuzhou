import os
import time

import requests
import concurrent.futures
import pandas as pd
from datetime import datetime, timedelta
from retrying import retry

headers = {
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cache-Control': 'no-cache',
    # 'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Origin': 'http://www.cninfo.com.cn',
    'Pragma': 'no-cache',
    'Referer': 'http://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search&lastPage=index',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
}


def remove_special_characters(strings):
    special_characters = "|\:*<>?./\""
    return "".join([string for string in strings if not any(char in special_characters for char in string)])


@retry(wait_fixed=5000)
def query_announcements(page, pageSize, seDate) -> tuple:
    global names
    totalpages = 0
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
        totalpages = json_data["totalpages"]
        num = json_data["totalRecordNum"]
        if totalpages * pageSize < num:
            totalpages += 1
        if json_data["announcements"]:
            # print(response.status_code, page, pageSize, seDate, response.text)
            for item in json_data["announcements"]:
                d = []
                for k in ["secCode", "secName", "announcementTitle"]:
                    d.append(remove_special_characters(item[k]))
                datetime_object = datetime.utcfromtimestamp(item["announcementTime"] / 1000)
                # Format the datetime object as a string
                formatted_time = datetime_object.strftime('%Y-%m-%d %H：%M：%S')
                d.append(formatted_time)
                d.append(str(item["announcementId"]))
                file_name = "_".join(d)
                # if file_name in names:
                #     d.append(str(int(time.time()*1e3)))
                #     file_name = "_".join(d)
                try:
                    ks.append({"file_name": file_name, "url": f"http://static.cninfo.com.cn/{item['adjunctUrl']}"})
                    names.append(file_name)
                except:
                    print(item)
        else:
            print(json_data)
    else:
        print(response.status_code, response.text)
    print(page, pageSize, seDate, len(ks))
    return response.status_code, totalpages, ks, num


@retry(wait_fixed=3000)
def save_pdf(pdf_ks: dict, p: str):
    global folder, fail_list
    file_path = f'{p}/{pdf_ks["file_name"]}.{pdf_ks["url"].split(".")[-1]}'
    if not os.path.exists(file_path):
        resp = requests.get(url=pdf_ks["url"], stream=True)
        if resp.status_code == 200:
            with open(f'{file_path}', 'wb') as fd:
                for chunk in resp.iter_content(5120):
                    fd.write(chunk)
        else:
            print(resp.status_code)
            fail_list[file_path] = pdf_ks["url"]


def get_cninfo_pdf_links() -> list:
    likes = []
    PageSize = 30
    # 定义起始日期和结束日期
    start_date = datetime(2012, 7, 1)
    end_date = datetime(2023, 10, 31)
    # 初始化一个空列表来存储日期字符串·
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
        max_totalpages = 0
        max_num = 0
        pdf_num_dict[i] = {}
        while True:
            print(index, page, PageSize, i)
            status_code, max_totalpages, data, max_num = query_announcements(page, PageSize, i)
            if status_code != 200:
                continue
            p = f"{folder}/{i}/{page}"
            if not os.path.exists(p):
                os.makedirs(p)
            # x = []
            # for k in data:
            #     file_path = f'{k["file_name"]}.{k["url"].split(".")[-1]}'
            #     x.append(file_path)
            max_threads = 5
            with concurrent.futures.ThreadPoolExecutor(max_threads) as executor:
                futures = [executor.submit(save_pdf, value, p) for value in data]
                concurrent.futures.wait(futures)
            if not max_totalpages:
                break
            pdf_num_dict[i][page] = len(data)
            if page >= max_totalpages:
                break
            time.sleep(0.5)
            page += 1
        all_pdf_num += max_num
    print("所有数量：", all_pdf_num)
    print("数量分布：", pdf_num_dict)
    print(likes)
    return likes



if __name__ == '__main__':
    names = []
    fail_list = {}
    folder = "./巨潮资讯网PDF"
    if not os.path.exists(folder):
        os.makedirs(folder)
    likes = get_cninfo_pdf_links()

