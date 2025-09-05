import json
import os
import uuid
import urllib3

from .session import sessions, COMMON_HEADERS

urllib3.disable_warnings()
import requests

from .query import auth, getImage, generate_pointjson, checkImage


def query(data=None) -> dict:
    if data is None:
        data = {}
    required_keys = ['pageNum', 'service_type', 'domain', 'token', 'sign', 'uuid']

    pageNum = data.get('pageNum', 1)
    service_type = data.get('service_type', '1')
    domain = data.get('domain', '')
    token = data.get('token', '')
    sign = data.get('sign', '')
    uuid_token = data.get('uuid', '')
    rci = data.get('rci', '')

    # 参数校验
    for key in required_keys:
        if key not in data:
            raise f"Missing parameter: {key}"

    headers = {
        **COMMON_HEADERS,
        "Token": token,
        "Sign": sign,
        "Uuid": uuid_token,
        "Content-Type": "application/json; charset=UTF-8"
    }
    if rci is not None and rci != "":
        headers.update({"Rci": rci})

    data = {"pageNum": pageNum, "pageSize": 40, "unitName": domain, "serviceType": service_type}

    resp = sessions.post('https://hlwicpfwc.miit.gov.cn/icpproject_query/api/icpAbbreviateInfo/queryByCondition',
                         headers=headers, verify=False,
                         data=json.dumps(data, ensure_ascii=False).encode("utf-8").replace(b" ", b""), )
    rci = ''
    if 'rci' in resp.headers.keys():
        rci = resp.headers['rci']

    resp = resp.text

    data = json.loads(resp, )
    if rci != "":
        data['rci'] = rci
    return data


def get_uid_token_sign():
    try:
        token = auth()
        params, clientUid = getImage(token)
        pointjson = generate_pointjson(params["bigImage"], params["smallImage"], params["secretKey"])
        sign = checkImage(params["uuid"], params["secretKey"], clientUid, pointjson, token)
        uuid = params["uuid"]
        return {
            "uuid": uuid,
            "sign": sign,
            "token": token
        }
    except Exception as e:
        raise Exception(f"验证码校验失败: {e}")
