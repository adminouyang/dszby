import os
import re
import requests
import time
import json
import concurrent.futures
import random
import threading
from datetime import datetime, timedelta
from urllib.parse import quote, unquote
import base64
from queue import Queue
import eventlet

# ===============================
# 配置区
# ===============================

# FOFA Cookie
FOFA_COOKIE = "isRedirectLang=1; is_mobile=pc; __fcd=DQVA3CHUNOEWDZUY01EE1FAF708C52E9; Hm_lvt_4275507ba9b9ea6b942c7a3f7" \
              "c66da90=1769490368; HMACCOUNT=79E7429D30B36B70; _ga=GA1.1.561856398.1769490368; befor_router=%2Fresult%3F" \
              "qbase64%3DImlwdHYvbGl2ZS96aF9jbi5qcyIgJiYgY291bnRyeT0iQ04iICYmIHByb3ZpbmNlOiAiYW5odWki%26page%3D5%26page" \
              "_size%3D20; fofa_token=eyJhbGciOiJIUzUxMiIsImtpZCI6Ik5XWTVZakF4TVRkalltSTJNRFZsWXpRM05EWXdaakF3TURVMlkyW" \
              "TNZemd3TUdRd1pUTmpZUT09IiwidHlwIjoiSldUIn0.eyJpZCI6MTE4MTAxMSwibWlkIjoxMDA3NDEyMzIsInVzZXJuYW1lIjoiT1Vfe" \
              "WFuZyIsInBhcmVudF9pZCI6MCwiZXhwIjoxNzcwMDk1MTk2fQ.Dgvo38VAYRzhoBjLlNdk9oAAwXczhGHjDALiJoleKcnMQDex9Mz6jDC" \
              "Ompl-Ay5abNuGjlLxF8A1fTYMgmXPsA; user=%7B%22id%22%3A1181011%2C%22mid%22%3A100741232%2C%22is_admin%22%3" \
              "Afalse%2C%22username%22%3A%22OU_yang%22%2C%22nickname%22%3A%22OU_yang%22%2C%22email%22%3A%222856364053%" \
              "40qq.com%22%2C%22avatar_medium%22%3A%22https%3A%2F%2Fnosec.org%2Fmissing.jpg%22%2C%22avatar_thumb%22%3A%" \
              "22https%3A%2F%2Fnosec.org%2Fmissing.jpg%22%2C%22key%22%3A%229495b90e65813ae0e9188e6a5928d1f1%22%2C%22cat" \
              "egory%22%3A%22user%22%2C%22rank_avatar%22%3A%22%22%2C%22rank_level%22%3A0%2C%22rank_name%22%3A%22%E6%B3%" \
              "A8%E5%86%8C%E7%94%A8%E6%88%B7%22%2C%22company_name%22%3A%22OU_yang%22%2C%22coins%22%3A0%2C%22can_pay_" \
              "coins%22%3A0%2C%22fofa_point%22%3A0%2C%22credits%22%3A1%2C%22expiration%22%3A%22-%22%2C%22login_at%22%" \
              "3A0%2C%22data_limit%22%3A%7B%22web_query%22%3A300%2C%22web_data%22%3A3000%2C%22api_query%22%3A0%2C%22" \
              "api_data%22%3A0%2C%22data%22%3A-1%2C%22query%22%3A-1%7D%2C%22expiration_notice%22%3Afalse%2C%22remain_" \
              "giveaway%22%3A1000%2C%22fpoint_upgrade%22%3Afalse%2C%22account_status%22%3A%22%22%2C%22parents_" \
              "id%22%3A0%2C%22parents_email%22%3A%22%22%2C%22parents_fpoint%22%3A0%2C%22created_at%22%3A%222026-01" \
              "-25%2000%3A00%3A00%22%7D; is_flag_login=1; baseShowChange=false; viewOneHundredData=false; _ga_9GWBD260" \
              "K9=GS2.1.s1769520942$o5$g1$t1769521320$j33$l0$h0; Hm_lpvt_4275507ba9b9ea6b942c7a3f7c66da90=1769521320"

