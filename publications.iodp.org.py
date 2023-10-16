import os
from lxml import etree
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import requests
import concurrent.futures

# 禁用安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

headers = {
    'authority': 'doi.org',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'referer': 'http://publications.iodp.org/',
    'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'cross-site',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
}

# proxies = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
proxies = {}


def init_req() -> requests.sessions.Session:
    req_session = requests.session()
    req_session.headers = headers
    return req_session


def parse_url_list(index_url: str) -> list:
    url_list = []
    try:
        req_session = init_req()
        req = req_session.get(url=index_url, verify=False, proxies=proxies)
        if req.status_code == 200:
            # 使用解析器解析 HTML 字符串
            html_text = req.text
            tree = etree.HTML(html_text)
            url_list = tree.xpath("//a[starts-with(@href, 'https://doi.org')]/@href")
    except Exception as e:
        print(f"------------------------ 解析URL异常 {e} ------------------------")
    return list(set(url_list))


def save_pdf(sp_url: str):
    global folder
    req_session = init_req()
    resp = req_session.get(url=sp_url, verify=False, proxies=proxies)
    if resp.status_code == 200:
        tree = etree.HTML(resp.text.encode('utf-8'))
        pdf_urls = tree.xpath("//a[substring(@href, string-length(@href) - 3) = '.PDF']/@href")
        for u in list(set(pdf_urls)):
            s = resp.url.split("/")[:-1]
            path_folder = f"{folder}/{s[-1:][0]}/{s[3:4][0]}"
            if not os.path.exists(path_folder):
                os.makedirs(path_folder)
            if resp.url.endswith("/"):
                url = resp.url + u
            else:
                s.append(u)
                url = "/".join(s)
            u = u.replace("/", "&")
            max_retries = 3
            for _ in range(max_retries):
                try:
                    pdf_resp = req_session.get(url=url, stream=True, verify=False, timeout=120)
                    with open(f'{path_folder}/{u}', 'wb') as fd:
                        for chunk in pdf_resp.iter_content(5120):
                            fd.write(chunk)
                    break  # 如果下载成功，退出循环
                except Exception as e:
                    print(url, f"An error occurred: {str(e)}")
            print("爬取完成：", f'{path_folder}/{u}')
    else:
        print(resp.status_code, resp.text)


if __name__ == '__main__':
    folder = "./iodp_pdfs"
    url = "http://publications.iodp.org/index.html"
    url_list = parse_url_list(url)
    # url_list = ["https://doi.org/10.2204/iodp.sp.349.2013", "https://doi.org/10.14379/iodp.pr.349.2014", "https://doi.org/10.14379/iodp.proc.349.2015"]
    max_threads = 3
    with concurrent.futures.ThreadPoolExecutor(max_threads) as executor:
        futures = [executor.submit(save_pdf, value) for value in url_list]
        concurrent.futures.wait(futures)
        processed_data = []
        for future in futures:
            try:
                result = future.result()
                processed_data.append(result)
                print(f"Processed: {result}")
            except Exception as e:
                print(f"Error processing : {e}")
