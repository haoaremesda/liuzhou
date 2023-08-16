import requests
from bs4 import BeautifulSoup
import csv

# 目标网页的URL
url = "https://en.m.wikipedia.org/wiki/List_of_Christian_monasteries_in_Denmark"
headers = {
    'authority': 'en.m.wikipedia.org',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
}
# 此为代理配置，仅在大陆使用，非大陆地区可注释掉
proxies = {"http": "127.0.0.1:4780", "https": "127.0.0.1:4780"}
# 发起HTTP请求获取网页内容，使用代理
# response = requests.get(url=url, headers=headers, proxies=proxies)

# 发起HTTP请求获取网页内容，不适用代理
response = requests.get(url=url, headers=headers)

# 获取网页内容
html_content = response.text

# 使用BeautifulSoup解析网页内容
soup = BeautifulSoup(html_content, "html.parser")

# 找到所有的表格和表格标题
tables = soup.find_all("table", class_="wikitable")

# 将表格数据保存为CSV文件
with open("monasteries_data.csv", "w", newline="", encoding="utf-8") as csvfile:
    csvwriter = csv.writer(csvfile)

    # 循环遍历前三个表格
    for i, table in enumerate(tables[:3]):
        table_rows = table.find_all("tr")

        # 提取表格的标题（th标签）
        table_title_row = table_rows[0]
        table_title_cells = table_title_row.find_all("th")
        # 获取表格标题
        table_title = [cell.get_text(strip=True) for cell in table_title_cells]

        # 将标题作为CSV文件的标题行
        csvwriter.writerow(table_title)

        # 遍历表格数据行
        for row in table_rows[1:]:
            cells = row.find_all(["th", "td"])
            # 获取表格行内容
            row_data = [cell.get_text(strip=True) for cell in cells]
            csvwriter.writerow(row_data)
        csvwriter.writerow([])

print("CSV file saved successfully.")
