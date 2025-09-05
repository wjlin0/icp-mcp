import os

import requests

sessions = requests.Session()

COMMON_HEADERS = {
    "Cookie": "__jsluid_s=e8f856091e3de0cc6e452f8e1a188c94",
    "Sec-Ch-Ua-Platform": "\"macOS\"",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Referer": 'https://beian.miit.gov.cn/',
    "Sec-Ch-Ua": 'Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139',
    'Sec-Ch-Ua-Mobile': '?0',
    "Connection": "close",
    "Accept": "application/json, text/plain, */*",
    "Origin": 'https://beian.miit.gov.cn',
    "Accept-Encoding":'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Priority':'u=1, i',
    'Sec-Fetch-Dest':'empty',
    'Sec-Fetch-Mode':'cors',
    'Sec-Fetch-Site':'same-site',
}
sessions.headers.update(COMMON_HEADERS)