# 搜索关键词（按省份搜索）
SEARCH_QUERIES = [
    '"iptv/live/zh_cn.js" && country="CN"',
    # '"iptv/live/zh_cn.js" && country="CN" && region="Anhui"',  # 安徽
    # '"iptv/live/zh_cn.js" && country="CN" && region="Beijing"',  # 北京
    # '"iptv/live/zh_cn.js" && country="CN" && region="Shanghai"',  # 上海
    # '"iptv/live/zh_cn.js" && country="CN" && region="Jiangsu"',  # 江苏
    # '"iptv/live/zh_cn.js" && country="CN" && region="Zhejiang"',  # 浙江
    # '"iptv/live/zh_cn.js" && country="CN" && region="Fujian"',  # 福建
    # '"iptv/live/zh_cn.js" && country="CN" && region="Guangdong"',  # 广东
    # '"iptv/live/zh_cn.js" && country="CN" && region="Hunan"',  # 湖南
    # '"iptv/live/zh_cn.js" && country="CN" && region="Hubei"',  # 湖北
    # '"iptv/live/zh_cn.js" && country="CN" && region="Henan"',  # 河南
    # '"iptv/live/zh_cn.js" && country="CN" && region="Hebei"',  # 河北
    # '"iptv/live/zh_cn.js" && country="CN" && region="Shandong"',  # 山东
    # '"iptv/live/zh_cn.js" && country="CN" && region="Shanxi"',  # 山西
    # '"iptv/live/zh_cn.js" && country="CN" && region="Shaanxi"',  # 陕西
    # '"iptv/live/zh_cn.js" && country="CN" && region="Sichuan"',  # 四川
    # '"iptv/live/zh_cn.js" && country="CN" && region="Chongqing"',  # 重庆
    # '"iptv/live/zh_cn.js" && country="CN" && region="Liaoning"',  # 辽宁
    # '"iptv/live/zh_cn.js" && country="CN" && region="Jilin"',  # 吉林
    # '"iptv/live/zh_cn.js" && country="CN" && region="Heilongjiang"',  # 黑龙江
    # '"iptv/live/zh_cn.js" && country="CN" && region="Jiangxi"',  # 江西
    # '"iptv/live/zh_cn.js" && country="CN" && region="Guangxi"',  # 广西
    # '"iptv/live/zh_cn.js" && country="CN" && region="Yunnan"',  # 云南
    # '"iptv/live/zh_cn.js" && country="CN" && region="Guizhou"',  # 贵州
    # '"iptv/live/zh_cn.js" && country="CN" && region="Gansu"',  # 甘肃
    # '"iptv/live/zh_cn.js" && country="CN" && region="Ningxia"',  # 宁夏
    # '"iptv/live/zh_cn.js" && country="CN" && region="Qinghai"',  # 青海
    # '"iptv/live/zh_cn.js" && country="CN" && region="Xinjiang"',  # 新疆
    # '"iptv/live/zh_cn.js" && country="CN" && region="Tianjin"',  # 天津
    # '"iptv/live/zh_cn.js" && country="CN" && region="Hainan"',  # 海南
    # '"iptv/live/zh_cn.js" && country="CN" && region="Neimenggu"',  # 内蒙古
    # '"iptv/live/zh_cn.js" && country="CN" && region="Xizang"',  # 西藏
]

# IP存储目录
IP_DIR = "Hotel/ip"
if not os.path.exists(IP_DIR):
    os.makedirs(IP_DIR)

# 测速阈值 (MB/s)
SPEED_THRESHOLD = 0.1

# User-Agent列表
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"
]

