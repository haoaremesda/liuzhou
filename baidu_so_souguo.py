import re

import requests


def query_sogou(key_words: str):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive',
        'Referer': 'https://www.sogou.com/web',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    params = {
        'query': key_words,
        # '_ast': '1694697040',
        '_asf': 'www.sogou.com',
        # 'w': '01029901',
        # 'p': '40040100',
        'dp': '1',
        'cid': '',
        's_from': 'result_up',
    }
    response = requests.get('https://www.sogou.com/web', params=params, headers=headers, verify=False)
    print(response.text)


def query_360(key_words: str):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive',
        'Referer': 'https://www.so.com/',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    params = {
        'ie': 'utf-8',
        'fr': 'none',
        'src': '360sou_newhome',
        # 'ssid': 'ae107ca2585d493092ef27034d6ecbb7',
        'sp': 'a81',
        # 'cp': '0a15020013',
        'nlpv': 'placeholder_bt_21',
        'q': key_words,
    }
    response = requests.get('https://www.so.com/s', params=params, headers=headers)
    print(response.text)


def query_baidu(key_words: str):
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive',
        'Referer': 'https://www.baidu.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'is_referer': 'https://www.baidu.com/',
        'is_xhr': '1',
        'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    params = [
        ('ie', 'utf-8'),
        ('mod', '1'),
        ('isbd', '1'),
        # 参数随机
        ('isid', 'bc0f56e606922674'),
        ('ie', 'utf-8'),
        ('f', '8'),
        ('rsv_bp', '1'),
        ('rsv_idx', '1'),
        ('tn', 'baidu'),
        ('wd', key_words),
        ('fenlei', '256'),
        ('rqlang', 'cn'),
        ('rsv_enter', '0'),
        ('rsv_dl', 'tb'),
        ('rsv_btype', 't'),
        ('bs', '平安银行杨军新一代信息技术产业'),
        ('_ss', '1'),
        ('clist', ''),
        ('hsug', ''),
    ]
    response = requests.get('https://www.baidu.com/s', params=params, headers=headers)
    print(response.text)
    data = re.findall(r'"title":"([^"]*)".*"contentText":"([^"]*)"', response.text)
    print(data)


query_baidu("平安银行杨军新一代信息技术产业")
