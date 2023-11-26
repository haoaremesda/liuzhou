import json
import os
import re
import time

import requests
from datetime import datetime, timedelta
from requests_toolbelt.multipart.encoder import MultipartEncoder
import concurrent.futures
import pandas as pd

req_session = requests.session()
req_session.headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"}


def send_sczwfw_data(url, app_id, interface_id, currentPage, pageSize, fieldValue, timestamp, sign="", json_data=None) -> tuple:
    req_session = requests.session()
    req_session.headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"}
    if not json_data:
        json_data = {
                "app_id": app_id,
                "interface_id": interface_id,
                "charset": "UTF-8",
                "timestamp": timestamp,
                "biz_content": json.dumps({"currentPage": currentPage, "pageSize": pageSize, "conditionList": [
                    {"fieldEn": "zhanming", "fieldValue": fieldValue, "whereCondition": "="}]}),
                "origin": "0",
                "version": "1",
            }
    if sign:
        json_data["sign"] = sign
    multipart_data = MultipartEncoder(
        fields=json_data
    )
    req_session.headers['Content-Type'] = multipart_data.content_type
    req_session.headers['accept'] = 'application/json'
    res = req_session.post(url, data=multipart_data)
    return res.status_code, res.json()


def get_sczwfw_data(key):
    createsign_do_url = "https://tftb.sczwfw.gov.cn:8085/jmas-api-gateway-server/createsign.do"
    gateway_do_url = "https://tftb.sczwfw.gov.cn:8085/jmas-api-gateway-server/gateway.do"
    station_data = []
    total = 0
    page, page_size = 1, 60
    if key in ['雅江（三）', '桐子林（二）']:
        columns = {"zhanming": "站名", "zm": "站码", "hlmc": "河流名称", "xzqh": "行政区划", "lymc": "流域名称",
                   "sw": "水位(m)", "rkll": "入库流量(m³/s)", "ll": "出库流量(m³/s)", "xsl": "蓄水量(百万m²)",
                   "sj": "时间"}
        app_id, interface_id = "sltqszdhdsssqxxpc", "sltqszdhdsssqxx"
    else:
        columns = {"zhanming": "站名", "zm": "站码", "hlmc": "河流名称", "xzqh": "行政区划", "lymc": "流域名称", "ksw": "水位(m)", "rkll": "入库流量(m³/s)", "ckll": "出库流量(m³/s)", "xsl": "蓄水量(百万m²)", "sj": "时间"}
        app_id, interface_id = "sltqszdsksssqxxpc", "sltqszdsksssqxx"
    while True:
        # if page > 30:
        #     break
        if total != 0 and (page_size * page - total) >= page_size:
            break
        timestamp = str(int(time.time() * 1e3))
        try:
            sign_code, sign_json_data = send_sczwfw_data(createsign_do_url, app_id, interface_id, page, page_size, key, timestamp)
        except Exception as e:
            print(e)
            time.sleep(1)
            continue
        if sign_code == 200 and sign_json_data["success"]:
            sign = sign_json_data["data"]["sign"]
            try:
                status_code, json_data = send_sczwfw_data(gateway_do_url, app_id, interface_id, page, page_size, key, timestamp, sign)
            except Exception as e:
                print(e)
                time.sleep(1)
                continue
            if status_code == 200:
                d = json.loads(json_data["data"])
                if d["status"] == 0:
                    if 'list' in d['result']['data']:
                        if total == 0:
                            total = d['result']['data']['total']
                        for item in d['result']['data']['list']:
                            station_data.append([item[s] if s in item else '' for s in columns])
                        print(key, f"第 {page} 页爬取完成")
                        page += 1
                    else:
                        print(d)
                        break
            else:
                print(status_code, json_data)
                time.sleep(10)
        else:
            print(sign_code, sign_json_data)
            time.sleep(10)
            # time.sleep(1)
    return station_data


def run():
    global sczwfw_datas_file_path, sczwfw_summary_file_path
    station_datas = []
    current_date = datetime.now()
    sczwfw_names = ['雅江（三）', '桐子林（二）', '二滩', '锦屏一级', '官地']
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(sczwfw_names)) as executor:  # 最大线程数为4
        # 提交任务给线程池
        futures = {executor.submit(get_sczwfw_data, value): value for value in sczwfw_names}
        # 等待所有线程执行完毕
        done, not_done = concurrent.futures.wait(futures, return_when=concurrent.futures.ALL_COMPLETED)
        # 获取所有线程返回的数据
        for future in done:
            option_value = futures[future]
            try:
                data = future.result()
                station_datas.extend(data)
            except Exception as e:
                print(f"线程发生异常: {e}")
    station_datas.reverse()
    df = pd.DataFrame(station_datas, columns=['站名', '站码', '河流名称', '行政区划', '流域名称', '水位(m)', '入库流量(m³/s)', '出库流量(m³/s)', '蓄水量(百万m²)', '时间'])
    ks = ['水位(m)', '出库流量(m³/s)', "入库流量(m³/s)", "蓄水量(百万m²)"]
    means = {k: 'mean' for k in ks}
    for k in ks:
        df[k] = pd.to_numeric(df[k], errors='coerce')
    df['时间'] = pd.to_datetime(df['时间'])
    df['时间'] = df['时间'].dt.date
    df = df[df['时间'] != current_date.date()]
    result = df.groupby(['站名', '时间']).agg(means).reset_index()
    # 如果文件不存在，创建新的Excel文件并写入数据
    for k in ks:
        pivot_df = result[["时间", "站名", k]].pivot(index='时间', columns='站名', values=k)
        pivot_df.reset_index(inplace=True)
        k = re.sub(r'\(.*\)', '', k)
        path = f'{sczwfw_summary_file_path}/任务3 {k}.csv'
        pivot_df.to_csv(path, index=False)
    df.to_csv(sczwfw_datas_file_path, index=False)


if __name__ == '__main__':
    sczwfw_summary_file_path = './汇总数据'
    if not os.path.exists(sczwfw_summary_file_path):
        os.makedirs(sczwfw_summary_file_path)
    sczwfw_datas_file_path = f'{sczwfw_summary_file_path}/任务三 备份数据.csv'
    fields = ["水位", "出库流量", "入库流量", "蓄水池"]
    run()
    print("任务3执行完成")