# 省份卫视映射
PROVINCE_TV_MAP = {
    "北京": "北京卫视", "天津": "天津卫视", "河北": "河北卫视", "山西": "山西卫视", "内蒙古": "内蒙古卫视",
    "辽宁": "辽宁卫视", "吉林": "吉林卫视", "黑龙江": "黑龙江卫视", "上海": "上海卫视", "江苏": "江苏卫视",
    "浙江": "浙江卫视", "安徽": "安徽卫视", "福建": "东南卫视", "江西": "江西卫视", "山东": "山东卫视",
    "河南": "河南卫视", "湖北": "湖北卫视", "湖南": "湖南卫视", "广东": "广东卫视", "广西": "广西卫视",
    "海南": "海南卫视", "重庆": "重庆卫视", "四川": "四川卫视", "贵州": "贵州卫视", "云南": "云南卫视",
    "西藏": "西藏卫视", "陕西": "陕西卫视", "甘肃": "甘肃卫视", "青海": "青海卫视", "宁夏": "宁夏卫视",
    "新疆": "新疆卫视",
}


# ===============================
# 工具函数
# ===============================

def get_random_headers():
    """获取随机User-Agent的headers"""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cookie": FOFA_COOKIE
    }


def get_isp(ip):
    """IP运营商判断"""
    telecom_pattern = r"^(1\.|14\.|27\.|36\.|39\.|42\.|49\.|58\.|60\.|101\.|106\.|110\.|111\.|112\.|113\.|114\.|115\.|116\.|117\.|118\.|119\.|120\.|121\.|122\.|123\.|124\.|125\.|126\.|171\.|175\.|182\.|183\.|202\.|203\.|210\.|211\.|218\.|219\.|220\.|221\.|222\.)"
    unicom_pattern = r"^(42\.1[0-9]{0,2}|43\.|58\.|59\.|60\.|61\.|110\.|111\.|112\.|113\.|114\.|115\.|116\.|117\.|118\.|119\.|120\.|121\.|122\.|123\.|124\.|125\.|126\.|171\.8[0-9]|171\.9[0-9]|171\.1[0-9]{2}|175\.|182\.|183\.|210\.|211\.|218\.|219\.|220\.|221\.|222\.)"
    mobile_pattern = r"^(36\.|37\.|38\.|39\.1[0-9]{0,2}|42\.2|42\.3|47\.|106\.|111\.|112\.|113\.|114\.|115\.|116\.|117\.|118\.|119\.|120\.|121\.|122\.|123\.|124\.|125\.|126\.|134\.|135\.|136\.|137\.|138\.|139\.|150\.|151\.|152\.|157\.|158\.|159\.|170\.|178\.|182\.|183\.|184\.|187\.|188\.|189\.)"

    if re.match(telecom_pattern, ip):
        return "电信"
    elif re.match(unicom_pattern, ip):
        return "联通"
    elif re.match(mobile_pattern, ip):
        return "移动"
    else:
        return "未知"


def get_ip_info(ip_port):
    """获取IP地理信息"""
    try:
        ip = ip_port.split(":")[0]

        # 使用IP-API查询
        try:
            response = requests.get(f"http://ip-api.com/json/{ip}?lang=zh-CN", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    province = data.get("regionName", "未知")
                    isp = get_isp(ip)
                    return province, isp, ip_port
        except:
            pass

        return "未知", "未知", ip_port

    except Exception as e:
        return "未知", "未知", ip_port


def parse_ip_line(line):
    """解析IP行，支持格式：ip:port$运营商已存活n天"""
    line = line.strip()
    if not line or line.startswith('#'):
        return None, None, 0, None, None

    # 匹配IP:端口格式
    ip_match = re.match(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5})', line)
    if not ip_match:
        return None, None, 0, None, None

    ip_port = ip_match.group(1)

    # 尝试解析存活天数
    days_match = re.search(r'已存活(\d+)天', line)
    days = int(days_match.group(1)) if days_match else 0

    # 尝试解析运营商
    isp_match = re.search(r'\$([^$]+?)已存活', line)
    isp = isp_match.group(1).strip() if isp_match else ""

    # 尝试解析最后更新日期
    date_match = re.search(r'最后更新:(\d{4}-\d{2}-\d{2})', line)
    last_update = date_match.group(1) if date_match else None

    # 尝试解析速度
    speed_match = re.search(r'#速度:([\d.]+)MB/s', line)
    speed = float(speed_match.group(1)) if speed_match else 0.0

    return ip_port, isp, days, last_update, speed


