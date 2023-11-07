import csv

import requests

requests.packages.urllib3.disable_warnings()


headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'Origin': 'https://www.mgtv.com',
    'Referer': 'https://www.mgtv.com/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Chromium";v="118", "Google Chrome";v="118", "Not=A?Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}


def get_barrage(url: str) -> list:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        resp = response.json()
        if resp["status"] == 0 and resp["data"]["total"] > 0:
            return resp["data"]["items"]
    print(response.text)
    return []


def get_barrage_url(vid: str) -> str:
    params = {
        'version': '8.1.5-1',
        'abroad': '0',
        'uuid': '',
        'os': '10.0',
        'platform': '0',
        'deviceid': 'b96469f5-631b-4b54-a0f0-cb0aaaa525c5',
        'mac': '',
        'vid': vid,
        'pid': '',
        'cid': '457910',
        'ticket': '',
    }

    response = requests.get('https://galaxy.bz.mgtv.com/getctlbarrage', params=params, headers=headers, verify=False)
    if response.status_code == 200:
        resp = response.json()
        if resp["status"] == 0 and resp["data"]["cdn_version"]:
            start_url = resp["data"]["cdn_list"].split(",")[0]
            end_url = resp["data"]["cdn_version"]
            return f"https://{start_url}/{end_url}"
    print(response.text)
    return ""


def get_showlist(month: str) -> list:
    params = {
        'allowedRC': '1',
        'collection_id': '457910',
        'month': month,
        'page': '1',
        '_support': '10000000',
    }
    response = requests.get('https://pcweb.api.mgtv.com/variety/showlist', params=params, headers=headers, verify=False)
    if response.status_code == 200:
        resp = response.json()
        if resp["code"] == 200 and resp["data"]["total"] > 0:
            return resp["data"]["list"]
    print("get_showlist：", response.json())
    return []


if __name__ == '__main__':
    # CSV文件路径
    csv_file = "快乐再出发弹幕.csv"
    # 表头
    item_header = ["isvip", "clip_id", "img", "playcnt", "t1", "t2", "t3", "time", "video_id", "url"]
    end_header = ["content", "send_time", "type", "uid", "v2_up_count"]
    header = ["节目名称", "是否需要VIP", "节目ID", "每期背景图", "每期播放量", "每期标题", "发布日期", "每期详细标题", "每期时常", "期ID", "期URL",
              "弹幕内容", "弹幕发送时间", "类型", "用户ID", "弹幕点赞量"]
    months = ["202207", "202208"]
    for i in months:
        showlist = get_showlist(i)
        for v in showlist:
            time_len = v["time"]
            barrage_url = get_barrage_url(v["video_id"])
            if not barrage_url:
                continue
            l = int(time_len.split(":")[0])
            for t in range(l + 1):
                data_list = []
                v_barrage_url = f"{barrage_url}/{t}.json"
                barrages = get_barrage(v_barrage_url)
                for item in barrages:
                    d = ["快乐再出发"] + [v[k] for k in item_header[:-1]]
                    d.append(f"https://www.mgtv.com{v['url']}")
                    d.append(item["content"])
                    d.append(item["time"])
                    d.append(item["type"])
                    d.append(item["uid"])
                    d.append(item["v2_up_count"] if "v2_up_count" in item else 0)
                    data_list.append(d)
                if not data_list:
                    continue
                # 打开CSV文件，使用追加模式
                with open(csv_file, mode='a', newline='', encoding='utf-8-sig') as file:
                    writer = csv.writer(file)
                    # 写入表头
                    if file.tell() == 0:  # 只有在文件为空时写入表头
                        writer.writerow(header)
                    # 一次性追加多条数据
                    writer.writerows(data_list)
