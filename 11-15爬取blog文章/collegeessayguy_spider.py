import requests
from lxml import etree

heads = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}

proxies = {"http": "http://127.0.0.1:4780", "https": "http://127.0.0.1:4780"}

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
        xpath_str = '//div[@class="sqs-block-content"]/li//a/@href'
    else:
        xpath_str = '//div[@class="sqs-block-content"]/li//a/@href'
    blog_links_2 = []
    blog_links = tree.xpath(xpath_str)
    for i in blog_links:
        if str(i).startswith("/"):
            i = f"https://www.collegeessayguy.com{i}"
        if "/blog/" in i:
            blog_links_2.append(i)
    return blog_links_2


def get_blog_text(blog_url: str):
    resp = requests.get(url=blog_url, headers=heads, proxies=proxies)
    # 使用lxml.etree解析HTML
    tree = etree.HTML(resp.content)


if __name__ == '__main__':
    url = "https://www.collegeessayguy.com"
    free_resources_links = get_free_resources(url)[:4]
    for i in free_resources_links:
        blog_links = get_blog_links(i)
        for b in blog_links:
            get_blog_text(b)
    print(free_resources_links)
