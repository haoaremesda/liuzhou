import base64
import re
import threading
import time

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from lxml import etree
import os
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


req_session = requests.session()
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'iframe',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

req_session.headers = headers


# 定义一个函数，用于提取行业标准编码
def extract_standard_code(text):
    # 使用正则表达式匹配带斜杠的标准编码模式
    pattern = r'^[A-Z\d\s∕.\-╱]+'
    match = re.search(pattern, text)
    if match:
        return match.group().strip()  # 使用strip()去除可能的前后空格
    else:
        return ""


def get_file_names() -> list:
    # 获取用户输入的目录路径
    directory = input("请输入目录路径: ")
    file_names_without_extension = []
    # 检查输入路径是否存在
    if os.path.exists(directory) and os.path.isdir(directory):
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file == "LIST.TXT" or file == "新建文本文档.bat":
                    continue
                file_names_without_extension.append(file.replace("+", " "))
        # print(f"该目录下有文件数量 {len(file_names_without_extension)}")
    else:
        print("指定的目录路径不存在或不是目录。")
    return file_names_without_extension


def query_samr_gov_state(old_keywords: str):
    old_keywords = old_keywords
    params = {
        'q': old_keywords,
        'tid': '',
    }
    try:
        response = req_session.get('https://std.samr.gov.cn/search/stdPage', params=params, verify=False)
        if response.status_code == 200:
            tree = etree.HTML(response.text)
            # 使用XPath表达式选择所有class为s-title的表格
            tables = tree.xpath('//div[@class="post-head"]/table')
            if not tables:
                return f"未查询到"
            # 遍历每个表格
            for table in tables:
                rows = table.xpath('.//tr')
                # 假设每个表格都有相同数量的行
                for i in rows:
                    tds = i.xpath('.//td')
                    if len(tds) == 2:
                        standard_numbe = tds[0].xpath('./a//text()')
                        standard_numbe = "".join(standard_numbe).replace("\xa0", "").replace(" ", "").replace("/", "").replace("∕", "")
                        keywords_strip = old_keywords.replace("/", "").replace(" ", "")
                        state = tds[1].xpath('./span/text()')
                        if keywords_strip in standard_numbe:
                            return "|".join(state)
        else:
            print(old_keywords, "    查询失败")
    except Exception as e:
        print(e)
    return f"未查询到"


def query_csres_state(keywords):
    url = f"http://www.csres.com/s.jsp?keyword={keywords}&submit12=%B1%EA%D7%BC%CB%D1%CB%F7&xx=on&wss=on&zf=on&fz=on&pageSize=25&pageNum=1&SortIndex=1&WayIndex=0&nowUrl="
    response = requests.get(url=url, headers=headers, verify=False)
    if response.status_code == 200:
        tree = etree.HTML(response.text)
        # 使用XPath表达式选择所有class为s-title的表格
        bzh_list = tree.xpath("//thead[@class='th1']//tr/td[1]/a/font/text()")
        state_list = tree.xpath("//thead[@class='th1']//tr/td[5]/font/text()")
        for bzh, state in zip(bzh_list, state_list):
            bzh = bzh.strip().replace(" ", "").replace("/", "").replace("∕", "")
            keywords = keywords.replace(" ", "").replace("/", "")
            if bzh == keywords or bzh in keywords:
                return state
    else:
        print("query_weboos_state", response.status_code)
    return "未查询到"


def query_zjamr_zj_state(keywords):
    data = base64.b64encode(f"stdNo={keywords}".encode()).decode()
    url = f"https://bz.zjamr.zj.gov.cn/public/std/list/ALL/1.html?data={data}"
    response = requests.get(url=url, headers=headers, verify=False)
    if response.status_code == 200:
        tree = etree.HTML(response.text)
        # 使用XPath表达式选择所有class为s-title的表格
        bzh_list = tree.xpath("//span[@class='list-gb']")
        state_list = tree.xpath("//span[@class='liat-time']")
        for bzh, state in zip(bzh_list, state_list):
            bzh = bzh.text.strip().replace(" ", "").replace("/", "").replace("∕", "")
            keywords = keywords.replace(" ", "").replace("/", "")
            if bzh == keywords or bzh in keywords:
                return state.text.strip()
    else:
        print("query_weboos_state", response.status_code)
    return f"未查询到"


