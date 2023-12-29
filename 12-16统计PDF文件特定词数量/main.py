import os

import fitz  # PyMuPDF
import re
from concurrent.futures import ThreadPoolExecutor
import pandas as pd


def parse_keywords(keywords: str) -> list:
    # 使用正则表达式进行拆分，这里的分隔符是逗号、分号、竖线
    split_pattern = r'[、．，。]'
    result = re.split(split_pattern, keywords)
    return result


def parse_infos(infos_str: str):
    infos_list = []
    # 定义正则表达式模式
    regular = [r"代码：(\d+).*", r"股票代码\s+(\d+).*", r"股票代码：(\d+).*",
               r"A 股股票代码：(\d+).*", r"股票代码：\n(\d+).*", r"证券代码\s+(\d+).*"]
    for i in regular:
        match = re.search(i, infos_str)
        if match:
            # 提取匹配到的信息
            company_code = match.group(1)
            if len(company_code) < 6:
                print(company_code)
            infos_list.append(company_code)
            print("公司代码:", company_code)
            break
    if not infos_list:
        print("xxxxxxx")
    return infos_list



def count_specific_words(pdf_path, specific_words):
    # 打开PDF文件
    pdf_document = fitz.open(pdf_path)

    # 初始化计数器
    word_count = {word: 0 for word in specific_words}

    infos_list = []

    match = re.search(r"\\([^\\]+?)(\d{4}).*", pdf_path)
    if not match:
        print("sssssssss")

    # 遍历每一页
    for page_number in range(pdf_document.page_count):
        page = pdf_document[page_number]

        # 提取文本
        page_text = page.get_text()
        if "股票代码" in page_text or "公司代码" in page_text or "证券代码" in page_text:
            if not infos_list:
                infos_list = parse_infos(page_text)
                if match:
                    infos_list.append(match.group(1).split("：")[0])
                    infos_list.append(match.group(2))


        # 遍历特定词
        for word in specific_words:
            # 使用正则表达式进行不区分大小写的匹配
            matches = re.findall(fr'\b{re.escape(word.strip())}\b', page_text, re.IGNORECASE)

            # 更新计数器
            word_count[word] += len(matches)

    # 关闭PDF文件
    pdf_document.close()

    return infos_list, word_count


def process_pdf(pdf_path, specific_words):
    # 调用之前定义的函数统计特定词的出现次数
    infos_list, word_count = count_specific_words(pdf_path, specific_words)
    return pdf_path, infos_list, word_count


# 目录路径
pdf_directory_path = r'F:\压缩文件\年报'

# 要统计的特定词列表
specific_words_str = """红色文创、红船精神、浙江精神、红色影视、中国故事、不忘初心、牢记使命、红色文化、民族精神、文化强国、民旅振兴、马克思主文、习近平新时代中国特色社会主文恩想、中国梦、三个代表面要思想、可持续发展、高质量发展．毛译东思想、邓小平理论、马克恩列宁主义、中华民族伟大复兴、政治意识、大局意识、核心意识，看齐意识。生态保护、节能减排、可持续发展、绿色发展观、环境友好、低碳。实事求是、公平公正、开放自由、格守承诺、解放思想、开拓进取。正版化、合法化、尊重创作、版权保护、打击盗版、合规经营、反舞弊、法治。团结协作、共享、交流、互助、爱心、友善、平台连接、文化艺术交流、互利共赢、战略合作、协同发展、公益活动、捐赠、助学、乡村振兴、扶贫助农、人才培养、开展培训、以人为本、以客户为中心、员工关怀、勤学、修德、明辨、笃实"""

specific_words = parse_keywords(specific_words_str)

# 获取目录中的所有PDF文件路径
pdf_files_list = [os.path.join(pdf_directory_path, filename) for filename in os.listdir(pdf_directory_path) if filename.endswith(".pdf") or filename.endswith(".PDF")]

# 设置线程池大小，根据实际情况调整
pool_size = min(8, len(pdf_files_list))

# 使用线程池处理每个PDF文件
with ThreadPoolExecutor(max_workers=pool_size) as executor:
    # 提交每个PDF文件的任务给线程池
    futures = [executor.submit(process_pdf, pdf_file, specific_words) for pdf_file in pdf_files_list]

    # 等待所有任务完成
    results = [future.result() for future in futures]

datas = [["证券代码", "公司简称", "年度", "数量"]]

# 打印每个PDF文件的统计结果
for pdf_file, infos_list, word_count in results:
    print(f"File: {pdf_file}")
    print(f"infos_list: {infos_list}")
    print("Word Count:", word_count)
    print("-" * 30)
    if len(infos_list) < 3:
        print("dsadsadsadsadsa")
    infos_list.append(sum(word_count.values()))
    datas.append(infos_list)


# 将数据转换为DataFrame
df = pd.DataFrame(datas)
# 将数据写入Excel文件
excel_file_path = '特定词统计.xlsx'
df.to_excel(excel_file_path, index=False, header=False)

print(f"数据已成功写入到 {excel_file_path}")
