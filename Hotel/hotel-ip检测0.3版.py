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

# FOFA Cookie（可能需要更新）
FOFA_COOKIE = "isRedirectLang=1; is_mobile=pc; _ga=GA1.1.160198945.1769557307; Hm_lvt_4275507ba9b9ea6b942c7a3f7c66da90=1769557307; HMACCOUNT=581AA0E813A2B463; __fcd=N4SR6J0XFKSRM1MP3909FFC89DFB9F17; befor_router=%2Fcaptcha%3Fredirect%3D%252Fresult%253Fqbase64%253DImlwdHYvbGl2ZS96aF9jbi5qcyIgJiYgY291bnRyeT0iQ04i; fofa_token=eyJhbGciOiJIUzUxMiIsImtpZCI6Ik5XWTVZakF4TVRkalltSTJNRFZsWXpRM05EWXdaakF3TURVMlkyWTNZemd3TUdRd1pUTmpZUT09IiwidHlwIjoiSldUIn0.eyJpZCI6MTE4MTAxMSwibWlkIjoxMDA3NDEyMzIsInVzZXJuYW1lIjoiT1VfeWFuZyIsInBhcmVudF9pZCI6MCwiZXhwIjoxNzcwMTYyMjM5fQ.ljqZV_EcYuwtmxrjZzvAg5E-AydXGtOBn7xnJXXWNmcKwzy8Z8HCV_3Fz19PlTHH97gN_CSCPAf8RGzgEXyZgQ; user=%7B%22id%22%3A1181011%2C%22mid%22%3A100741232%2C%22is_admin%22%3Afalse%2C%22username%22%3A%22OU_yang%22%2C%22nickname%22%3A%22OU_yang%22%2C%22email%22%3A%222856364053%40qq.com%22%2C%22avatar_medium%22%3A%22https%3A%2F%2Fnosec.org%2Fmissing.jpg%22%2C%22avatar_thumb%22%3A%22https%3A%2F%2Fnosec.org%2Fmissing.jpg%22%2C%22key%22%3A%229495b90e65813ae0e9188e6a5928d1f1%22%2C%22category%22%3A%22user%22%2C%22rank_avatar%22%3A%22%22%2C%22rank_level%22%3A0%2C%22rank_name%22%3A%22%E6%B3%A8%E5%86%8C%E7%94%A8%E6%88%B7%22%2C%22company_name%22%3A%22OU_yang%22%2C%22coins%22%3A0%2C%22can_pay_coins%22%3A0%2C%22fofa_point%22%3A0%2C%22credits%22%3A1%2C%22expiration%22%3A%22-%22%2C%22login_at%22%3A0%2C%22data_limit%22%3A%7B%22web_query%22%3A300%2C%22web_data%22%3A3000%2C%22api_query%22%3A0%2C%22api_data%22%3A0%2C%22data%22%3A-1%2C%22query%22%3A-1%7D%2C%22expiration_notice%22%3Afalse%2C%22remain_giveaway%22%3A1000%2C%22fpoint_upgrade%22%3Afalse%2C%22account_status%22%3A%22%22%2C%22parents_id%22%3A0%2C%22parents_email%22%3A%22%22%2C%22parents_fpoint%22%3A0%2C%22created_at%22%3A%222026-01-25%2000%3A00%3A00%22%7D; is_flag_login=1; baseShowChange=false; viewOneHundredData=false; _ga_9GWBD260K9=GS2.1.s1769557306$o1$g1$t1769557469$j35$l0$h0; Hm_lpvt_4275507ba9b9ea6b942c7a3f7c66da90=1769557469"