def read_existing_ips(filepath):
    """读取现有文件内容并解析"""
    existing_ips = {}  # ip_port: (days, isp, last_update, speed)
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    ip_port, isp, days, last_update, speed = parse_ip_line(line)
                    if ip_port:
                        existing_ips[ip_port] = (days, isp, last_update, speed)
        except Exception as e:
            print(f"❌ 读取文件 {filepath} 失败: {e}")

    return existing_ips


def encode_query(query):
    """编码查询字符串为base64"""
    return base64.b64encode(query.encode()).decode()


def generate_fofa_urls():
    """生成FOFA搜索URL"""
    urls = []
    pages = 2
    page_size = 30

    for query in SEARCH_QUERIES:
        encoded_query = encode_query(query)
        for page in range(1, pages + 1):
            url = f"https://fofa.info/result?qbase64={encoded_query}&page={page}&page_size={page_size}"
            urls.append(url)

    return urls


# ===============================
# 爬取函数
# ===============================

def crawl_fofa_with_cookie():
    """使用Cookie爬取FOFA数据"""
    urls = generate_fofa_urls()
    all_ips = set()
    session = requests.Session()

    print(f"🔍 开始爬取FOFA，共 {len(urls)} 个搜索页面")

    for i, url in enumerate(urls, 1):
        print(f"📡 正在爬取第 {i}/{len(urls)} 页: {url}")

        try:
            # 随机延迟，避免请求过快
            time.sleep(random.uniform(2, 5))

            # 使用带Cookie的headers
            headers = get_random_headers()
            response = session.get(url, headers=headers, timeout=15)

            if response.status_code == 403 or "访问限制" in response.text or "请登录" in response.text:
                print(f"❌ 第 {i} 页访问被限制，可能需要重新登录")
                continue

            if response.status_code != 200:
                print(f"❌ 第 {i} 页请求失败，状态码: {response.status_code}")
                continue

            # 保存页面内容用于分析
            if i == 1:  # 只保存第一页用于调试
                with open("fofa_first_page.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
                print("💾 已保存第一页HTML到 fofa_first_page.html")

            # 多种正则表达式匹配IP
            ip_patterns = [
                r'<a[^>]*href="[^"]*?//(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5})"',  # IP:端口
                r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5})',  # 通用IP:端口格式
                r'ip.*?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).*?port.*?(\d{1,5})',  # IP和端口分开
                r'host.*?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).*?port.*?(\d{1,5})'  # host和port
            ]

            page_ips = set()
            for pattern in ip_patterns:
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        if len(match) == 2:
                            ip_port = f"{match[0]}:{match[1]}"
                        else:
                            continue
                    else:
                        ip_port = match

                    # 验证IP和端口格式
                    ip_match = re.match(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})', ip_port)
                    if ip_match:
                        # 验证IP地址的每个部分
                        ip_parts = ip_match.group(1).split('.')
                        if all(0 <= int(part) <= 255 for part in ip_parts):
                            # 验证端口
                            port = int(ip_match.group(2))
                            if 1 <= port <= 65535:
                                page_ips.add(ip_port)
                                print(f"✅ 找到IP: {ip_port}")

            all_ips.update(page_ips)
            print(f"✅ 第 {i} 页获取到 {len(page_ips)} 个IP，当前总数 {len(all_ips)}")

        except Exception as e:
            print(f"❌ 第 {i} 页爬取失败: {e}")

    print(f"🎯 FOFA爬取完成，总共获取到 {len(all_ips)} 个有效IP")
    return all_ips


# ===============================
# IP可用性验证和测速函数（保持原有逻辑）
# ===============================

def test_ip_availability(ip_port):
    """测试IP可用性"""
    try:
        # 测试JSON接口
        json_url = f"http://{ip_port}/iptv/live/1000.json?key=txiptv"
        response = requests.get(json_url, timeout=5)

        if response.status_code == 200:
            try:
                data = response.json()
                if data.get("code") == 0 and "data" in data:
                    return True, data
            except:
                pass
        return False, None
    except:
        return False, None


