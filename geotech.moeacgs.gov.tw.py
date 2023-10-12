import copy
import os.path

import chardet as chardet
import requests
from retrying import retry
import pandas as pd
import concurrent.futures
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from bs4 import BeautifulSoup
import base64
from io import BytesIO
from PIL import Image

# 禁用安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

req_session = requests.session()

headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Referer': 'https://geotech.moeacgs.gov.tw/imoeagis/js/WebWorker/GetGeoReport.js?v=1695029799130',
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.31',
    'Content-Type': 'application/json; charset=UTF-8',
}

req_session.headers = headers

# 设置代理
proxies = {"http": "http://127.0.0.1:4780", "https": "http://127.0.0.1:4780"}


projects_num = {}


def make_dirs(path):
    if not os.path.exists(path):
        os.makedirs(path)
        # print(f"文件夹 '{path}' 创建成功.")
    else:
        # print(f"文件夹 '{path}' 已经存在.")
        pass


def remove_special_characters(strings):
    special_characters = "!$%^&*{}[]|\:;'<>?./\""
    return "".join([string for string in strings if not any(char in special_characters for char in string)])


@retry(wait_fixed=2000)
def get_content(url: str, data=None, send_type: str = "POST", is_proxies: bool = True,
                result_null: bool = False) -> list:
    sends = {"url": url, "verify": False}
    if is_proxies:
        sends["proxies"] = proxies
    if send_type == "GET":
        response = req_session.get(**sends)
    else:
        sends["json"] = data
        response = req_session.post(**sends)
    if response.status_code == 404:
        return []
    if result_null:
        return []
    return response.json()


def get_drill_projects() -> list:
    url = 'https://geotech.moeacgs.gov.tw/imoeagis/api/DrillProjectsJson/GetDrillProjects'
    drill_data = {"sType": "search", "sWKT": "", "sKeyWord": "", "sPlan": "", "exename": "", "orgname": "",
                  "userauth": "", "status": None, "pagecnt": "1"}
    projects = get_content(url=url, data=drill_data, send_type="POST")
    return projects


def get_dr_coords_json(project_key_id: int) -> list:
    url = f'https://geotech.moeacgs.gov.tw/imoeagis/api/DrCoordsJson/{project_key_id}'
    coords_json = get_content(url=url, send_type="GET")
    return coords_json


def get_drill_image(key_id: int) -> list:
    url = 'https://geotech.moeacgs.gov.tw/imoeagis/api/DrillImageJson'
    drill_image = get_content(url=url, data=key_id)
    return drill_image


def get_geo_report(mode: str, project_key_id: int, key_id: int) -> list:
    url = 'https://geotech.moeacgs.gov.tw/imoeagis/api/GeoReport'
    geo_report = {"Mode": mode, "ProjectKeyId": project_key_id, "KeyId": key_id}
    coords_json = get_content(url=url, data=geo_report)
    return coords_json


def save_info(html_string: str, file_path: str) -> list:
    # 使用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(html_string, 'html.parser')
    # 找到表格标签
    table = soup.find('table', class_='BaseDataCss')
    item = []
    # 打开文件以写入模式，如果文件存在则覆盖
    with open(file_path, 'w', encoding="utf-8") as file:
        # 遍历数据字典，将数据写入文件
        for row in table.find_all('tr'):
            # 获取表格行中的标题和数据单元格
            th = row.find('th')
            td = row.find('td')
            td_text = td.text.replace('\r', '').replace('\n', '').strip().replace('聯', '').replace('行', '行')
            item.append(td_text)
            file.write(f"{th.text.strip()}:     {td_text}\n")
    # 输出文件已写入
    # print(f"数据已写入文件：{file_path}")
    return item


def save_table(html_string, excel_file):
    soup = BeautifulSoup(html_string, 'html.parser')
    # 找到表格标签
    tables = soup.find_all('table')
    data_rows = []
    # 处理每个表格
    for table in tables:
        # 获取表头中的标题文本
        headers = [element.get_text(strip=True) for element in table.select('thead th, thead td')]
        data_rows.append(headers)
        # 获取数据单元格文本
        data = [element.get_text(strip=True) for element in table.select('tbody th, tbody td')]
        data_rows.append(data)
    df = pd.DataFrame(data_rows)
    # 将DataFrame保存为Excel文件
    df.to_excel(excel_file, index=False, header=False)


def save_chart_img(html_string, img_file):
    soup = BeautifulSoup(html_string, 'html.parser')
    # 找到表格标签
    img_tag = soup.find('img')
    # 从 Base64 数据中提取图像数据
    image_data = img_tag.get('src').split(",")[1]  # 去除"data:image/jpeg;base64,"前缀
    # 解码 Base64 数据
    decoded_data = base64.b64decode(image_data)
    # 创建一个字节流对象
    image_stream = BytesIO(decoded_data)
    # 打开图像
    image = Image.open(image_stream)
    image = image.convert("RGB")
    # 保存为 JPG 文件
    image.save(img_file, "JPEG")
    # 关闭字节流对象
    image_stream.close()


def save_drill_img(image_data, img_file):
    if not image_data:
        return
    image_data = image_data['imagePath'].split(",")[1]  # 去除"data:image/jpeg;base64,"前缀
    # 解码 Base64 数据
    decoded_data = base64.b64decode(image_data)
    # 创建一个字节流对象
    image_stream = BytesIO(decoded_data)
    # 打开图像
    image = Image.open(image_stream)
    image = image.convert("RGB")
    # 保存为 JPG 文件
    image.save(img_file, "JPEG")
    # 关闭字节流对象
    image_stream.close()