# 搜索关键词（修正省份名称）
SEARCH_QUERIES = [
    '"iptv/live/zh_cn.js" && country="CN" && region="Anhui"',  # 安徽
    '"iptv/live/zh_cn.js" && country="CN" && region="Beijing"',  # 北京
    '"iptv/live/zh_cn.js" && country="CN" && region="Shanghai"',  # 上海
    '"iptv/live/zh_cn.js" && country="CN" && region="Jiangsu"',  # 江苏
    '"iptv/live/zh_cn.js" && country="CN" && region="Zhejiang"',  # 浙江
    '"iptv/live/zh_cn.js" && country="CN" && region="Fujian"',  # 福建
    '"iptv/live/zh_cn.js" && country="CN" && region="Guangdong"',  # 广东（修正）
    '"iptv/live/zh_cn.js" && country="CN" && region="Hunan"',  # 湖南
    '"iptv/live/zh_cn.js" && country="CN" && region="Hubei"',  # 湖北
    '"iptv/live/zh_cn.js" && country="CN" && region="Henan"',  # 河南
    '"iptv/live/zh_cn.js" && country="CN" && region="Hebei"',  # 河北
    '"iptv/live/zh_cn.js" && country="CN" && region="Shandong"',  # 山东
    '"iptv/live/zh_cn.js" && country="CN" && region="Shanxi"',  # 山西
    '"iptv/live/zh_cn.js" && country="CN" && region="Shaanxi"',  # 陕西
    '"iptv/live/zh_cn.js" && country="CN" && region="Sichuan"',  # 四川
    '"iptv/live/zh_cn.js" && country="CN" && region="Chongqing"',  # 重庆
    '"iptv/live/zh_cn.js" && country="CN" && region="Liaoning"',  # 辽宁
    '"iptv/live/zh_cn.js" && country="CN" && region="Jilin"',  # 吉林
    '"iptv/live/zh_cn.js" && country="CN" && region="Heilongjiang"',  # 黑龙江
    '"iptv/live/zh_cn.js" && country="CN" && region="Jiangxi"',  # 江西
    '"iptv/live/zh_cn.js" && country="CN" && region="Guangxi"',  # 广西
    '"iptv/live/zh_cn.js" && country="CN" && region="Yunnan"',  # 云南
    '"iptv/live/zh_cn.js" && country="CN" && region="Guizhou"',  # 贵州
    '"iptv/live/zh_cn.js" && country="CN" && region="Gansu"',  # 甘肃
    '"iptv/live/zh_cn.js" && country="CN" && region="Ningxia"',  # 宁夏
    '"iptv/live/zh_cn.js" && country="CN" && region="Qinghai"',  # 青海
    '"iptv/live/zh_cn.js" && country="CN" && region="Xinjiang"',  # 新疆
    '"iptv/live/zh_cn.js" && country="CN" && region="Tianjin"',  # 天津
    '"iptv/live/zh_cn.js" && country="CN" && region="Hainan"',  # 海南
    '"iptv/live/zh_cn.js" && country="CN" && region="Neimenggu"',  # 内蒙古
    '"iptv/live/zh_cn.js" && country="CN" && region="Xizang"',  # 西藏
]

# IP存储目录
IP_DIR = "Hotel/ip"
if not os.path.exists(IP_DIR):
    os.makedirs(IP_DIR)

# 频道文件输出目录
CHANNEL_DIR = "Hotel"
if not os.path.exists(CHANNEL_DIR):
    os.makedirs(CHANNEL_DIR)

# 测速阈值 (MB/s)
SPEED_THRESHOLD = 0.1

# User-Agent列表
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"
]

