import os
from lxml import etree
import requests
import concurrent.futures

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

proxies = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}


def init_req() -> requests.sessions.Session:
    req_session = requests.session()
    req_session.headers = headers
    return req_session


def parse_url_list(index_url: str) -> list:
    url_list = []
    try:
        req_session = init_req()
        req = req_session.get(url=index_url, proxies=proxies)
        if req.status_code == 200:
            # 使用解析器解析 HTML 字符串
            html_text = req.text
            tree = etree.HTML(html_text)
            url_list = tree.xpath("//a[starts-with(text(), 'Volume')]/@href")
    except Exception as e:
        print(f"------------------------ 解析URL异常 {e} ------------------------")
    return list(set(url_list))


def parse_pdf_url_list(urls: list) -> list:
    url_list = []
    req_session = init_req()
    for i in urls:
        index_url = f"http://www.deepseadrilling.org/{i}"
        try:
            req = req_session.get(url=index_url, proxies=proxies)
            if req.status_code == 200:
                # 使用解析器解析 HTML 字符串
                html_text = req.text
                tree = etree.HTML(html_text)
                href_list = tree.xpath("//a[substring(@href, string-length(@href) - 3) = '.pdf']/@href")
                if href_list:
                    for x in href_list:
                        if ".." in x:
                            x = x.replace("..", "")
                            url_list.append(f"http://www.deepseadrilling.org{x}")
                        else:
                            doman = i.split('/')[:-1]
                            url_list.append(f"{'/'.join(doman)}/{x}")
        except Exception as e:
            print(f"------------------------ 解析URL异常 {e} ------------------------")
    return list(set(url_list))


def save_pdf(pdf_url: str):
    global folder
    req_session = init_req()
    pdf_resp = req_session.get(url=pdf_url, stream=True)
    if pdf_resp.status_code == 200:
        s = pdf_url.split("/")
        path_folder = f"{folder}/{s[3]}"
        if not os.path.exists(path_folder):
            os.makedirs(path_folder)
        with open(f'{path_folder}/{s[5]}', 'wb') as fd:
            for chunk in pdf_resp.iter_content(5120):
                fd.write(chunk)
        print("爬取完成：", pdf_url)
    else:
        print(pdf_url, pdf_resp.status_code, pdf_resp.text)


if __name__ == '__main__':
    folder = "./deepseadrilling_pdfs"
    url = "http://www.deepseadrilling.org/i_reports.htm"
    url_list = parse_url_list(url)
    # url_list = ["http://www.deepseadrilling.org/87/dsdp_toc.htm"]
    pdf_url_list = parse_pdf_url_list(url_list)
    max_threads = 1
    with concurrent.futures.ThreadPoolExecutor(max_threads) as executor:
        futures = [executor.submit(save_pdf, value) for value in pdf_url_list]
        concurrent.futures.wait(futures)
        processed_data = []
        for future in futures:
            try:
                result = future.result()
                processed_data.append(result)
            except Exception as e:
                print(f"Error processing : {e}")
