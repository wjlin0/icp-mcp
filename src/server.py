"""
一个简化的 Python3 MCP 服务器，仅提供 ICP 备案查询工具和提示词。

功能:
  - icp_query(keyword, page, page_size): 模拟查询ICP备案信息
  - analyze_icp(keyword): 中文提示词函数，指导模型分析ICP备案结果

运行方式:
  - STDIO (Claude Desktop, MCP Inspector): uv run mcp dev mcp_server.py
  - HTTP: uv run python mcp_server.py --transport streamable-http --host 127.0.0.1 --port 8000
"""
from __future__ import annotations

import argparse
import json
import os
import threading
import time

import loguru
from mcp.server.fastmcp import FastMCP
import icp.app
import cache_utils

# --- 后台任务配置 ------------------------------------------------------
TOKEN_REFRESH_INTERVAL = 5  # token刷新间隔(秒)
TOKEN_EXPIRY_SECONDS = 60  # token过期时间(秒)
MIN_TOKENS_THRESHOLD = 1  # 最小token数量阈值


# --- 后台任务 ----------------------------------------------------------------
class TokenRefresher:
    """Token刷新器类，线程安全"""

    def __init__(self):
        self.lock = threading.Lock()
        self.running = False
        self.thread = None

    def start(self):
        """启动token刷新器"""
        with self.lock:
            if self.running:
                loguru.logger.info("Token刷新器已在运行中")
                return

            self.running = True
            self.thread = threading.Thread(target=self._refresh_loop, daemon=True)
            self.thread.start()
            loguru.logger.info("Token刷新器已启动")

    def stop(self):
        """停止token刷新器"""
        with self.lock:
            if not self.running:
                return

            self.running = False
            if self.thread:
                self.thread.join(timeout=5)
            loguru.logger.info("Token刷新器已停止")

    def _refresh_loop(self):
        """刷新循环"""
        while self.running:
            try:
                self._check_and_refresh_tokens()
                time.sleep(TOKEN_REFRESH_INTERVAL)
            except Exception as e:
                loguru.logger.error(f"刷新循环出错: {e}")
                time.sleep(TOKEN_REFRESH_INTERVAL)

    def _check_and_refresh_tokens(self):
        """检查并刷新token"""
        # 检查现有token是否足够且未过期
        valid_tokens = self._count_valid_tokens()
        loguru.logger.info(f"当前有效token数量: {valid_tokens}")

        if valid_tokens < MIN_TOKENS_THRESHOLD:
            loguru.logger.info(f"有效token数量({valid_tokens})低于阈值({MIN_TOKENS_THRESHOLD})，开始获取新token")
            self._fetch_and_save_token()

    def _count_valid_tokens(self) -> int:
        """统计有效token数量"""
        tokens = cache_utils.load_token_from_cache(TOKEN_EXPIRY_SECONDS)
        return len(tokens)

    def _fetch_and_save_token(self):
        """获取并保存新token"""
        for i in range(0, 5):
            loguru.logger.info("开始获取新token...")
            try:
                token_dict = icp.app.get_uid_token_sign()

                # 保存到缓存
                cache_utils.save_token_to_cache(token_dict)
                loguru.logger.info("新token已保存到缓存")
            except Exception as e:
                loguru.logger.error(f"获取token失败: {e}")
                if i < 4:
                    continue
            break


# --- Server 实例 ------------------------------------------------------------
parser = argparse.ArgumentParser(description="运行 ICP 查询 MCP 服务")
# 全局token刷新器实例
token_refresher = TokenRefresher()
# parser.add_argument(
#
# )
parser.add_argument("--host", default="0.0.0.0")
parser.add_argument("--port", type=int, default=8000)
args = parser.parse_args()

# 启动后台token刷新任务
# token_refresher.start()

mcp = FastMCP(
    name="ICP 查询服务",
    host=args.host,
    port=args.port,
)


