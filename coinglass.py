import base64
import re
from Crypto.Cipher import AES
import json
import zlib


# 解密后，去掉补足的空格用strip() 去掉
def decrypt(text, key):
    key = key.encode('utf-8')
    mode = AES.MODE_ECB
    cryptos = AES.new(key, mode)
    plain_text = cryptos.decrypt(base64.b64decode(text))
    plain_text = plain_text[:- ord(plain_text[len(plain_text) - 1:])]
    return plain_text.hex()


def c(text):
    # 初始化一个空列表，用于存储每两位的字符串
    result = []
    # 使用循环遍历字符串
    matches = re.findall(r'[\da-fA-F]{2}', text)
    for i in matches:
        result.append(int(i, 16))
    # 压缩的数据
    compressed_data = bytearray(result)
    # 初始化 Zlib 解压缩对象
    decompressor = zlib.decompressobj(zlib.MAX_WBITS | 16)
    # 解压缩数据
    decompressed_data = decompressor.decompress(compressed_data)
    # 结束解压缩
    decompressed_data += decompressor.flush()
    return decompressed_data.decode()


if __name__ == '__main__':
    url_end = '/api/kline'
    montage_str = f"coinglass{url_end}coinglass"
    b64_str = base64.b64encode(montage_str.encode()).decode()
    # 注意resp_user就是返回的请求头中的User参数
    resp_user = "Ka6cND4Pa9hOhggT877PFodr8GVIQdRZFYIL40F7Sot/UDUoiTOfkPwwxCNuSzik"
    d = decrypt(resp_user, b64_str[:16])  # 解密
    key = c(d)
    sign = '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'
    d = decrypt(sign, key)  # 解密
    i = c(d)
    decript_json = json.loads(i)
    print("解密:", decript_json)