# 频道分类定义
CHANNEL_CATEGORIES = {
    "央视频道": [
        "CCTV1", "CCTV2", "CCTV3", "CCTV4", "CCTV4欧洲", "CCTV4美洲", "CCTV5", "CCTV5+", "CCTV6", "CCTV7",
        "CCTV8", "CCTV9", "CCTV10", "CCTV11", "CCTV12", "CCTV13", "CCTV14", "CCTV15", "CCTV16", "CCTV17",
        "兵器科技", "风云音乐", "风云足球", "风云剧场", "怀旧剧场", "第一剧场", "女性时尚", "世界地理", "央视台球", "高尔夫网球",
        "央视文化精品", "卫生健康", "电视指南", "老故事", "中学生", "发现之旅", "书法频道", "国学频道", "环球奇观",
        "CETV1", "CETV2", "CETV3", "CETV4", "早期教育", "CGTN纪录",
    ],
    "卫视频道": [
        "重温经典", "湖南卫视", "浙江卫视", "江苏卫视", "东方卫视", "深圳卫视", "北京卫视", "广东卫视", "广西卫视", "东南卫视", "海南卫视",
        "河北卫视", "河南卫视", "湖北卫视", "江西卫视", "四川卫视", "重庆卫视", "贵州卫视", "云南卫视", "天津卫视", "安徽卫视", "厦门卫视",
        "山东卫视", "辽宁卫视", "黑龙江卫视", "吉林卫视", "内蒙古卫视", "宁夏卫视", "山西卫视", "陕西卫视", "甘肃卫视", "青海卫视",
        "新疆卫视", "西藏卫视", "三沙卫视", "兵团卫视", "延边卫视", "安多卫视", "康巴卫视", "农林卫视", "山东教育卫视",
    ],
    "数字频道": [
        "CHC动作电影", "CHC家庭影院", "CHC影迷电影", "淘电影", "淘精彩", "淘剧场", "淘4K", "淘娱乐", "淘BABY", 
        "淘萌宠", "海看大片", "经典电影", "精彩影视", "喜剧影院", "动作影院", "精品剧场", "IPTV戏曲", "求索纪录", "求索科学", "法制天地",
        "求索生活", "求索动物", "纪实人文", "金鹰纪实", "纪实科教", "睛彩青少", "睛彩竞技", "睛彩篮球", "睛彩广场舞", "魅力足球", "五星体育", "体育赛事",
        "劲爆体育", "快乐垂钓", "四海钓鱼", "茶频道", "先锋乒羽", "天元围棋", "汽摩", "车迷频道", "梨园频道", "文物宝库", "武术世界",
        "乐游", "生活时尚", "都市剧场", "欢笑剧场", "金色学堂", "动漫秀场", "新动漫", "金鹰卡通", "优漫卡通", "哈哈炫动", "嘉佳卡通", 
        "优优宝贝", "中国交通", "中国天气", "网络棋牌", 
    ],
    "港澳台频道": [
        "凤凰卫视中文台", "凤凰卫视资讯台", "凤凰卫视香港台", "凤凰卫视电影台", "龙祥时代", "星空卫视", "CHANNEL[V]", "", "", "", "", "", "", "", "",
    ],
    "安徽频道": [
        "安徽影视", "安徽经济生活", "安徽公共", "安徽综艺体育", "安徽农业科教", "阜阳公共频道", "马鞍山新闻综合", "马鞍山公共", "", "", "", "环球奇观",
        "临泉一台", "", "", "", "", "", "", "",
        "", "", "", "", "", "", "", "", "", "", "",
    ],
    "北京频道": [
        "北京纪实科教", "", "", "", "", "", "", "", "", "北京卡酷少儿", 
    ],
    "上海频道": [
        "新闻综合", "都市频道", "东方影视", "纪实人文", "第一财经", "五星体育", "东方财经", "ICS频道", "上海教育台", "七彩戏剧", "法治天地", "金色学堂",
        "动漫秀场", "欢笑剧场4K", "生活时尚", "", "", "", "", "",
        "", "", "", "", "", "", "", "", "", "", "",
    ],
    "湖南频道": [
        "湖南国际", "湖南电影", "湖南电视剧", "湖南经视", "湖南娱乐", "湖南公共", "湖南都市", "湖南教育", "芒果互娱", "长沙新闻", "长沙政法", "长沙影视", "长沙女性", "",
        "益阳公共", "抗战剧场", "古装剧场", "高清院线", "先锋兵羽", "望城综合", "花鼓戏", "",
        "", "", "", "", "", "", "", "", "", "", "",
    ],
    "湖北频道": [
        "湖北综合", "湖北影视", "湖北生活", "湖北教育", "湖北经视", "荆州新闻", "荆州垄上", "", "", "", "", "", "", "", "", "",
    ],
    "河北频道": [
        "河北影视剧", "河北都市", "河北经济", "河北公共", "河北少儿科教", "河北三农", "衡水新闻", "衡水公共", "", "", "", "", "", "",
    ],
    "山东频道": [
        "山东综艺", "山东影视", "山东齐鲁", "山东农科", "山东体育", "山东生活", "山东少儿", "烟台新闻", "山东教育", "临沂导视", "临沂图文", "临沂综合", "临沂农科", "兰陵导视", "兰陵公共", "兰陵综合",
    ],
    "广东频道": [
        "广东影视", "", "", "", "", "", "广东科教", "广东体育", "广州新闻", "广东珠江", "深圳都市", "深圳少儿", "嘉佳卡通", "茂名综合", "", "", "",
    ],
    "广西频道": [
        "广西影视", "广西综艺", "广西都市", "广西新闻", "广西移动", "广西科技", "精彩影视", "平南台", "南宁影视", "玉林新闻综合", "", "", "", "", "", "", "",
    ],
    "四川频道": [
        "四川新闻", "四川文化旅游", "四川影视文艺", "峨眉电影", "熊猫影院", "广元综合", "广元公共", "四川卫视-乡村公共", "蓬安电视台", "", "", "", "", "", "", "", "金熊猫卡通",
    ],
    "陕西频道": [
        "", "", "", "", "", "", "", "", "三门峡新闻综合", "灵宝新闻综合", "", "", "", "", "", "", "",
    ],    
    "浙江频道": [
        "浙江新闻", "杭州影视", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",
    ], 
    "吉林频道": [
        "吉林影视", "吉林都市", "吉林乡村", "吉林教育", "吉林综艺", "吉林生活", "", "", "长影频道", "松原公共", "松原", "", "", "", "", "", "",
    ],
    "新疆频道": [
        "新疆2", "新疆3", "新疆4", "新疆5", "新疆6", "新疆7", "新疆8", "新疆9", "", "", "", "", "", "", "", "", "",
    ],
    "其他频道": []
}

# 特殊符号映射
SPECIAL_SYMBOLS = ["HD", "LT", "XF", "-", "_", " ", ".", "·", "高清", "标清", "超清", "H265", "4K", "FHD", "HDTV"]

