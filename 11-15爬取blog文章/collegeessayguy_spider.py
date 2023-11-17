import json
import os

import requests
from lxml import etree
from bs4 import BeautifulSoup
import concurrent.futures

heads = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}

proxies = {"http": "http://127.0.0.1:4780", "https": "http://127.0.0.1:4780"}


def remove_special_characters(strings):
    special_characters = "!$%^&*{}[]|\:;'<>?./\""
    return "".join([string for string in strings if not any(char in special_characters for char in string)])


def get_free_resources(url):
    resp = requests.get(url=url, headers=heads, proxies=proxies)
    if resp.status_code == 200:
        # 使用lxml.etree解析HTML
        tree = etree.HTML(resp.content)
        # 通过XPath选择元素
        free_resources = tree.xpath('//nav[@id="mobileNavigation"]/div[5]//div[@class="external"]/a/@href')
        return [f"https://www.collegeessayguy.com{i}" for i in free_resources]
    return []


def get_blog_links(free_resource_url: str):
    resp = requests.get(url=free_resource_url, headers=heads, proxies=proxies)
    # 使用lxml.etree解析HTML
    tree = etree.HTML(resp.content)
    # 通过XPath选择元素
    if "college-application-hub" in free_resource_url:
        xpath_str = '//div[@class="image-subtitle sqs-dynamic-text"]//a/@href'
    elif "personal-statement" in free_resource_url:
        xpath_str = '//div[@class="sqs-html-content"]/h3//a/@href'
    elif "supplemental-essays" in free_resource_url:
        xpath_str = '//div[@class="sqs-block-content"]/li//a/@href | //div[@class="sqs-html-content"]/h2//a/@href'
    else:
        xpath_str = '//ul[@data-rte-list="default"]/li//a/@href'
    blog_links_2 = []
    blog_links = tree.xpath(xpath_str)
    for i in blog_links:
        if str(i).startswith("/"):
            i = f"https://www.collegeessayguy.com{i}"
        # if "/blog/" in i:
        #     blog_links_2.append(i)
        blog_links_2.append(i)
    return blog_links_2


def get_blog_text(blog_url: str):
    global folder
    blog_data = {"url": blog_url, "links": [], "paragraphs": []}
    resp = requests.get(url=blog_url, headers=heads, proxies=proxies)
    soup = BeautifulSoup(resp.content, 'html.parser')
    # 提取标题
    title = soup.title.text
    print("标题:", title)
    blog_data["title"] = title

    soup = soup.select("div[data-content-field='main-content']")[0]

    # 提取段落
    paragraphs = soup.find_all('p')
    for paragraph in paragraphs:
        blog_data["paragraphs"].append(paragraph.text)
        print("段落:", paragraph.text)
        paragraph_a = paragraph.find_all('a', href=True)
        for a in paragraph_a:
            blog_data["links"].append({a.text: a['href']})
    file_name = remove_special_characters(title)
    output_file = f"{folder}/{file_name}.json"
    with open(output_file, 'w', encoding='utf-8') as json_file:
        json.dump(blog_data, json_file, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    folder = "./blogs"
    url = "https://www.collegeessayguy.com"
    all_links = []
    if not os.path.exists(folder):
        os.makedirs(folder)
    free_resources_links = get_free_resources(url)[:4]
    for i in free_resources_links:
        blog_links = get_blog_links(i)
        all_links.extend(blog_links)
        # for b in blog_links:
        #     get_blog_text(b)
    max_threads = 3
    with concurrent.futures.ThreadPoolExecutor(max_threads) as executor:
        futures = [executor.submit(get_blog_text, value) for value in all_links]
        concurrent.futures.wait(futures)
    print(free_resources_links)
