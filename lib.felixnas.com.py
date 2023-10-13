import threading
import time

import requests
import os
import concurrent.futures

R = threading.Lock()

req_session = requests.session()
req_session.headers = {"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                       "Referer": "https://lib.felixnas.com/login"}

err_list = []

def login() -> bool:
    sign_in_url = "https://lib.felixnas.com/api/user/sign_in"
    sign_in_data = {"username": "haoaremesda", "password": "jyh789789"}
    try:
        resp = req_session.post(url=sign_in_url, data=sign_in_data)
        print(resp.text)
        return True
    except Exception as e:
        print("登录异常", e)
    return False


def get_href_tag(book_id: int) -> list:
    url = f"https://lib.felixnas.com/api/book/{book_id}"
    resp = req_session.get(url=url)
    if resp.status_code == 200:
        result = resp.json()
        if result["err"] == "ok":
            return [result["book"]["files"], result["book"]["title"], result["book"]["tag"]]
    return []


def download_pdf(url_end: str, title: str, tag: str):
    download_url = f"https://lib.felixnas.com{url_end}"
    resp = req_session.get(url=download_url, stream=True)
    if resp.status_code == 200:
        if tag.strip() == "":
            tag = "暂无标签"
        elif len(tag) > 50:
            tag = tag[:50]
        tag = tag.replace(":", " ").replace("/", "&").strip().replace("?", " ").replace('"', '')
        dir_path = f"./books/{tag}"
        R.acquire()
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        R.release()
        title = title.replace(":", " ").replace("/", "&").replace("?", " ").replace('"', '')
        file_path = f'{dir_path}/{title}.{url_end.split(".")[1]}'
        if os.path.exists(file_path):
            pass
        else:
            try:
                with open(f'{file_path}', 'wb') as fd:
                    for chunk in resp.iter_content(5120):
                        fd.write(chunk)
            except Exception as e:
                print(e)
            import time
            now = time.time()
            timeArray = time.localtime(now)
            otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
            print(otherStyleTime, "下载完成", url_end)
    else:
        print(resp.status_code, url_end, title)
        err_list.append([url_end, title, tag])


def run(recent_url: str):
    resp = req_session.get(url=recent_url)
    if resp.status_code == 200:
        for ids in resp.json()["books"]:
            href_tag = get_href_tag(ids["id"])
            if href_tag:
                for f in href_tag[0]:
                    download_pdf(f["href"], href_tag[1], href_tag[2])


if __name__ == '__main__':
    max_size = 1917
    recents = []
    for i in range(1800, 1917, 60):
        url = f"https://lib.felixnas.com/api/recent?start={i}&size=60"
        recents.append(url)
    MAX_WORKERS = 1
    if login():
        # 创建线程池
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:  # 最大线程数为5
            # 提交任务给线程池
            futures = {executor.submit(run, value): value for value in recents}
            # 获取线程返回的数据
            for future in concurrent.futures.as_completed(futures):
                option_value = futures[future]
                try:
                    data = future.result()
                except Exception as e:
                    print(f"线程发生异常: {e}")
        for i in err_list:
            download_pdf(*i)
    else:
        print("登录失败")