# 频道名称映射
CHANNEL_MAPPING = {
    "CCTV1": ["CCTV1", "CCTV-1", "CCTV1综合", "CCTV1高清", "CCTV1HD", "cctv1", "中央1台", "sCCTV1-综合", "CCTV01"],
    "CCTV2": ["CCTV2", "CCTV-2", "CCTV2财经", "CCTV2高清", "CCTV2HD", "cctv2", "中央2台", "aCCTV2", "sCCTV2-财经", "CCTV02"],
    "CCTV3": ["CCTV3", "CCTV-3", "CCTV3综艺", "CCTV3高清", "CCTV3HD", "cctv3", "中央3台", "acctv3", "sCCTV3-综艺", "CCTV03"],
    "CCTV4": ["CCTV4", "CCTV-4", "CCTV4中文国际", "CCTV4高清", "CCTV4HD", "cctv4", "中央4台", "aCCTV4", "sCCTV4-国际", "CCTV04"],
    "CCTV5": ["CCTV5", "CCTV-5", "CCTV5体育", "CCTV5高清", "CCTV5HD", "cctv5", "中央5台", "sCCTV5-体育", "CCTV05"],
    "CCTV5+": ["CCTV5+", "CCTV-5+", "CCTV5+体育赛事", "CCTV5+高清", "CCTV5+HD", "cctv5+", "CCTV5plus"],
    "CCTV6": ["CCTV6", "CCTV-6", "CCTV6电影", "CCTV6高清", "CCTV6HD", "cctv6", "中央6台", "sCCTV6-电影", "CCTV06"],
    "CCTV7": ["CCTV7", "CCTV-7", "CCTV7军事", "CCTV7高清", "CCTV7HD", "cctv7", "中央7台", "CCTV07"],
    "CCTV8": ["CCTV8", "CCTV-8", "CCTV8电视剧", "CCTV8高清", "CCTV8HD", "cctv8", "中央8台", "sCCTV8-电视剧", "CCTV08"],
    "CCTV9": ["CCTV9", "CCTV-9", "CCTV9纪录", "CCTV9高清", "CCTV9HD", "cctv9", "中央9台", "sCCTV9-纪录", "CCTV09"],
    "CCTV10": ["CCTV10", "CCTV-10", "CCTV10科教", "CCTV10高清", "CCTV10HD", "cctv10", "中央10台", "sCCTV10-科教"],
    "CCTV11": ["CCTV11", "CCTV-11", "CCTV11戏曲", "CCTV11高清", "CCTV11HD", "cctv11", "中央11台", "sCCTV11-戏曲"],
    "CCTV12": ["CCTV12", "CCTV-12", "CCTV12社会与法", "CCTV12高清", "CCTV12HD", "cctv12", "中央12台", "sCCTV12-社会与法"],
    "CCTV13": ["CCTV13", "CCTV-13", "CCTV13新闻", "CCTV13高清", "CCTV13HD", "cctv13", "中央13台", "sCCTV13-新闻"],
    "CCTV14": ["CCTV14", "CCTV-14", "CCTV14少儿", "CCTV14高清", "CCTV14HD", "cctv14", "中央14台", "sCCTV14-少儿"],
    "CCTV15": ["CCTV15", "CCTV-15", "CCTV15音乐", "CCTV15高清", "CCTV15HD", "cctv15", "中央15台", "sCCTV15-音乐"],
    "CCTV16": ["CCTV16", "CCTV-16", "CCTV16奥林匹克", "CCTV16高清", "CCTV16HD", "cctv16", "中央16台"],
    "CCTV17": ["CCTV17", "CCTV-17", "CCTV17农业农村", "CCTV17高清", "CCTV17HD", "cctv17", "中央17台"],
    
    "浙江卫视": ["浙江卫视", "浙江卫视高清"],
    "北京卫视": ["北京卫视", "北京卫视HD", "北京卫视高清"],
    "湖南卫视": ["湖南卫视", "湖南电视"],
    "江苏卫视": ["江苏卫视", "江苏卫视HD", "江苏卫视高清"],
    "东方卫视": ["东方卫视", "上海卫视", "SBN"],
    "安徽卫视": ["安徽卫视", "安徽卫视高清"],
    "山东卫视": ["山东卫视", "山东高清", "山东卫视高清", "山东卫视HD"],
    "广东卫视": ["广东卫视", "广东卫视高清"],
    "深圳卫视": ["深圳卫视", "深圳卫视高清", "深圳"],
    "天津卫视": ["天津卫视"],
    "河北卫视": ["河北卫视"],
    "山西卫视": ["山西卫视"],
    "内蒙古卫视": ["内蒙古卫视", "内蒙古", "内蒙卫视"],
    "辽宁卫视": ["辽宁卫视", "辽宁卫视HD"],
    "吉林卫视": ["吉林卫视"],
    "黑龙江卫视": ["黑龙江卫视"],
    "上海卫视": ["上海卫视", "东方卫视"],
    "福建东南卫视": ["东南卫视", "福建东南"],
    "江西卫视": ["江西卫视"],
    "河南卫视": ["河南卫视"],
    "湖北卫视": ["湖北卫视"],
    "广西卫视": ["广西卫视"],
    "海南卫视": ["海南卫视", "旅游卫视", "海南卫视HD"],
    "重庆卫视": ["重庆卫视"],
    "四川卫视": ["四川卫视", "四川卫视高清"],
    "贵州卫视": ["贵州卫视"],
    "云南卫视": ["云南卫视"],
    "西藏卫视": ["西藏卫视", "XZTV2"],
    "陕西卫视": ["陕西卫视"],
    "甘肃卫视": ["甘肃卫视"],
    "青海卫视": ["青海卫视"],
    "宁夏卫视": ["宁夏卫视"],
    "新疆卫视": ["新疆卫视", "新疆1"],
    
    "凤凰卫视中文台": ["凤凰卫视中文台", "凤凰中文", "凤凰卫视"],
    "凤凰卫视资讯台": ["凤凰卫视资讯台", "凤凰资讯", "凤凰咨询"],
    "凤凰卫视香港台": ["凤凰卫视香港台", "凤凰香港"],
    "凤凰卫视电影台": ["凤凰卫视电影台", "凤凰电影", "鳳凰衛視電影台"],
}

