import requests
from retrying import retry
from bs4 import BeautifulSoup
import re

headers = {
    'authority': 'vetcardiomed.edrapublishing.com',
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'accept-language': 'zh-CN,zh;q=0.9',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'referer': 'https://vetcardiomed.edrapublishing.com/',
    'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
}

proxies = {"http": "http://127.0.0.1:4780", "https": "http://127.0.0.1:4780"}


@retry(wait_fixed=3000)
def get_video_urls():
    urls = []
    for i in range(1, 14):
        params = {
            'id_capitolo': str(i),
        }
        response = requests.get(
            'https://vetcardiomed.edrapublishing.com/ajax/mostra_contenuti.php',
            params=params,
            headers=headers,
            proxies=proxies
        )
        if response.status_code == 200:
            json_data = response.json()
            html_content = json_data["contenuto"]
            soup = BeautifulSoup(html_content, "html.parser")
            # 查找所有包含视频路径的div元素
            video_divs = soup.find_all("div", {"class": "video"})

            # 遍历所有视频路径
            for video_div in video_divs:
                # 获取视频路径
                video_path = video_div.find("div", {"class": "path"}).text.strip()
                # print("Video Path:", video_path)
                urls.append(video_path)
        # print(response.text)
    return list(set(urls))


@retry(wait_fixed=3000)
def get_master_m3u8(url: str):
    response = requests.get(url, headers=headers, proxies=proxies)
    if response.status_code == 200:
        m3u8_url = re.findall(r'"avc_url":"(.*?)","origin":"gcs', response.text)
        m3u8_url = m3u8_url[0].split("/")[:-1]
        m3u8_url.append("master.m3u8?query_string_ranges=1&=")
        return "/".join(m3u8_url)
    return ""


@retry(wait_fixed=3000)
def get_master_m3u8_url(url: str) -> list:
    response = requests.get(url, headers=headers, proxies=proxies)
    if response.status_code == 200:
        pattern = re.compile(r'#EXT-X-STREAM-INF:.*?RESOLUTION=(\d+x\d+).*?\n(.*?)\n')
        matches = pattern.findall(response.text)
        resolutions_and_urls = {resolution: url for resolution, url in matches}
        # 按照分辨率排序
        sorted_resolutions_and_urls = dict(sorted(resolutions_and_urls.items(), key=lambda x: tuple(map(int, x[0].split('x')))))
        m3u8_list = list(sorted_resolutions_and_urls.values())
        return m3u8_list
    return []


if __name__ == '__main__':
    # video_urls = get_video_urls()
    # print(video_urls)
    video_urls = ['https://player.vimeo.com/video/827225233',
                  'https://player.vimeo.com/video/827227400',
                  'https://player.vimeo.com/video/835327105',
                  'https://player.vimeo.com/video/827224406',
                  'https://player.vimeo.com/video/827224611',
                  'https://player.vimeo.com/video/827233339',
                  'https://player.vimeo.com/video/827228187',
                  'https://player.vimeo.com/video/827232810',
                  'https://player.vimeo.com/video/827228991',
                  'https://player.vimeo.com/video/827223448',
                  'https://player.vimeo.com/video/827233031',
                  'https://player.vimeo.com/video/827231716',
                  'https://player.vimeo.com/video/827231249',
                  'https://player.vimeo.com/video/827232757',
                  'https://player.vimeo.com/video/827228616',
                  'https://player.vimeo.com/video/827224212',
                  'https://player.vimeo.com/video/827223932',
                  'https://player.vimeo.com/video/827224100',
                  'https://player.vimeo.com/video/827224372',
                  'https://player.vimeo.com/video/827231938',
                  'https://player.vimeo.com/video/827225978',
                  'https://player.vimeo.com/video/827225646',
                  'https://player.vimeo.com/video/827229920',
                  'https://player.vimeo.com/video/827226438',
                  'https://player.vimeo.com/video/827224138',
                  'https://player.vimeo.com/video/827224297',
                  'https://player.vimeo.com/video/827230301',
                  'https://player.vimeo.com/video/827224182',
                  'https://player.vimeo.com/video/827224254',
                  'https://player.vimeo.com/video/827224776',
                  'https://player.vimeo.com/video/827230127',
                  'https://player.vimeo.com/video/827225082',
                  'https://player.vimeo.com/video/827232873',
                  'https://player.vimeo.com/video/827224435',
                  'https://player.vimeo.com/video/827229655',
                  'https://player.vimeo.com/video/827225047',
                  'https://player.vimeo.com/video/827223314',
                  'https://player.vimeo.com/video/827223983',
                  'https://player.vimeo.com/video/827230457',
                  'https://player.vimeo.com/video/827227052',
                  'https://player.vimeo.com/video/827223784',
                  'https://player.vimeo.com/video/827225527',
                  'https://player.vimeo.com/video/827233151',
                  'https://player.vimeo.com/video/827233984',
                  'https://player.vimeo.com/video/835327143',
                  'https://player.vimeo.com/video/827230566',
                  'https://player.vimeo.com/video/827226105',
                  'https://player.vimeo.com/video/827225137',
                  'https://player.vimeo.com/video/827226541',
                  'https://player.vimeo.com/video/827226202',
                  'https://player.vimeo.com/video/827226753',
                  'https://player.vimeo.com/video/835327168',
                  'https://player.vimeo.com/video/827228374',
                  'https://player.vimeo.com/video/827223883',
                  'https://player.vimeo.com/video/827229285',
                  'https://player.vimeo.com/video/827224466',
                  'https://player.vimeo.com/video/827230660',
                  'https://player.vimeo.com/video/827223711',
                  'https://player.vimeo.com/video/827224557',
                  'https://player.vimeo.com/video/827228498',
                  'https://player.vimeo.com/video/827228287',
                  'https://player.vimeo.com/video/827224337',
                  'https://player.vimeo.com/video/827225332',
                  'https://player.vimeo.com/video/827231599',
                  'https://player.vimeo.com/video/827233398',
                  'https://player.vimeo.com/video/827227951',
                  'https://player.vimeo.com/video/827228752',
                  'https://player.vimeo.com/video/827228828',
                  'https://player.vimeo.com/video/827225794',
                  'https://player.vimeo.com/video/827231048',
                  'https://player.vimeo.com/video/827229454',
                  'https://player.vimeo.com/video/827227135',
                  'https://player.vimeo.com/video/827229985',
                  'https://player.vimeo.com/video/827233791',
                  'https://player.vimeo.com/video/827226983',
                  'https://player.vimeo.com/video/827229518',
                  'https://player.vimeo.com/video/827223854',
                  'https://player.vimeo.com/video/827224026',
                  'https://player.vimeo.com/video/827231111',
                  'https://player.vimeo.com/video/827224502',
                  'https://player.vimeo.com/video/827233550',
                  'https://player.vimeo.com/video/835327071',
                  'https://player.vimeo.com/video/827228097']
    ts_url = []
    split_str = "/"
    for u in video_urls:
        master_m3u8 = get_master_m3u8(u)
        if master_m3u8:
            m3u8_list = get_master_m3u8_url(master_m3u8)
            x = m3u8_list[-1].count("..")
            m3u8_ts_url = "/".join(master_m3u8.split(split_str)[:-(x+1)] + m3u8_list[-1].split(split_str)[-2:])
            print(m3u8_ts_url)
            ts_url.append(m3u8_ts_url)
    print(ts_url)
