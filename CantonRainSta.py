import os.path
import random
import time
from datetime import datetime, timedelta
import requests
from retrying import retry
import pandas as pd
from openpyxl import Workbook, load_workbook

req_session = requests.session()

headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cache-Control': 'no-cache',
    'Origin': 'http://113.57.190.228:8001',
    'Pragma': 'no-cache',
    'Proxy-Connection': 'keep-alive',
    'Referer': 'http://113.57.190.228:8001/web/Report/CantonRainSta',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
}
req_session.headers = headers
data_dict = {}


def save_data(folder):
    # 遍历字典的键和值
    for key, value in data_dict.items():
        # 将value转换为DataFrame
        df = pd.DataFrame(value)

        # 设置Excel文件名
        excel_file = f"./{folder}/{key}.xlsx"

        # 将DataFrame保存为Excel文件
        df.to_excel(excel_file, index=False, header=False)


@retry(stop_max_attempt_number=5, wait_random_min=1000, wait_random_max=2000)
def get_content(url: str) -> dict:
    response = req_session.post(url, verify=False)
    return response.json()


def run(folder: str, sdate: str, edate: str):
    start_date = datetime.strptime(sdate, "%Y-%m-%d")
    end_date = datetime.strptime(edate, "%Y-%m-%d")
    current_date = start_date
    while current_date < end_date:
        next_day = current_date + timedelta(days=1)
        print(current_date, next_day)
        url = f"http://113.57.190.228:8001/web/report/GetRainReportDetail/?field=ADDVNM&id=420100&sdate={current_date.strftime('%Y-%m-%d')}%2008:00&edate={next_day.strftime('%Y-%m-%d')}%2008:00"
        rain_data = get_content(url)
        if "total" in rain_data and rain_data["total"] > 0:
            for item in rain_data["rows"]:
                if item["STNM"] not in data_dict:
                    data_dict[item["STNM"]] = []
                data = [current_date.strftime('%Y-%m-%d')]
                data.append(item["STNM"])
                data.append(item["RAIN"])
                data_dict[item["STNM"]].append(data)
        current_date += timedelta(days=1)
        time.sleep(random.uniform(0, 1))
    save_data(folder)
    print(f"------------------------ 程序运行结束 ------------------------")


if __name__ == '__main__':
    folder = "武汉市降雨量详细信息"
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"文件夹 '{folder}' 创建成功.")
    else:
        print(f"文件夹 '{folder}' 已经存在.")
    sdate = "2012-01-01"
    edate = "2023-07-31"
    run(folder, sdate, edate)