# 图标文件路径
LOGO_FILE = "Hotel/logo.txt"

# ===============================
# 工具函数
# ===============================

def get_random_headers():
    """获取随机User-Agent的headers"""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
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
    """解析IP行，支持格式：ip:port 或 ip:port$运营商已存活n天"""
    line = line.strip()
    if not line or line.startswith('#'):
        return None, None, 0
    
    # 匹配IP:端口格式
    ip_match = re.match(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5})', line)
    if not ip_match:
        return None, None, 0
    
    ip_port = ip_match.group(1)
    
    # 尝试解析存活天数
    days_match = re.search(r'已存活(\d+)天', line)
    days = int(days_match.group(1)) if days_match else 0
    
    # 尝试解析运营商 - 修复这里的正则表达式
    # 运营商应该在$符号和"已存活"之间
    isp_match = re.search(r'\$([^$]+?)已存活', line)
    isp = isp_match.group(1).strip() if isp_match else ""
    
    return ip_port, isp, days

def read_existing_ips(filepath):
    """读取现有文件内容并解析"""
    existing_ips = {}  # ip_port: (days, isp)
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    ip_port, isp, days = parse_ip_line(line)
                    if ip_port:
                        existing_ips[ip_port] = (days, isp)
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
    page_size = 20
    
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
            time.sleep(random.uniform(3, 8))
            
            # 使用带Cookie的headers
            headers = get_random_headers()
            response = session.get(url, headers=headers, timeout=20)
            
            if response.status_code == 403 or "访问限制" in response.text or "请登录" in response.text or "[-3000]" in response.text:
                print(f"❌ 第 {i} 页访问被限制，Cookie可能已失效")
                # 保存当前页面用于调试
                with open(f"debug_page_{i}.html", "w", encoding="utf-8") as f:
                    f.write(response.text[:5000])  # 只保存前5000字符
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
                r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5})',  # 通用IP:端口
                r'<div[^>]*class="hsxa-clearfix"[^>]*>.*?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).*?(\d{1,5})</div>',  # 新版格式
            ]
            
            page_ips = set()
            for pattern in ip_patterns:
                matches = re.findall(pattern, response.text, re.IGNORECASE | re.DOTALL)
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
                        ip_parts = ip_match.group(1).split('.')
                        if all(0 <= int(part) <= 255 for part in ip_parts):
                            page_ips.add(ip_port)
                            print(f"✅ 找到IP: {ip_port}")
            
            all_ips.update(page_ips)
            print(f"✅ 第 {i} 页获取到 {len(page_ips)} 个IP，当前总数 {len(all_ips)}")
            
        except Exception as e:
            print(f"❌ 第 {i} 页爬取失败: {e}")
    
    print(f"🎯 FOFA爬取完成，总共获取到 {len(all_ips)} 个有效IP")
    return all_ips

