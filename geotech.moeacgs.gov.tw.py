import requests

headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Referer': 'https://geotech.moeacgs.gov.tw/imoeagis/js/WebWorker/GetProjectList.js?v=0331',
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    'Content-Type': 'application/json; charset=UTF-8',
}

json_data = {
    'sType': 'wkt',
    'sWKT': 'POLYGON((13385311.650344318 2582741.9284753087,13385311.650344318 2590681.824788431,13395219.800135782 2590681.824788431,13395219.800135782 2582741.9284753087,13385311.650344318 2582741.9284753087))',
    'sKeyWord': None,
    'sPlan': '',
    'exename': '',
    'orgname': '',
    'userauth': '',
    'status': None,
    'pagecnt': '1',
}

proxies = {"http": "http://127.0.0.1:4780", "https": "http://127.0.0.1:4780"}

response = requests.post('https://geotech.moeacgs.gov.tw/imoeagis/api/DrillProjectsJson/GetDrillProjects', headers=headers, json=json_data, proxies=proxies)
print(response.text)