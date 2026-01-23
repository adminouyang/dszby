import urllib.request
from urllib.parse import urlparse
import re
import os
from datetime import datetime, timedelta, timezone
import threading
import time
import socket
import concurrent.futures
from queue import Queue

# 定义
freetv_lines = []

# 速度测试相关全局变量
speed_threshold = 100  # 300KB/s
timeout = 5  # 超时时间（秒）
max_workers = 20  # 最大并发线程数
tested_channels = {}  # 存储已测试的频道速度
speed_test_lock = threading.Lock()

#读取修改频道名称方法
def load_modify_name(filename):
    corrections = {}
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split(',')
            correct_name = parts[0]
            for name in parts[1:]:
                corrections[name] = correct_name
    return corrections

#读取修改字典文件
rename_dic = load_modify_name('py/iptv源收集检测/assets/freetv/freetv_rename.txt')

#纠错频道名称
def rename_channel(corrections, data):
    corrected_data = []
    for line in data:
        name, url = line.split(',', 1)
        if name in corrections and name != corrections[name]:
            name = corrections[name]
        corrected_data.append(f"{name},{url}")
    return corrected_data

#读取文本方法
def read_txt_to_array(file_name):
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            lines = [line.strip() for line in lines]
            return lines
    except FileNotFoundError:
        print(f"File '{file_name}' not found.")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

# 速度测试函数
def test_channel_speed(channel_info):
    """测试单个频道的速度"""
    try:
        channel_name, channel_address = channel_info
        url = channel_address.split('$')[0]  # 获取URL部分
        
        # 解析URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme:
            return channel_info, 0
        
        # 设置socket超时
        socket.setdefaulttimeout(timeout)
        
        # 开始计时
        start_time = time.time()
        
        # 创建请求
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')
        req.add_header('Range', 'bytes=0-102399')  # 只下载前100KB用于测速
        
        # 打开URL
        with urllib.request.urlopen(req) as response:
            data = b''
            total_size = 0
            max_size = 102400  # 最多下载100KB用于测速
            
            while True:
                chunk = response.read(8192)
                if not chunk:
                    break
                data += chunk
                total_size += len(chunk)
                if total_size >= max_size:
                    break
        
        # 计算耗时
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        if elapsed_time <= 0:
            return channel_info, 0
            
        # 计算速度 (KB/s)
        speed = (total_size / 1024) / elapsed_time
        
        with speed_test_lock:
            tested_channels[channel_name] = speed
            
        return channel_info, speed
        
    except Exception as e:
        # 出错时返回0速度
        with speed_test_lock:
            tested_channels[channel_name] = 0
        return channel_info, 0

# 批量速度测试
def batch_speed_test(channels, max_workers=20):
    """批量测试频道速度"""
    print(f"开始速度测试，共 {len(channels)} 个频道，使用 {max_workers} 个线程...")
    
    # 创建频道队列
    channel_queue = Queue()
    for channel in channels:
        channel_queue.put(channel)
    
    # 使用线程池进行并发测试
    tested_count = 0
    fast_channels = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有测试任务
        future_to_channel = {executor.submit(test_channel_speed, channel): channel for channel in channels}
        
        # 处理完成的任务
        for future in concurrent.futures.as_completed(future_to_channel):
            tested_count += 1
            try:
                channel_info, speed = future.result()
                channel_name, channel_address = channel_info
                
                if speed >= speed_threshold:
                    fast_channels.append(f"{channel_name},{channel_address}")
                
                # 显示进度
                if tested_count % 10 == 0 or tested_count == len(channels):
                    print(f"进度: {tested_count}/{len(channels)} 个频道已完成测试")
                
            except Exception as e:
                print(f"测试出错: {e}")
    
    print(f"速度测试完成，共有 {len(fast_channels)} 个频道速度超过 {speed_threshold} KB/s")
    return fast_channels

# 组织过滤后的freetv
def process_channel_line(line):
    if  "#genre#" not in line and "," in line and "://" in line:
        channel_name, channel_address = line.split(',', 1)
        channel_address=channel_address+"$"+channel_name.strip().replace(' ', '_')
        line=channel_name+","+channel_address
        freetv_lines.append(line.strip())


def process_url(url):
    try:
        # 创建一个请求对象并添加自定义header
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')

        # 打开URL并读取内容
        with urllib.request.urlopen(req) as response:
            # 以二进制方式读取数据
            data = response.read()
            # 将二进制数据解码为字符串
            text = data.decode('utf-8')
            # channel_name=""
            # channel_address=""

            # 逐行处理内容
            lines = text.split('\n')
            print(f"行数: {len(lines)}")
            for line in lines:
                if  "#genre#" not in line and "," in line and "://" in line:
                    # 拆分成频道名和URL部分
                    channel_name, channel_address = line.split(',', 1)
                    
                    if channel_name in freetv_dictionary:
                        process_channel_line(line) 

    except Exception as e:
        print(f"处理URL时发生错误：{e}")



#读取文本
freetv_dictionary=read_txt_to_array('py/iptv源收集检测/assets/freetv/freetvlist.txt')  #all
freetv_dictionary_cctv=read_txt_to_array('py/iptv源收集检测/assets/freetv/freetvlist_cctv.txt')   #二次分发cctv，单独存
freetv_dictionary_ws=read_txt_to_array('py/iptv源收集检测/assets/freetv/freetvlist_ws.txt')   #二次分发卫视，单独存

