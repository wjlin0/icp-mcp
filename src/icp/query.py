import base64
import hashlib
import json
import os
import time
import uuid
from urllib import parse
import loguru
import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from .crack import Crack
from .session import sessions, COMMON_HEADERS


def auth():
    t = str(round(time.time()))
    data = {
        "authKey": hashlib.md5(('testtest' + t).encode()).hexdigest(),
        "timeStamp": t
    }
    headers = {**COMMON_HEADERS, "Content-Type": "application/x-www-form-urlencoded"}

    for i in range(3):
        try:
            resp = sessions.post('https://hlwicpfwc.miit.gov.cn/icpproject_query/api/auth', headers=headers,
                                 data=parse.urlencode(data), verify=False, )

            resp = resp.json()
            return resp["params"]["bussiness"]
        except Exception as e:
            loguru.logger.error(f"认证请求失败: {e}")
            # time.sleep(CAPTCHA_CONFIG['retry_delay'])
            continue


def getImage(token):
    headers = {**COMMON_HEADERS, "Token": token}
    payload = {"clientUid": "point-" + str(uuid.uuid4())}
    for i in range(3):
        try:
            resp = sessions.post('https://hlwicpfwc.miit.gov.cn/icpproject_query/api/image/getCheckImagePoint',
                                 headers=headers, json=payload, verify=False, )
            # print(resp)
            resp = resp.json()
            return resp["params"], payload["clientUid"]
        except Exception as e:
            loguru.logger.error(f"获取验证码图片失败: {e}")
            continue


def aes_ecb_encrypt(plaintext: bytes, key: bytes, block_size=16):
    backend = default_backend()
    cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=backend)

    padding_length = block_size - (len(plaintext) % block_size)
    plaintext_padded = plaintext + bytes([padding_length]) * padding_length

    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext_padded) + encryptor.finalize()

    return base64.b64encode(ciphertext).decode('utf-8')


crack = Crack()


def generate_pointjson(big_img, small_img, secretKey):
    boxes = crack.detect(big_img)
    if boxes:
        pass
    else:
        pass
        raise Exception("文字检测失败,请重试")
    points = crack.siamese(image_list=crack.get_origin_image(small_img), boxes=boxes)
    # log_info("文字匹配成功")
    new_points = [[p[0] + 20, p[1] + 20] for p in points]
    pointJson = [{"x": p[0], "y": p[1]} for p in new_points]
    enc_pointJson = aes_ecb_encrypt(json.dumps(pointJson).replace(" ", "").encode(), secretKey.encode())
    return enc_pointJson


def checkImage(uuid_token, secretKey, clientUid, pointJson, token):
    headers = {**COMMON_HEADERS, "Token": token}
    data = {
        "token": uuid_token,
        "secretKey": secretKey,
        "clientUid": clientUid,
        "pointJson": pointJson
    }
    resp = sessions.post('https://hlwicpfwc.miit.gov.cn/icpproject_query/api/image/checkImage', headers=headers,
                         json=data, verify=False).json()
    if resp["code"] == 200:
        if 'sign' in resp["params"]:
            return resp["params"]["sign"]
        else:
            raise Exception(f"Sign 签名获取失败: {resp['msg']}")


def gaCheck(pointJson, token):
    headers = {**COMMON_HEADERS}
    data = {
        "pointJson": pointJson,
        "token": token,
        "captchaType": "clickWord"
    }
    resp = sessions.post('https://beian.mps.gov.cn/cyber_portal/captcha/check', headers=headers, json=data)
    if resp.status_code == 200 and resp.json()["repCode"] == "0000" and "result" in resp.json()["repData"] and \
            resp.json()["repData"]["result"]:
        return True
    else:
        print(resp.text)
        return False

# print(get_ga_pointJson())