def get_province_tv_url(ip_port, json_data, province_name):
    """获取省份卫视URL"""
    try:
        tv_name = PROVINCE_TV_MAP.get(province_name)
        if not tv_name:
            return None

        for channel in json_data.get("data", []):
            if tv_name in channel.get("name", ""):
                url = channel.get("url", "")
                if url:
                    # 构建完整URL
                    if url.startswith("/"):
                        return f"http://{ip_port}{url}"
                    else:
                        return f"http://{ip_port}/{url}"
        return None
    except:
        return None


def test_channel_speed(channel_url, max_attempts=2):
    """测试频道速度（保持原有逻辑）"""
    best_speed = 0.0

    for attempt in range(max_attempts):
        try:
            # 获取m3u8文件内容
            response = requests.get(channel_url, timeout=3)
            if response.status_code != 200:
                if attempt < max_attempts - 1:
                    print(f"第{attempt + 1}次测速 {channel_url}: HTTP {response.status_code}，将重试")
                continue

            lines = response.text.strip().split('\n')
            ts_lists = [line.split('/')[-1] for line in lines if line.startswith('#') == False and line.strip()]
            if not ts_lists:
                if attempt < max_attempts - 1:
                    print(f"第{attempt + 1}次测速 {channel_url}: 没有找到TS列表，将重试")
                continue

            # 获取TS文件的URL
            channel_url_t = channel_url.rstrip(channel_url.split('/')[-1])
            ts_url = channel_url_t + ts_lists[0]

            # 测速逻辑
            start_time = time.time()
            try:
                with eventlet.Timeout(5, False):
                    ts_response = requests.get(ts_url, timeout=6, stream=True)
                    if ts_response.status_code != 200:
                        if attempt < max_attempts - 1:
                            print(f"第{attempt + 1}次测速 {channel_url}: TS文件HTTP {ts_response.status_code}，将重试")
                        continue

                    # 读取部分内容进行测速
                    content_length = 0
                    chunk_size = 1024 * 1024  # 1MB
                    for chunk in ts_response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            content_length += len(chunk)
                            # 只读取1MB用于测速
                            if content_length >= chunk_size:
                                break

                    resp_time = time.time() - start_time

                    if content_length > 0 and resp_time > 0:
                        normalized_speed = content_length / resp_time / 1024 / 1024

                        # 更新最佳速度
                        if normalized_speed > best_speed:
                            best_speed = normalized_speed

                        # 如果速度合格，不再重试
                        if normalized_speed > SPEED_THRESHOLD:
                            break
                        else:
                            if attempt < max_attempts - 1:
                                print(f"第{attempt + 1}次测速 {channel_url}: {normalized_speed:.3f} MB/s，将重试")
                    else:
                        if attempt < max_attempts - 1:
                            print(f"第{attempt + 1}次测速 {channel_url}: 获取内容失败，将重试")
            except eventlet.Timeout:
                if attempt < max_attempts - 1:
                    print(f"第{attempt + 1}次测速 {channel_url}: 请求超时，将重试")
                continue
            except Exception as e:
                if attempt < max_attempts - 1:
                    print(f"第{attempt + 1}次测速 {channel_url} 失败: {str(e)}，将重试")
                continue

        except Exception as e:
            if attempt < max_attempts - 1:
                print(f"第{attempt + 1}次测速 {channel_url} 处理失败: {str(e)}，将重试")
            continue

    return best_speed


def test_single_ip(ip_port, province_name):
    """测试单个IP的可用性和速度"""
    try:
        # 1. 测试IP可用性
        is_available, json_data = test_ip_availability(ip_port)
        if not is_available:
            return 0.0, False

        # 2. 获取省份卫视URL
        channel_url = get_province_tv_url(ip_port, json_data, province_name)
        if not channel_url:
            return 0.0, False

        # 3. 测速
        speed = test_channel_speed(channel_url)
        return speed, speed > SPEED_THRESHOLD

    except Exception as e:
        return 0.0, False


