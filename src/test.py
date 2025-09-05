import json

import loguru

import cache_utils
import icp.app


def main():
    keyword = "北京百度网讯科技有限公司"
    page = 1
    # 首先尝试从数据库缓存中获取查询结果
    # cached_result = cache_utils.load_query_result_from_cache(keyword, page)
    # if cached_result:
    #     print(json.dumps(cached_result))
    #     return cached_result

    # 尝试从缓存获取token
    token_dict = cache_utils.load_token_from_cache_one()

    # 如果缓存中没有有效的token，则重新获取
    if not token_dict:
        for i in range(0, 5):
            try:
                token_dict = icp.app.get_uid_token_sign()
            except Exception as e:
                loguru.logger.error(e)
                if i == 4:
                    return {
                        'error': e
                    }
                continue
            break
        # 保存新获取的token到缓存

    data = {
        "pageNum": page,
        "domain": keyword,
        'service_type': "1",
        "token": token_dict.get('token', ""),
        "uuid": token_dict.get('uuid', ''),
        "sign": token_dict.get('sign', '')
    }
    text = icp.app.query(data)
    if text.get('code', 500) != 200:
        cache_utils.delete_token_to_cache(token_dict)
        loguru.logger.error(text.get('msg', Exception(f"状态码 {text.get('code', 500)}")))
        return {
            'error': text.get('msg', Exception(f"状态码 {text.get('code', 500)}"))
        }
    params_list = text.get('params', {}).get('list', [])
    result = {
        "keyword": keyword,
        "page": page,
        "pageSize": 40,
        "total": text.get('params', {}).get('total', 0),
        "records": params_list,
    }

    # 保存查询结果到数据库
    cache_utils.save_query_result(keyword, page, result)

    cache_utils.delete_token_to_cache(token_dict)
    return result


print(main())
