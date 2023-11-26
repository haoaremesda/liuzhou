import os
import time

import requests
from datetime import datetime, timedelta
from requests_toolbelt.multipart.encoder import MultipartEncoder
from apscheduler.schedulers.blocking import BlockingScheduler
import pandas as pd

req_session = requests.session()
req_session.headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"}


def get_ynswj_data():
    global ynswj_data, ynswj_names
    # 获取今天的日期
    today = datetime.now().date()
    # 获取昨天的日期
    yesterday = today - timedelta(days=1)
    # 将日期转换为字符串
    today_str = today.strftime('%Y-%m-%d')
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    url = f"http://www.ynswj.cn/webapi/api/v1/water?itm=1&no_data_visible=true&time=[{yesterday_str}%2008:00:00,{today_str}%208:00:00]&sttp=RR&station_type=4,5"
    res = req_session.get(url=url)
    if res.status_code == 200:
        if res.json()["data"]:
            for i in res.json()["data"]:
                if i["name"] in ynswj_names:
                    ynswj_data["水位"][i["name"]] = str(i["val"]) if i["val"] else "-"
                    ynswj_data["出库流量"][i["name"]] = str(i["out_val"]) if i["out_val"] else "-"
                    ynswj_data["入库流量"][i["name"]] = str(i["in_val"]) if i["in_val"] else "-"
                    ynswj_data["蓄水池"][i["name"]] = str(i["capacity"]) if i["capacity"] else "-"


def get_schwr_data():
    global ynswj_data, ynswj_names
    t = int(time.time() * 1e3)
    url = f"http://www.schwr.com:8088/api/sl/stRsvrR/listNew?t={t}"
    res = req_session.get(url=url)
    if res.status_code == 200:
        d = res.json()
        if d["code"] == 200 and d["result"]:
            for i in d["result"]:
                if i["stnm"] in ynswj_names:
                    ynswj_data["水位"][i["stnm"]] = str(i["rz"]) if i["rz"] else "-"
                    ynswj_data["出库流量"][i["stnm"]] = str(i["otq"]) if i["otq"] else "-"
                    ynswj_data["入库流量"][i["stnm"]] = str(i["inq"]) if i["inq"] else "-"
                    ynswj_data["蓄水池"][i["stnm"]] = str(i["w"]) if i["w"] else "-"


def run():
    get_ynswj_data()
    get_schwr_data()
    for c in ynswj_data.items():
        columns = ["时间"] + list(c[1].keys())
        values = [[datetime.now().strftime("%Y-%m-%d")] + list(c[1].values())]
        df = pd.DataFrame(values, columns=columns)
        path = f'{sczwfw_summary_file_path}/任务1&2 {c[0]}.csv'
        if os.path.exists(path):
            df.to_csv(path, mode='a', header=False, index=False)
        else:
            df.to_csv(path, index=False)
    print("任务1&2执行完成")


if __name__ == '__main__':
    sczwfw_summary_file_path = './汇总数据'
    if not os.path.exists(sczwfw_summary_file_path):
        os.makedirs(sczwfw_summary_file_path)
    fields = ["水位", "出库流量", "入库流量", "蓄水池"]
    ynswj_names = ['黄登', '大华桥', '苗尾', '功果桥', '小湾', '乌东德水库', '糯扎渡', '景洪', '溪洛渡水库', '向家坝水库']
    ynswj_data = {i: {s: "-" for s in ynswj_names} for i in fields}
    run()
    # 创建调度器
    scheduler = BlockingScheduler()
    # 添加定时任务，每天下午两点执行一次
    scheduler.add_job(run, 'cron', hour=15, minute=00)
    try:
        # 开始调度器
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        # 如果需要手动停止程序，按下Ctrl+C
        pass
    print(ynswj_data)
