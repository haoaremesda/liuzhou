import re
import time

from selenium import webdriver
from lxml import etree
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import concurrent.futures
import pandas as pd


def start_browser():
    # 返回selenium实例
    driver = webdriver.Edge(executable_path='msedgedriver.exe')
    return driver


def browser_task(option_value: str) -> list:
    datas = []
    # 获取浏览器实例
    browser = start_browser()
    browser.get('https://data.eastmoney.com/yjfp/')
    try:
        time.sleep(2)
        # 显式等待元素出现，并且可点击
        option = WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, f"//option[@value='{option_value}']")))
        option.click()
        time.sleep(3)
        # 显式等待元素出现，并且可见
        dataview = WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, 'dataview-body')))
        response = browser.page_source
        html = etree.HTML(response)
        page_number = html.xpath('//div[@class="pagerbox"]/a/@data-page')[-2]
        for i in range(int(page_number)):
            # 第一页不用点击下一页
            if i > 0:
                link_text = '下一页'
                next_page_link = browser.find_element_by_xpath(f'//a[text()="{link_text}"]')
                if not next_page_link.text:
                    break
                next_page_link.click()
                # 显式等待元素出现，并且可见
                dataview = WebDriverWait(browser, 10).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, 'dataview-body')))
                time.sleep(3)
            # 获取表格的所有行
            rows = dataview.find_elements_by_tag_name('tr')
            # rows = html.xpath('//*[@id="dataview"]/div[2]/div[2]/table/tbody/tr')
            for row in rows[2:]:
                data = []
                row_texts = row.text.split(" ")
                data.append(row_texts[0]),
                data.append(row_texts[1]),
                data.append(option_value),
                data.append(row_texts[19]),
                x = row_texts[5]
                y = row_texts[6]
                z = row_texts[7]
                if x != '-':
                    song = round(float(re.findall('10送(\d+(?:\.\d+)?)', x)[0]) / 10, 2)
                else:
                    song = x
                if y != '-':
                    zhuan = round(float(re.findall('10转(\d+(?:\.\d+)?)', y)[0]) / 10, 2)
                else:
                    zhuan = y
                if z != '-':
                    pai = round(float(re.findall('10派(\d+(?:\.\d+)?)', z)[0]) / 10, 2)
                else:
                    pai = '-'
                data.append(f'{song},{zhuan}'),
                data.append(song),
                data.append(zhuan),
                data.append(pai),
                data.append(row_texts[8]),
                data.append(row_texts[9]),
                data.append(row_texts[10]),
                data.append(row_texts[11]),
                data.append(row_texts[12]),
                data.append(row_texts[13])
                datas.append(data)
    except Exception as e:
        print("异常情况：", e)
        # 发生异常关闭浏览器实例
        browser.quit()
    return datas


def main():
    MAX_WORKERS = 5
    option_values = ['2023-06-30', '2023-03-31', '2022-12-31', '2022-09-30', '2022-06-30', '2022-03-31', '2021-12-31',
                     '2021-09-30',
                     '2021-06-30', '2021-03-31', '2020-12-31', '2020-09-30', '2020-06-30', '2020-03-31', '2019-12-31',
                     '2019-09-30',
                     '2019-06-30', '2019-03-31', '2018-12-31', '2018-09-30', '2018-06-30', '2018-03-31', '2017-12-31',
                     '2017-09-30',
                     '2017-06-30', '2017-03-31', '2016-12-31', '2016-09-30', '2016-06-30', '2016-03-31', '2015-12-31',
                     '2015-09-30',
                     '2015-06-30', '2014-12-31', '2014-09-30', '2014-06-30', '2013-12-31', '2013-09-30', '2013-06-30',
                     '2013-03-31',
                     '2012-12-31', '2012-09-30', '2012-06-30', '2011-12-31', '2011-06-30', '2010-12-31', '2010-06-30',
                     '2009-12-31',
                     '2009-06-30', '2008-12-31', '2008-09-30', '2008-06-30', '2007-12-31', '2007-06-30', '2006-12-31',
                     '2006-06-30',
                     '2005-12-31', '2005-06-30', '2004-12-31', '2004-06-30', '2003-12-31', '2003-06-30', '2002-12-31',
                     '2002-06-30',
                     '2001-12-31', '2001-06-30', '2000-12-31', '2000-06-30', '1999-12-31', '1999-06-30', '1998-12-31',
                     '1998-06-30',
                     '1997-12-31', '1997-06-30', '1996-12-31', '1996-06-30', '1995-12-31', '1995-06-30', '1994-12-31',
                     '1994-06-30',
                     '1993-12-31', '1993-06-30', '1992-12-31', '1992-06-30', '1991-12-31', '1990-12-31']

    # option_values = ['2023-03-31']
    datas = [['股票代码', '公司名称', '分红年份', '公告日期', '送转股总比例', '送股比例', '转股比例', '现金分红比例', '股息率', '每股收益', '每股净资产', '每股公积金', '每股未分配利润', '净利润同比增长率']]
    # 创建线程池
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:  # 最大线程数为5
        # 提交任务给线程池
        futures = {executor.submit(browser_task, value): value for value in option_values}
        # 获取线程返回的数据
        for future in concurrent.futures.as_completed(futures):
            option_value = futures[future]
            try:
                data = future.result()
                datas.extend(data)
                print(f"{option_value} 线程返回数据: {len(data)}")
            except Exception as e:
                print(f"线程发生异常: {e}")
    print(len(datas))
    stockdata = pd.DataFrame(datas[1:], columns=datas[0])
    # 将特定列的数据类型设置为字符串
    # stockdata['股票代码'] = stockdata['股票代码'].astype(str)
    stockdata.to_csv('股票数据second单.csv', encoding='utf-8', index=True)


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print(end_time - start_time)
