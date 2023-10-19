import json
import time

import requests
from datetime import datetime, timedelta
from requests_toolbelt.multipart.encoder import MultipartEncoder
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


def get_sczwfw_data():
    global sczwfw_data, sczwfw_names, fields
    createsign_do_url = "https://tftb.sczwfw.gov.cn:8085/jmas-api-gateway-server/createsign.do"
    gateway_do_url = "https://tftb.sczwfw.gov.cn:8085/jmas-api-gateway-server/gateway.do"
    for i in sczwfw_names:
        station_datas = []
        total = 0
        page, page_size = 1, 60
        if i in ['雅江（三）', '桐子林（二）']:
            columns = {"zhanming": "站名", "zm": "站码", "sj": "时间", "sw": "水位（m）", "hlmc": "河流名称", "xzqh": "行政区划", "lymc": "流域名称", "ll": "流量(m³/s)"}
            app_id, interface_id = "sltqszdhdsssqxxpc", "sltqszdhdsssqxx"
        else:
            columns = {"zhanming": "站名", "zm": "站码", "hlmc": "河流名称", "xzqh": "行政区划", "lymc": "流域名称", "ksw": "库水位（m）", "rkll": "入库流量（m3/s）", "ckll": "出库流量（m3/s）", "xsl": "蓄水量 (百万m² )", "sj": "时间"}
            app_id, interface_id = "sltqszdsksssqxxpc", "sltqszdsksssqxx"
        while True:
            if total != 0 and (page_size * page - total) >= page_size:
                break
            timestamp = str(int(time.time() * 1e3))
            sign_code, sign_json_data = send_sczwfw_data(createsign_do_url, app_id, interface_id, page, page_size, i, timestamp)
            if sign_code == 200 and sign_json_data["success"]:
                sign = sign_json_data["data"]["sign"]
                status_code, json_data = send_sczwfw_data(gateway_do_url, app_id, interface_id, page, page_size, i, timestamp, sign)
                if status_code == 200:
                    d = json.loads(json_data["data"])
                    if d["status"] == 0:
                        if 'list' in d['result']['data']:
                            if total == 0:
                                total = d['result']['data']['total']
                            for item in d['result']['data']['list']:
                                station_datas.append([item[s] if s in item else '' for s in columns])
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
        station_datas.reverse()
        df = pd.DataFrame(station_datas, columns=list(columns.values()))
        # 将DataFrame保存为Excel文件
        df.to_excel(f'{i}.xlsx', index=False)






if __name__ == '__main__':
    fields = ["水位", "出库流量", "入库流量", "蓄水池"]
    ynswj_names = ['黄登', '大华桥', '苗尾', '功果桥', '小湾', '乌东德', '糯扎渡', '景洪', '溪洛渡水库', '向家坝水库']
    ynswj_data = {i: {s: "-" for s in ynswj_names} for i in fields}
    sczwfw_names = ['雅江（三）', '桐子林（二）', '二滩', '锦屏', '官地']
    sczwfw_data = {}
    # get_ynswj_data()
    # get_schwr_data()
    get_sczwfw_data()
    print(ynswj_data)