def speed_test_ips(ip_list, province_name):
    """多线程测速IP列表（保持原有逻辑）"""
    results = []
    checked = [0]
    total_count = len(ip_list)

    def show_progress():
        """显示进度"""
        while checked[0] < total_count:
            numberx = checked[0] / total_count * 100
            print(f"已测试{checked[0]}/{total_count}，可用频道:{len(results)}个，进度:{numberx:.2f}%")
            time.sleep(5)

    def worker():
        """工作线程"""
        while True:
            try:
                # 从队列中获取任务
                with task_queue_lock:
                    if not task_queue:
                        break
                    ip_info = task_queue.pop(0)

                ip_port = ip_info[0]
                speed, is_usable = test_single_ip(ip_port, province_name)

                if is_usable:
                    result = (ip_info[0], ip_info[1], ip_info[2], speed)
                    results.append(result)
                    print(f"✓ {ip_port}: {speed:.3f} MB/s")
                else:
                    print(f"× {ip_port}: {speed:.3f} MB/s")

                checked[0] += 1
            except Exception as e:
                checked[0] += 1
                print(f"处理 {ip_info[0]} 时发生错误: {e}")

    # 创建任务队列
    task_queue = ip_list.copy()
    task_queue_lock = threading.Lock()

    # 启动进度显示线程
    progress_thread = threading.Thread(target=show_progress, daemon=True)
    progress_thread.start()

    # 创建工作线程
    threads = []
    for _ in range(min(10, len(ip_list))):
        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()
        threads.append(thread)

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    # 按速度排序
    results.sort(key=lambda x: x[3], reverse=True)
    return results


# ===============================
# 文件管理和更新函数
# ===============================
def calculate_days_between(date_str1, date_str2):
    """计算两个日期字符串之间的天数差"""
    try:
        date1 = datetime.strptime(date_str1, "%Y-%m-%d")
        date2 = datetime.strptime(date_str2, "%Y-%m-%d")
        return (date2 - date1).days
    except:
        return 0



def update_ip_file(filepath, new_usable_ips):
    """更新IP文件 - 修复存活天数计算"""
    try:
        existing_ips = read_existing_ips(filepath)
        current_date = datetime.now().strftime("%Y-%m-%d")

        updated_ips = {}
        for ip_port, (days, isp, last_update, old_speed) in existing_ips.items():
            is_still_usable = any(ip[0] == ip_port for ip in new_usable_ips)

            if is_still_usable:
                if not isp:
                    ip = ip_port.split(":")[0]
                    isp = get_isp(ip)

                if last_update:
                    days_diff = calculate_days_between(last_update, current_date)
                    if days_diff > 0:
                        new_days = days + days_diff
                    else:
                        new_days = days
                else:
                    new_days = 1

                # 获取新的速度
                new_speed = old_speed
                for ip_info in new_usable_ips:
                    if ip_info[0] == ip_port:
                        new_speed = ip_info[3]
                        break

                updated_ips[ip_port] = (new_days, isp, current_date, new_speed)
            elif days > 0:
                updated_ips[ip_port] = (days, isp, last_update, old_speed)

        for ip_info in new_usable_ips:
            ip_port, isp, old_days, speed = ip_info
            if ip_port not in updated_ips:
                if not isp:
                    ip = ip_port.split(":")[0]
                    isp = get_isp(ip)
                updated_ips[ip_port] = (1, isp, current_date, speed)

        if not updated_ips:
            if os.path.exists(filepath):
                os.remove(filepath)
            print(f"🗑️ 删除空文件: {os.path.basename(filepath)}")
            return

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 测速阈值: {SPEED_THRESHOLD} MB/s\n")
            f.write("# 格式: IP:端口$运营商已存活n天#最后更新:YYYY-MM-DD#速度\n")
            f.write("=" * 50 + "\n")

            sorted_ips = sorted(updated_ips.items(), key=lambda x: x[1][0], reverse=True)

            for ip_port, (days, isp, last_update, speed) in sorted_ips:
                speed_info = f"#速度:{speed:.3f}MB/s" if speed > 0 else ""
                f.write(f"{ip_port}${isp}已存活{days}天#最后更新:{last_update}{speed_info}\n")

        print(f"💾 已更新 {os.path.basename(filepath)}，有效IP: {len(updated_ips)} 个")

    except Exception as e:
        print(f"❌ 更新文件 {filepath} 失败: {e}")