def spider_coord(coord: dict, path: str) -> list:
    spider_data = []
    coord['holePointNo'] = remove_special_characters(coord['holePointNo']).replace("\r", "").replace("\n", "")
    coord_path = f"{path}/{coord['holePointNo']}".strip()
    make_dirs(coord_path)
    for mode in ["BaseData", "Test", "Chart", "DrillImage"]:
        if mode == "DrillImage":
            mode_data = get_drill_image(key_id=coord["keyid"])
        else:
            mode_data = get_geo_report(mode=mode, project_key_id=coord["projectKeyid"], key_id=coord["keyid"])
        num = 1
        for info in mode_data:
            if mode == "BaseData":
                info_file_path = f"{coord_path}/基本信息_{num}.txt"
                coord_info = save_info(info, info_file_path)
                if coord_info:
                    spider_data = coord_info
            elif mode == "Test":
                # 设置Excel文件名
                excel_file = f"{coord_path}/试验资料_{num}.xlsx"
                save_table(info, excel_file)
            elif mode == "Chart":
                img_file = f"{coord_path}/{coord['holePointNo']}_{num}.jpg"
                save_chart_img(info, img_file)
            else:
                img_file = f"{coord_path}/{coord['holePointNo']}_岩心照片_{num}.jpg"
                save_drill_img(info, img_file)
    print(coord["keyid"])
    return spider_data


def spider(dril_obj: dict):
    global folder
    # dril_obj['projName'] = remove_special_characters(dril_obj['projName']).replace("\r", "").replace("\n", "").strip()
    path = f"{folder}/{dril_obj['projName']}"
    if os.path.exists(path):
        return
    print(dril_obj['projName'], "---正在开始")
    make_dirs(path)
    coords_list = get_dr_coords_json(dril_obj["keyid"])
    projects_num[dril_obj['projName']] = len(coords_list)
    max_threads = 10
    with concurrent.futures.ThreadPoolExecutor(max_threads) as executor:
        futures = [executor.submit(spider_coord, value, path) for value in coords_list]
        concurrent.futures.wait(futures)
        # results = [future.result() for future in futures if future.result()]
    print(dril_obj['projName'], "---爬取结束")


def run():
    global folder
    drill_projects = get_drill_projects()
    drill_projects2 = []
    for i in drill_projects:
        if i["projName"] is None:
            continue
        i['projName'] = remove_special_characters(i['projName']).strip().replace("\r", "").replace("\n", "")
        path = f"{folder}/{remove_special_characters(i['projName'])}"
        if os.path.exists(path):
            continue
        drill_projects2.append(i)
    print("需要爬取的项目数量：", len(drill_projects2))
    # 创建标题行数据
    datas = [["鑽孔編號", "鑽孔工程名稱", "計畫編號", "鑽孔地點", "鑽孔地表高程", "座標系統", "孔口X座標", "孔口Y座標",
              "鑽探起始日期", "鑽探完成日期", "鑽機機型", "鑽孔總總深度", "鑽探公司"]]
    max_threads = 5
    with concurrent.futures.ThreadPoolExecutor(max_threads) as executor:
        futures = [executor.submit(spider, value) for value in drill_projects2]
        concurrent.futures.wait(futures)
    items = os.listdir(folder)
    subfolders = [item for item in items if os.path.isdir(os.path.join(folder, item))]
    for subfolder in subfolders:
        subfolderx = f"{folder}/{subfolder}"
        # 遍历目录下的文件夹
        for folder_name in os.listdir(subfolderx):
            folder_pathx = os.path.join(subfolderx, folder_name)
            # 检查是否是文件夹
            if os.path.isdir(folder_pathx):
                # 构建基本信息_1.txt文件的完整路径
                file_path = os.path.join(folder_pathx, '基本信息_1.txt')
                # 检查文件是否存在
                if os.path.exists(file_path):
                    # 使用检测到的编码方式打开文件并读取内容
                    with open(file_path, 'rb') as file:
                        raw_data = file.read()
                        result = chardet.detect(raw_data)
                        file_encoding = result['encoding']
                        if file_encoding == "GB2312":
                            file_encoding = "GBK"
                    with open(file_path, 'r', encoding=file_encoding) as file:
                        file_content = file.read()
                        # 初始化一个空列表
                        data_list = []
                        # 以换行符分割文本内容
                        lines = file_content.split('\n')
                        # 遍历每一行
                        for line in lines:
                            # 使用冒号分割每行，获取右侧的值
                            if not line or ":" not in line:
                                continue
                            if "鑽孔工程名稱" in line:
                                data_list.append(subfolder)
                                continue
                            try:
                                d = line.split(':')
                                value = "".join(d[1:])
                            except:
                                print(line)
                            # 去除多余的空格并添加到列表
                            data_list.append(value.strip())
                        datas.append(data_list)
                    # 在这里可以对文件内容进行处理，例如打印或者存储到另一个地方
                else:
                    datas.append([folder_name, subfolder])
    df = pd.DataFrame(datas)
    df.to_excel(f"{folder}/汇总表.xlsx", index=False, header=False)


if __name__ == '__main__':
    folder = "./项目"
    make_dirs(folder)
    url = "https://geotech.moeacgs.gov.tw/imoeagis/Home/Map"
    get_content(url=url, result_null=True, send_type="GET")
    run()