freetv_cctv_lines = []
freetv_ws_lines = []
freetv_other_lines = []


# 定义
urls = ["https://freetv.fun/test_channels_original_new.txt"]

# 处理
for url in urls:
    print(f"处理URL: {url}")
    process_url(url)

# 获取当前的 UTC 时间
utc_time = datetime.now(timezone.utc)
# 北京时间
beijing_time = utc_time + timedelta(hours=8)
# 格式化为所需的格式
formatted_time = beijing_time.strftime("%Y%m%d %H:%M:%S")

# freetv_all
freetv_lines_renamed=rename_channel(rename_dic,freetv_lines)

# 准备速度测试
channels_to_test = []
for line in freetv_lines_renamed:
    if "#genre#" not in line and "," in line and "://" in line:
        try:
            channel_name, channel_address = line.split(',', 1)
            channels_to_test.append((channel_name, channel_address))
        except:
            pass

# 进行速度测试
if channels_to_test:
    print(f"开始对 {len(channels_to_test)} 个频道进行速度测试...")
    fast_channels = batch_speed_test(channels_to_test, max_workers)
    
    # 生成通过测速的频道列表
    version=formatted_time+",url"
    output_lines =  ["更新时间,#genre#"] +[version] + ['\n'] +\
                  ["freetv,#genre#"] + sorted(set(fast_channels))
else:
    print("没有需要测试的频道")
    output_lines = ["#genre#"]

# 将合并后的文本写入文件：全集
output_file = "py/iptv源收集检测/assets/freetv/freetv_output.txt"
try:
    with open(output_file, 'w', encoding='utf-8') as f:
        for line in output_lines:
            f.write(line + '\n')
    print(f"已保存到文件: {output_file}")
    
    # 保存速度统计信息
    speed_stats_file = "py/iptv源收集检测/assets/freetv/freetv_speed_stats.txt"
    with open(speed_stats_file, 'w', encoding='utf-8') as f:
        f.write(f"速度测试统计 - 阈值: {speed_threshold} KB/s\n")
        f.write(f"测试时间: {formatted_time}\n")
        f.write(f"总频道数: {len(channels_to_test)}\n")
        f.write(f"通过测试数: {len(fast_channels)}\n")
        f.write(f"通过率: {len(fast_channels)/len(channels_to_test)*100:.2f}%\n\n")
        
        # 按速度排序
        sorted_speeds = sorted(tested_channels.items(), key=lambda x: x[1], reverse=True)
        f.write("频道速度排名:\n")
        for i, (name, speed) in enumerate(sorted_speeds[:50], 1):  # 显示前50名
            f.write(f"{i:3d}. {name}: {speed:.2f} KB/s\n")
            
    print(f"速度统计已保存到: {speed_stats_file}")

except Exception as e:
    print(f"保存文件时发生错误：{e}")

# # # # # # # # # # # # # # # # # # # # # # # 分批再次保存
# $去掉
def clean_url(url):
    last_dollar_index = url.rfind('$')  # 安全起见找最后一个$处理
    if last_dollar_index != -1:
        return url[:last_dollar_index]
    return url

# 对通过测速的频道进行分类
for line in fast_channels:
    if  "#genre#" not in line and "," in line and "://" in line:
        channel_name=line.split(',')[0].strip()
        channel_address=clean_url(line.split(',')[1].strip())  #把URL中$之后的内容都去掉
        line=channel_name+","+channel_address #重新组织line

        if channel_name in freetv_dictionary_cctv: #央视频道
            freetv_cctv_lines.append(line.strip())
        elif channel_name in freetv_dictionary_ws: #卫视频道
            freetv_ws_lines.append(line.strip())
        else:
            freetv_other_lines.append(line.strip())

# freetv_cctv
output_lines_cctv =  ["更新时间,#genre#"] +[version] + ['\n'] +\
             ["freetv_cctv,#genre#"] + sorted(set(freetv_cctv_lines))
# freetv_ws
output_lines_ws =  ["更新时间,#genre#"] +[version] + ['\n'] +\
             ["freetv_ws,#genre#"] + sorted(set(freetv_ws_lines))
# freetv_other
output_lines_other =  ["更新时间,#genre#"] +[version] + ['\n'] +\
             ["freetv_other,#genre#"] + sorted(set(freetv_other_lines))

# 再次写入文件：分开
output_file_cctv = "py/iptv源收集检测/assets/freetv/freetv_output_cctv.txt"
output_file_ws = "py/iptv源收集检测/assets/freetv/freetv_output_ws.txt"
output_file_other = "py/iptv源收集检测/assets/freetv/freetv_output_other.txt"
try:
    with open(output_file_cctv, 'w', encoding='utf-8') as f:
        for line in output_lines_cctv:
            f.write(line + '\n')
    print(f"已保存到文件: {output_file_cctv}")

    with open(output_file_ws, 'w', encoding='utf-8') as f:
        for line in output_lines_ws:
            f.write(line + '\n')
    print(f"已保存到文件: {output_file_ws}")
    
    with open(output_file_other, 'w', encoding='utf-8') as f:
        for line in output_lines_other:
            f.write(line + '\n')
    print(f"已保存到文件: {output_file_other}")

except Exception as e:
    print(f"保存文件时发生错误：{e}")
