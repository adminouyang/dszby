ip_version_priority = "ipv6"

source_urls = [
    "https://ghproxy.cc/https://raw.githubusercontent.com/lalifeier/IPTV/refs/heads/main/txt/udpxy/天津.txt",  #联通
    "https://ghproxy.cc/https://raw.githubusercontent.com/lalifeier/IPTV/refs/heads/main/txt/udpxy/山西.txt",  #联通
    "https://ghproxy.cc/https://raw.githubusercontent.com/lalifeier/IPTV/refs/heads/main/txt/udpxy/黑龙江.txt",  #联通
    "https://ghproxy.cc/https://raw.githubusercontent.com/lalifeier/IPTV/refs/heads/main/txt/udpxy/重庆.txt",  #联通
    "https://ghproxy.cc/https://raw.githubusercontent.com/mlzlzj/iptv/refs/heads/main/iptv_list.txt",  #湖南电信
    "https://ghproxy.cc/https://raw.githubusercontent.com/adminouyang/231006/refs/heads/main/py/安徽组播/iptv_list.txt"  #电信

]

url_blacklist = [
    'tvgslb.hn.chinamobile.com:8089',
  
]
url_whitelist = [
    "rtp",
    "udp",
]

announcements = [
    # {
    #     "channel": "公告",
    #     "entries": [
    #         {"name": "请阅读", "url": "https://liuliuliu.tv/api/channels/1997/stream", "logo": "http://175.178.251.183:6689/LR.jpg"},
    #         {"name": "yuanzl77.github.io", "url": "https://liuliuliu.tv/api/channels/233/stream", "logo": "http://175.178.251.183:6689/LR.jpg"},
    #         {"name": "更新日期", "url": "https://gitlab.com/lr77/IPTV/-/raw/main/%E4%B8%BB%E8%A7%92.mp4", "logo": "http://175.178.251.183:6689/LR.jpg"},
    #         {"name": None, "url": "https://gitlab.com/lr77/IPTV/-/raw/main/%E8%B5%B7%E9%A3%8E%E4%BA%86.mp4", "logo": "http://175.178.251.183:6689/LR.jpg"}
    #     ]
    # }
]

epg_urls = [
    "https://live.fanmingming.com/e.xml",
    "http://epg.51zmt.top:8000/e.xml",
    "http://epg.aptvapp.com/xml",
    "https://epg.pw/xmltv/epg_CN.xml",
    "https://epg.pw/xmltv/epg_HK.xml",
    "https://epg.pw/xmltv/epg_TW.xml"
]