def query_weboos_state(keywords):
    global VIEWSTATE, EVENTVALIDATION
    session = requests.session()
    session.headers = headers
    session.headers["Content-Type"] = "application/x-www-form-urlencoded"
    session.headers["Referer"] = "http://www.weboos.com/"
    if not VIEWSTATE:
        start_url = "http://www.weboos.com/"
        start_resp = session.get(url=start_url, headers=headers, verify=False)
        if start_resp.status_code == 200:
            VIEWSTATE = re.findall(r'__VIEWSTATE" value="(.*?)"', start_resp.text)[0]
            EVENTVALIDATION = re.findall(r'__EVENTVALIDATION" value="(.*?)"', start_resp.text)[0]
    url = "http://www.weboos.com/index.aspx"
    data = {"__VIEWSTATE": VIEWSTATE, "__EVENTVALIDATION": EVENTVALIDATION, "txtQuery": keywords, "btnSearch": "标准搜索", "__EVENTTARGET": "", "__EVENTARGUMENT": ""}
    resp = session.post(url=url, data=data, verify=False)
    if resp.status_code == 200:
        tree = etree.HTML(resp.text)
        # 使用XPath表达式选择所有class为s-title的表格
        bzh_list = tree.xpath("//table[@id='dgList']//tr[2]/td[1]/a")
        state_list = tree.xpath("//table[@id='dgList']//tr[2]/td[4]")
        for bzh, state in zip(bzh_list, state_list):
            bzh = bzh.text.strip().replace(" ", "").replace("/", "").replace("∕", "")
            keywords = keywords.replace(" ", "").replace("/", "")
            if bzh == keywords or bzh in keywords:
                return state.text.strip()
    else:
        print("query_weboos_state", resp.status_code)
    return f"未查询到"


if __name__ == '__main__':
    VIEWSTATE, EVENTVALIDATION = "", ""
    file_names = get_file_names()
    start_time = time.time()
    states = []
    datas = []
    # file_names = {"GBZ 115-2002 X射线衍射仪和荧光分析仪卫生防护标准.pdf": "", "GB∕T 11743-2013 土壤中放射性核素的γ能谱分析方法.pdf": "", "GB∕T 16148-2009 放射性核素摄入量及内照射剂量估算规范.pdf": ""}
    for k in file_names:
        keyword = k
        keyword = extract_standard_code(keyword).strip()
        if not keyword:
            continue
        results = [k]
        threads = []
        keyword = keyword.replace("∕", "/").strip()
        # for fun in [query_samr_gov_state, query_zjamr_zj_state, query_weboos_state]:
        #     thread = threading.Thread(target=lambda: results.append(fun(keyword)))
        #     thread.start()
        #     threads.append(thread)
        # for thread in threads:
        #     thread.join()
        with ThreadPoolExecutor(max_workers=3) as executor:
            # 同时启动三个函数
            futures = [executor.submit(query_samr_gov_state, keyword),
                       executor.submit(query_zjamr_zj_state, keyword),
                       executor.submit(query_weboos_state, keyword)]

            for future in futures:
                result = future.result()
                results.append(result)
        if "废止" in results or "作废" in results:
            results.append("废止")
        elif "现行" in results or "实行中" in results:
            results.append("现行")
        else:
            results.append("未查询到")
        print(results)
        states.append(results)

    df = pd.DataFrame(states, columns=['法规名称', 'https://std.samr.gov.cn/查询结果', 'https://bz.zjamr.zj.gov.cn/查询结果', 'http://www.weboos.com/查询结果', '标准状态'])
    # excel_file = input("请输入指定文件名保存结果: ")
    # # 保存数据框为 Excel 文件
    # if excel_file:
    #     excel_file += '.xlsx'
    # else:
    #     excel_file = 'special_characters.xlsx'
    excel_file = '标准查询.xlsx'
    df.to_excel(excel_file, index=False, engine='openpyxl')
    end_time = time.time()
    print(end_time - start_time)
    # 等待用户输入以结束程序
    # input("结果保存成功按Enter键以结束程序...")
