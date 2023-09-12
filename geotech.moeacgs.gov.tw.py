import os.path
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
    'Referer': 'https://geotech.moeacgs.gov.tw/imoeagis/js/WebWorker/GetProjectList.js?v=0331',
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    'Content-Type': 'application/json; charset=UTF-8',
}

req_session.headers = headers
proxies = {"http": "http://127.0.0.1:4780", "https": "http://127.0.0.1:4780"}


def make_dirs(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"文件夹 '{path}' 创建成功.")
    else:
        print(f"文件夹 '{path}' 已经存在.")


@retry(stop_max_attempt_number=5, wait_random_min=1000, wait_random_max=2000)
def get_content(url: str, data=None, send_type: str = "POST", is_proxies: bool = True, result_null: bool = False) -> list:
    sends = {"url": url, "verify": False}
    if is_proxies:
        sends["proxies"] = proxies
    if send_type == "GET":
        response = req_session.get(**sends)
    else:
        sends["json"] = data
        response = req_session.post(**sends)
    if result_null:
        return []
    return response.json()


def get_drill_projects() -> list:
    url = 'https://geotech.moeacgs.gov.tw/imoeagis/api/DrillProjectsJson/GetDrillProjects'
    drill_data = {
        'sType': 'wkt',
        'sWKT': 'POLYGON((13385311.650344318 2582741.9284753087,13385311.650344318 2590681.824788431,13395219.800135782 2590681.824788431,13395219.800135782 2582741.9284753087,13385311.650344318 2582741.9284753087))',
        'sKeyWord': None,
        'sPlan': '',
        'exename': '',
        'orgname': '',
        'userauth': '',
        'status': None,
        'pagecnt': '1',
    }
    projects = get_content(url=url, data=drill_data, send_type="POST")
    return projects


def get_dr_coords_json(project_key_id: int) -> list:
    url = f'https://geotech.moeacgs.gov.tw/imoeagis/api/DrCoordsJson/{project_key_id}'
    coords_json = get_content(url=url, send_type="GET")
    return coords_json


def get_drill_image(key_id: int) -> list:
    url = f'https://geotech.moeacgs.gov.tw/imoeagis/api/DrillImageJson'
    drill_image = get_content(url=url, data=key_id)
    return drill_image


def get_geo_report(mode: str, project_key_id: int, key_id: int) -> list:
    url = 'https://geotech.moeacgs.gov.tw/imoeagis/api/GeoReport'
    geo_report = {"Mode": mode, "ProjectKeyId": project_key_id, "KeyId": key_id}
    coords_json = get_content(url=url, data=geo_report)
    return coords_json


def save_info(html_string: str, file_path: str):
    # 使用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(html_string, 'html.parser')
    # 找到表格标签
    table = soup.find('table', class_='BaseDataCss')
    # 打开文件以写入模式，如果文件存在则覆盖
    with open(file_path, 'w') as file:
        # 遍历数据字典，将数据写入文件
        for row in table.find_all('tr'):
            # 获取表格行中的标题和数据单元格
            th = row.find('th')
            td = row.find('td')
            file.write(f"{th.text.strip()}: {td.text.strip()}\n")
    # 输出文件已写入
    print(f"数据已写入文件：{file_path}")


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


def spider(dril_obj: dict):
    global folder
    if dril_obj["projName"] is None:
        return False
    path = f"{folder}/{dril_obj['projName']}"
    make_dirs(path)
    coords_list = get_dr_coords_json(dril_obj["keyid"])
    for coord in coords_list:
        coord_path = f"{path}/{coord['holePointNo']}"
        make_dirs(coord_path)
        for mode in ["BaseData", "Test", "Chart", "DrillImage"]:
            mode_data = get_geo_report(mode=mode, project_key_id=coord["projectKeyid"], key_id=coord["keyid"])
            num = 1
            for info in mode_data:
                if mode == "BaseData":
                    info_file_path = f"{coord_path}/基本信息_{num}.txt"
                    # save_info(info, info_file_path)
                    pass
                elif mode == "Test":
                    # 设置Excel文件名
                    excel_file = f"{coord_path}/试验资料_{num}.xlsx"
                    # save_table(info, excel_file)
                elif mode == "Chart":
                    img_file = f"{coord_path}/{coord['holePointNo']}_{num}.jpg"
                    save_chart_img(info, img_file)
                else:
                    pass


def run():
    drill_projects = get_drill_projects()
    drill_projects = [{'exename': '', 'orgname': '08215715 高雄市政府捷運工程局', 'keyid': 6, 'projName': '鹽埕行政中心新建工程', 'projNo': '08215715-A08(4)', 'drillHoleCount': 4, 'sReason': '', 'sStatus': '正常'}]
    max_threads = 20
    with concurrent.futures.ThreadPoolExecutor(max_threads) as executor:
        futures = [executor.submit(spider, value) for value in drill_projects]



if __name__ == '__main__':
    folder = "./项目"
    make_dirs(folder)
    url = "https://geotech.moeacgs.gov.tw/imoeagis/Home/Map"
    get_content(url=url, result_null=True, send_type="GET")
    run()