# ===============================
# IP可用性验证和测速函数
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
        # 从频道分类中查找对应的卫视名称
        for category, channels in CHANNEL_CATEGORIES.items():
            for channel in channels:
                if province_name in channel and "卫视" in channel:
                    tv_name = channel
                    break
            else:
                continue
            break
        else:
            # 如果没有找到，使用通用名称
            tv_name = f"{province_name}卫视"
        
        for channel in json_data.get("data", []):
            channel_name = channel.get("name", "")
            if tv_name in channel_name:
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
    """测试频道速度"""
    best_speed = 0.0
    
    for attempt in range(max_attempts):
        try:
            # 获取m3u8文件内容
            response = requests.get(channel_url, timeout=3)
            if response.status_code != 200:
                continue
            
            lines = response.text.strip().split('\n')
            ts_lists = [line.split('/')[-1] for line in lines if not line.startswith('#') and line.strip()]
            
            if not ts_lists:
                continue
            
            # 获取TS文件的URL
            channel_url_t = channel_url.rstrip(channel_url.split('/')[-1])
            ts_url = channel_url_t + ts_lists[0]
            
            # 测速逻辑
            start_time = time.time()
            
            try:
                eventlet.monkey_patch()
                with eventlet.Timeout(5, False):
                    ts_response = requests.get(ts_url, timeout=6, stream=True)
                    if ts_response.status_code != 200:
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
                        if normalized_speed > best_speed:
                            best_speed = normalized_speed
                        
                        # 如果速度合格，不再重试
                        if normalized_speed > SPEED_THRESHOLD:
                            break
            except eventlet.Timeout:
                continue
            except Exception:
                continue
                
        except Exception:
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
    """多线程测速IP列表"""
    results = []
    task_queue = Queue()
    
    # 添加任务到队列
    for ip_info in ip_list:
        task_queue.put(ip_info)
    
    def worker():
        while True:
            try:
                ip_info = task_queue.get_nowait()
                ip_port = ip_info[0]
                speed, is_usable = test_single_ip(ip_port, province_name)
                
                if is_usable:
                    results.append((ip_info[0], ip_info[1], ip_info[2], speed))
                    print(f"✅ {ip_port} - 速度: {speed:.3f} MB/s")
                else:
                    print(f"❌ {ip_port} - 速度: {speed:.3f} MB/s (不可用)")
                
                task_queue.task_done()
            except:
                break
    
    # 创建并启动线程
    threads = []
    for _ in range(min(5, len(ip_list))):  # 减少线程数
        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()
        threads.append(thread)
    
    # 等待所有任务完成
    task_queue.join()
    
    # 按速度排序
    results.sort(key=lambda x: x[3], reverse=True)
    return results

# ===============================
# 文件管理和更新函数
# ===============================

def update_ip_file(filepath, new_usable_ips):
    """更新IP文件"""
    try:
        # 读取现有IP
        existing_ips = read_existing_ips(filepath)
        
        # 更新存活天数
        updated_ips = {}
        for ip_port, (days, isp) in existing_ips.items():
            # 检查IP是否在新可用列表中
            is_still_usable = any(ip[0] == ip_port for ip in new_usable_ips)
            if is_still_usable:
                updated_ips[ip_port] = (days + 1, isp)
            # 如果不在新列表中但原来可用，保持原样
            elif days > 0:
                updated_ips[ip_port] = (days, isp)
        
        # 添加新IP
        for ip_info in new_usable_ips:
            ip_port, isp, days, speed = ip_info
            if ip_port not in updated_ips:
                updated_ips[ip_port] = (1, isp)
        
        # 如果文件为空，删除文件
        if not updated_ips:
            if os.path.exists(filepath):
                os.remove(filepath)
            print(f"🗑️ 删除空文件: {os.path.basename(filepath)}")
            return
        
        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 测速阈值: {SPEED_THRESHOLD} MB/s\n")
            f.write("# 格式: IP:端口$运营商已存活n天#速度\n")
            f.write("=" * 50 + "\n")
            
            # 按存活天数排序
            sorted_ips = sorted(updated_ips.items(), key=lambda x: x[1][0], reverse=True)
            
            for ip_port, (days, isp) in sorted_ips:
                # 查找速度信息
                speed_info = ""
                for ip_info in new_usable_ips:
                    if ip_info[0] == ip_port:
                        speed_info = f"#速度:{ip_info[3]:.3f}MB/s"
                        break
                
                f.write(f"{ip_port}${isp}已存活{days}天{speed_info}\n")
        
        print(f"💾 已更新 {os.path.basename(filepath)}，有效IP: {len(updated_ips)} 个")
        
    except Exception as e:
        print(f"❌ 更新文件 {filepath} 失败: {e}")

def validate_existing_ips():
    """验证现有IP文件中的IP"""
    print("🔍 开始验证现有IP文件...")
    
    for filename in os.listdir(IP_DIR):
        if filename.endswith('.txt') and filename != "ip_summary.txt":
            filepath = os.path.join(IP_DIR, filename)
            
            # 从文件名提取省份和运营商
            match = re.match(r'(.+?)(电信|联通|移动|未知)\.txt', filename)
            if not match:
                continue
                
            province = match.group(1)
            isp = match.group(2)
            
            print(f"📋 验证文件: {filename} (省份: {province}, 运营商: {isp})")
            
            # 读取IP
            existing_ips = read_existing_ips(filepath)
            if not existing_ips:
                print(f"⚠️ 文件 {filename} 为空，跳过验证")
                continue
            
            # 准备测试数据
            ip_list = [(ip, isp, days) for ip, (days, isp_val) in existing_ips.items()]
            
            # 测试IP
            usable_ips = speed_test_ips(ip_list, province)
            
            # 更新文件
            update_ip_file(filepath, usable_ips)
    
    print("✅ 现有IP验证完成")