# --- 工具函数 ----------------------------------------------------------------
@mcp.tool()
async def icp_query(keyword: str, page: int = 1) -> dict:
    """查询 ICP 备案信息

    参数:
        keyword: 查询关键词，可以是公司名、备案号或域名
        page: 查询页数
    返回:
        包含分页信息和备案记录数组
    """
    # 首先尝试从数据库缓存中获取查询结果
    cached_result = cache_utils.load_query_result_from_cache(keyword, page)
    if cached_result:
        return cached_result

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
        cache_utils.save_token_to_cache(token_dict)

    data = {
        "pageNum": page,
        "domain": keyword,
        'service_type': "1",
        "token": token_dict.get('token', ""),
        "uuid": token_dict.get('uuid', ''),
        "sign": token_dict.get('sign', ''),
        'rci': token_dict.get('rci', ""),
    }
    text = icp.app.query(data)
    if text.get('code', 500) != 200:
        cache_utils.delete_token_to_cache(token_dict)
        loguru.logger.error(text.get('msg', Exception(f"状态码 {text.get('code', 500)}")))
        return {
            'error': text.get('msg', Exception(f"状态码 {text.get('code', 500)}"))
        }
    params_list = text.get('params', {}).get('list', [])
    if 'rci' in text:
        rci = text.get('rci')
        token_dict['rci'] = rci
        cache_utils.update_token_cache(token_dict)

    result = {
        "keyword": keyword,
        "page": page,
        "pageSize": 40,
        "total": text.get('params', {}).get('total', 0),
        "records": params_list,
    }

    # 保存查询结果到数据库
    cache_utils.save_query_result(keyword, page, result)

    # cache_utils.delete_token_to_cache(token_dict)
    return result


@mcp.tool()
async def icp_output_file(keyword: str, page: int = 1) -> str:
    """查询 ICP 备案信息并将结果 写入文件

        参数:
            keyword: 查询关键词，可以是公司名、备案号或域名
            page: 查询页数
        返回:
            文件夹路径或异常错误
    """
    import csv
    
    result = await icp_query(keyword, page)
    if result.get('error', None):
        return result.get('error')
    # 读取当前用户
    home = CACHE_DIR = os.path.expanduser("~")
    desktop_dir = os.path.join(home, "Desktop")
    if not os.path.exists(desktop_dir):
        os.makedirs(desktop_dir)
    params_list = result.get('records', [])
    
    # 写入 CSV 文件
    file_path = os.path.join(desktop_dir, f"{keyword}.csv")
    
    if params_list:
        # 获取字段名（使用第一个记录的键）
        fieldnames = list(params_list[0].keys())
        
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(params_list)
    
    return f"查询结果已写入文件: {file_path}"


@mcp.prompt()
async def analyze_icp(keyword: str, page: int = 1, export_file: bool = False) -> str:
    """中文提示词函数，指导模型分析ICP备案结果

    参数:
        keyword: 查询关键词，可以是公司名、备案号或域名
        page: 查询页数
        export_file: 是否导出查询结果到CSV文件
    返回:
        分析指导提示词
    """
    # 提示用户可以使用导出功能
    export_tip = ""
    if export_file:
        export_tip = f"\n注意：您可以使用 icp_output_file('{keyword}', {page}) 工具查询并导出到桌面的CSV文件中。函数会返回文件路径，如果出错会返回错误信息"
    
    prompt = f"""
你是一个专业的网络安全分析师，请根据以下ICP备案信息进行分析：

查询关键词: {keyword}
页数: {page}{export_tip}

备案信息分析指导：
1. 单位背景调查：分析单位的性质、规模和业务范围
2. 网站合规性：检查网站内容与备案信息是否一致
3. 备案有效性：确认备案状态是否正常
4. 关联关系：分析同一单位下不同网站之间的关联
5. 风险提示：指出可能存在的风险点或异常情况

请根据以上指导方向，结合您对ICP备案信息的理解，给出专业的分析报告和建议。
"""
    
    return prompt


# --- 入口点 -----------------------------------------------------------------
def main() -> None:
    try:
        mcp.run(transport="streamable-http")
    finally:
        pass
        # 停止后台任务
        token_refresher.stop()


if __name__ == "__main__":
    main()