def validate_existing_ips():
    """验证现有IP文件中的IP"""
    print("🔍 开始验证现有IP文件...")

    for filename in os.listdir(IP_DIR):
        if filename.endswith('.txt') and filename != "ip_summary.txt":
            filepath = os.path.join(IP_DIR, filename)

            match = re.match(r'(.+?)(电信|联通|移动|未知)\.txt', filename)
            if not match:
                continue

            province = match.group(1)
            isp = match.group(2)

            print(f"📋 验证文件: {filename} (省份: {province}, 运营商: {isp})")

            existing_ips = read_existing_ips(filepath)
            if not existing_ips:
                print(f"⚠️ 文件 {filename} 为空，跳过验证")
                continue

            ip_list = []
            for ip_port, (days, isp_val, last_update, speed) in existing_ips.items():
                ip_list.append((ip_port, isp_val, days))

            usable_ips = speed_test_ips(ip_list, province)
            update_ip_file(filepath, usable_ips)

    print("✅ 现有IP验证完成")


def process_new_ips(new_ips):
    """处理新获取的IP - 修复运营商获取"""
    if not new_ips:
        print("⚠️ 没有获取到新IP")
        return

    print(f"🔧 开始处理 {len(new_ips)} 个新IP...")

    # 获取IP信息
    province_isp_dict = {}

    # 使用线程池获取IP信息
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_ip = {executor.submit(get_ip_info, ip): ip for ip in new_ips}

        for future in concurrent.futures.as_completed(future_to_ip):
            province, isp, ip_port = future.result()

            # 确保省份和运营商不为空
            if not province or province == "未知":
                province = "其他"
            else:
                # 清理省份名称
                province = province.replace("省", "").replace("市", "").replace("自治区", "").replace("特别行政区", "").strip()
                if not province:
                    province = "其他"

            if not isp or isp == "未知":
                ip = ip_port.split(":")[0]
                isp = get_isp(ip)

            fname = f"{province}{isp}.txt"
            province_isp_dict.setdefault(fname, []).append((ip_port, isp, 0))  # 新IP存活天数为0

    # 测试并保存新IP
    for fname, ip_list in province_isp_dict.items():
        filepath = os.path.join(IP_DIR, fname)

        # 从文件名提取省份
        match = re.match(r'(.+?)(电信|联通|移动|未知)\.txt', fname)
        province = match.group(1) if match else "其他"

        print(f"🧪 测试 {fname} 中的 {len(ip_list)} 个新IP...")
        usable_ips = speed_test_ips(ip_list, province)

        if usable_ips:
            update_ip_file(filepath, usable_ips)
        else:
            print(f"⚠️ {fname} 中没有可用的新IP")

    print("✅ 新IP处理完成")


# ===============================
# 主函数
# ===============================

def main():
    """主函数"""
    print("=" * 60)
    print("🌐 FOFA IP地址抓取与验证工具")
    print(f"📁 输出目录: {IP_DIR}")
    print(f"⚡ 测速阈值: {SPEED_THRESHOLD} MB/s")
    print("=" * 60)

    # 第一阶段：验证现有IP
    validate_existing_ips()

    # 第二阶段：爬取新IP
    print("\n🚀 开始爬取FOFA新IP...")
    new_ips = crawl_fofa_with_cookie()

    if new_ips:
        # 处理新IP
        process_new_ips(new_ips)
    else:
        print("❌ 没有获取到新IP")

    print("\n" + "=" * 60)
    print("🎉 任务完成！")
    print("=" * 60)


if __name__ == "__main__":
    # 安装依赖: pip install eventlet
    main()