def process_new_ips(new_ips):
    """处理新获取的IP"""
    if not new_ips:
        print("⚠️ 没有获取到新IP")
        return
    
    print(f"🔧 开始处理 {len(new_ips)} 个新IP...")
    
    # 获取IP信息
    province_isp_dict = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_ip = {executor.submit(get_ip_info, ip): ip for ip in new_ips}
        
        for future in concurrent.futures.as_completed(future_to_ip):
            province, isp, ip_port = future.result()
            if province and isp and isp != "未知":
                province_clean = province.replace("省", "").replace("市", "").replace("自治区", "").strip()
                if not province_clean:
                    province_clean = "其他"
                fname = f"{province_clean}{isp}.txt"
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
# 频道文件生成功能
# ===============================

def remove_special_symbols(text):
    """移除频道名称中的特殊符号"""
    for symbol in SPECIAL_SYMBOLS:
        text = text.replace(symbol, "")
    # 移除多余的空格
    text = re.sub(r'\s+', '', text)
    return text.strip()

def load_channel_logos():
    """加载频道图标映射"""
    channel_logos = {}
    if os.path.exists(LOGO_FILE):
        try:
            with open(LOGO_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and ',' in line:
                        parts = line.split(',', 1)
                        if len(parts) == 2:
                            channel_name = parts[0].strip()
                            logo_url = parts[1].strip()
                            channel_logos[channel_name] = logo_url
            print(f"✅ 已加载 {len(channel_logos)} 个频道图标")
        except Exception as e:
            print(f"❌ 加载频道图标文件失败: {e}")
    else:
        print(f"⚠️ 频道图标文件不存在: {LOGO_FILE}")
    return channel_logos

def map_channel_name(raw_name):
    """将原始频道名称映射到标准名称"""
    if not raw_name:
        return "未知频道"
    
    # 清理频道名称
    clean_name = remove_special_symbols(raw_name)
    
    # 在映射中查找
    for standard_name, variants in CHANNEL_MAPPING.items():
        for variant in variants:
            if clean_name == remove_special_symbols(variant):
                return standard_name
    
    # 如果没有找到匹配，尝试部分匹配
    for standard_name, variants in CHANNEL_MAPPING.items():
        for variant in variants:
            if standard_name in clean_name or clean_name in standard_name:
                return standard_name
            # 检查是否包含关键部分
            if any(keyword in clean_name for keyword in ["CCTV", "卫视", "TV"]):
                for v in variants:
                    if any(keyword in clean_name for keyword in ["CCTV", "卫视"]):
                        return standard_name
    
    return clean_name

def categorize_channel(channel_name):
    """将频道分类"""
    for category, channels in CHANNEL_CATEGORIES.items():
        if channel_name in channels:
            return category
    return "其他频道"

def get_channel_logo(channel_name, logo_dict):
    """获取频道图标URL"""
    # 直接匹配
    if channel_name in logo_dict:
        return logo_dict[channel_name]
    
    # 尝试清理后匹配
    clean_name = remove_special_symbols(channel_name)
    for logo_channel, logo_url in logo_dict.items():
        if clean_name == remove_special_symbols(logo_channel):
            return logo_url
    
    return ""

def collect_all_channels():
    """收集所有IP文件中的频道信息"""
    all_channels = {}
    logo_dict = load_channel_logos()
    
    print("📺 开始收集所有频道信息...")
    
    for filename in os.listdir(IP_DIR):
        if filename.endswith('.txt') and filename != "ip_summary.txt":
            filepath = os.path.join(IP_DIR, filename)
            
            # 读取IP文件
            existing_ips = read_existing_ips(filepath)
            
            for ip_port, (days, isp) in existing_ips.items():
                if days > 0:  # 只处理存活的IP
                    try:
                        # 测试IP可用性并获取频道信息
                        is_available, json_data = test_ip_availability(ip_port)
                        if is_available and json_data:
                            for channel in json_data.get("data", []):
                                raw_name = channel.get("name", "")
                                if raw_name:
                                    # 映射到标准名称
                                    std_name = map_channel_name(raw_name)
                                    # 分类
                                    category = categorize_channel(std_name)
                                    # 获取图标
                                    logo = get_channel_logo(std_name, logo_dict)
                                    
                                    # 构建播放URL
                                    url = channel.get("url", "")
                                    if url:
                                        if url.startswith("/"):
                                            play_url = f"http://{ip_port}{url}"
                                        else:
                                            play_url = f"http://{ip_port}/{url}"
                                        
                                        # 添加到频道列表
                                        channel_key = f"{std_name}|{play_url}"
                                        if channel_key not in all_channels:
                                            all_channels[channel_key] = {
                                                "name": std_name,
                                                "url": play_url,
                                                "logo": logo,
                                                "category": category,
                                                "ip": ip_port
                                            }
                    except Exception as e:
                        print(f"❌ 处理IP {ip_port} 的频道信息失败: {e}")
    
    print(f"✅ 共收集到 {len(all_channels)} 个频道")
    return all_channels

def generate_iptv_txt(channels_dict):
    """生成IPTV.txt文件"""
    output_file = os.path.join(CHANNEL_DIR, "IPTV.txt")
    
    # 按分类组织频道
    categorized_channels = {}
    for channel_info in channels_dict.values():
        category = channel_info["category"]
        categorized_channels.setdefault(category, []).append(channel_info)
    
    # 按分类顺序排序
    sorted_categories = []
    for cat in CHANNEL_CATEGORIES.keys():
        if cat in categorized_channels:
            sorted_categories.append(cat)
    
    # 添加其他频道
    if "其他频道" in categorized_channels:
        sorted_categories.append("其他频道")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # 文件头
            update_time = datetime.now().strftime('%Y/%m/%d %H:%M')
            f.write(f"{update_time},#genre#\n")
            
            # 按分类写入频道
            for category in sorted_categories:
                f.write(f"{category},#genre#\n")
                channels = categorized_channels[category]
                # 按频道名称排序
                channels.sort(key=lambda x: x["name"])
                
                for channel in channels:
                    f.write(f"{channel['name']},{channel['url']}\n")
                
                f.write("\n")
        
        print(f"💾 已生成IPTV.txt，共 {len(channels_dict)} 个频道，{len(sorted_categories)} 个分类")
        return True
        
    except Exception as e:
        print(f"❌ 生成IPTV.txt失败: {e}")
        return False

def generate_iptv_m3u(channels_dict):
    """生成IPTV.m3u文件"""
    output_file = os.path.join(CHANNEL_DIR, "IPTV.m3u")
    
    # 按分类组织频道
    categorized_channels = {}
    for channel_info in channels_dict.values():
        category = channel_info["category"]
        categorized_channels.setdefault(category, []).append(channel_info)
    
    # 按分类顺序排序
    sorted_categories = []
    for cat in CHANNEL_CATEGORIES.keys():
        if cat in categorized_channels:
            sorted_categories.append(cat)
    
    # 添加其他频道
    if "其他频道" in categorized_channels:
        sorted_categories.append("其他频道")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # M3U文件头
            f.write("#EXTM3U\n")
            f.write('x-tvg-url=""\n')
            
            # 按分类写入频道
            for category in sorted_categories:
                channels = categorized_channels[category]
                # 按频道名称排序
                channels.sort(key=lambda x: x["name"])
                
                for channel in channels:
                    # EXTINF行
                    logo_info = f' tvg-logo="{channel["logo"]}"' if channel["logo"] else ""
                    f.write(f'#EXTINF:-1 tvg-name="{channel["name"]}"{logo_info} group-title="{category}",{channel["name"]}\n')
                    # URL行
                    f.write(f'{channel["url"]}\n')
        
        print(f"💾 已生成IPTV.m3u，共 {len(channels_dict)} 个频道，{len(sorted_categories)} 个分类")
        return True
        
    except Exception as e:
        print(f"❌ 生成IPTV.m3u失败: {e}")
        return False

def generate_channel_files():
    """生成频道文件（IPTV.txt和IPTV.m3u）"""
    print("🎬 开始生成频道文件...")
    
    # 收集所有频道信息
    all_channels = collect_all_channels()
    
    if not all_channels:
        print("❌ 没有找到可用的频道")
        return False
    
    # 生成TXT文件
    txt_success = generate_iptv_txt(all_channels)
    
    # 生成M3U文件
    m3u_success = generate_iptv_m3u(all_channels)
    
    if txt_success and m3u_success:
        print("✅ 频道文件生成完成！")
        return True
    else:
        print("❌ 频道文件生成失败")
        return False

# ===============================
# 主函数
# ===============================

def main():
    """主函数"""
    print("=" * 60)
    print("🌐 FOFA IP地址抓取与验证工具")
    print(f"📁 IP目录: {IP_DIR}")
    print(f"📺 频道目录: {CHANNEL_DIR}")
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
        print("💡 可能的原因：")
        print("  1. Cookie已过期")
        print("  2. FOFA访问限制")
        print("  3. 网络连接问题")
        print("  4. 将使用现有IP文件生成频道")
    
    # 第三阶段：生成频道文件
    print("\n📺 开始生成频道文件...")
    generate_channel_files()
    
    print("\n" + "=" * 60)
    print("🎉 任务完成！")
    print("=" * 60)

if __name__ == "__main__":
    # 安装依赖: pip install eventlet
    main()
