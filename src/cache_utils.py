import os
import json
import sqlite3
import time
import datetime
from typing import Dict, Any

CACHE_DIR = os.path.expanduser("~/.icp-mcp/cache")
DB_PATH = os.path.expanduser("~/.icp-mcp/data.db")

# 确保缓存目录存在
os.makedirs(CACHE_DIR, exist_ok=True)


def get_token_cache_path() -> str:
    """获取token缓存文件路径"""
    return os.path.join(CACHE_DIR, "token_cache.json")


def save_token_to_cache(token_dict: Dict[str, str]) -> None:
    """将token信息保存到缓存文件"""
    cache_data = {
        "token_dict": token_dict,
        "timestamp": time.time()
    }
    key = token_dict['uuid']
    cache_all_data = load_token_from_cache()
    if key not in cache_all_data:
        cache_all_data[key] = cache_data

    with open(get_token_cache_path(), 'w') as f:
        json.dump(cache_all_data, f)


def update_token_cache(token_dict: Dict[str, str]) -> None:
    key = token_dict['uuid']
    cache_all_data = load_token_from_cache()
    if key in cache_all_data:
        cache_all_data[key]['token_dict'].update(token_dict)
    with open(get_token_cache_path(), 'w') as f:
        json.dump(cache_all_data, f)


def delete_token_to_cache(token_dict: Dict[str, str]) -> None:
    cache_all_data = load_token_from_cache()
    key = token_dict['uuid']
    if key in cache_all_data:
        cache_all_data.pop(key)
    with open(get_token_cache_path(), 'w') as f:
        json.dump(cache_all_data, f)


def load_token_from_cache(expiry_seconds: int = 180) -> Dict[str, dict] | None:
    """从缓存文件加载token信息，如果过期则返回None"""
    cache_path = get_token_cache_path()
    if not os.path.exists(cache_path):
        return {}

    try:
        cache_data = {}
        with open(cache_path, 'r') as f:
            _cache_data: dict = json.load(f)
        for key, value in _cache_data.items():
            # 检查是否过期
            if time.time() - value["timestamp"] > expiry_seconds:
                continue
            cache_data[key] = value

        return cache_data
    except (json.JSONDecodeError, KeyError):
        # 缓存文件损坏，删除它
        if os.path.exists(cache_path):
            os.remove(cache_path)
        return {}


def load_token_from_cache_one(expiry_seconds: int = 180) -> Dict[str, dict] | None:
    cache_all_data = load_token_from_cache(expiry_seconds)
    if cache_all_data is None or len(cache_all_data) == 0:
        return None
    import random
    random.seed(time.time())
    key = random.choice(list(cache_all_data.keys()))
    return cache_all_data[key].get('token_dict', {})


def init_database() -> None:
    """初始化SQLite数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 创建查询结果表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS icp_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            page INTEGER NOT NULL,
            query_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            result TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()


def save_query_result(keyword: str, page: int, result: Dict[str, Any]) -> None:
    """将查询结果保存到SQLite数据库"""
    init_database()  # 确保数据库已初始化

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO icp_queries (keyword, page, result)
        VALUES (?, ?, ?)
    ''', (keyword, page, json.dumps(result, ensure_ascii=False)))

    conn.commit()
    conn.close()


def load_query_result_from_cache(keyword: str, page: int, expiry_seconds: int = 2592000) -> Dict[str, Any] | None:
    """从数据库加载查询结果，如果不存在或过期则返回None
    默认缓存时间为一个月(30天 = 2592000秒)
    """
    if not os.path.exists(DB_PATH):
        return None

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 查询匹配keyword和page的最新记录
        cursor.execute('''
            SELECT result, query_time FROM icp_queries 
            WHERE keyword = ? AND page = ?
            ORDER BY query_time DESC LIMIT 1
        ''', (keyword, page))

        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        result_str, query_time_str = row

        # 检查是否过期
        query_time = datetime.datetime.fromisoformat(query_time_str.split('.')[0])
        if datetime.datetime.now() - query_time > datetime.timedelta(seconds=expiry_seconds):
            return None

        return json.loads(result_str)
    except Exception:
        return None
