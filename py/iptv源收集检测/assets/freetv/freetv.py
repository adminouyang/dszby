import urllib.request
import ssl
from urllib.parse import urlparse
from datetime import datetime, timedelta, timezone
import concurrent.futures
import time

# 定义
freetv_lines = []

# 速度测试相关全局变量
SPEED_THRESHOLD = 300  # 300KB/s
CHECK_TIMEOUT = 5  # 超时时间（秒）
MAX_WORKERS = 20  # 最大并发线程数
DEEP_SPEED_GROUPS = ['freetv', 'freetv_cctv', 'freetv_ws', 'freetv_other']  # 需要深度测速的组
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

# 禁用SSL警告
ssl._create_default_https_context = ssl._create_unverified_context

# 存储测速结果
speed_results = {}

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
    
# 组织过滤后的freetv
def process_channel_line(line):
    if "#genre#" not in line and "," in line and "://" in line:
        channel_name, channel_address = line.split(',', 1)
        freetv_lines.append(f"{channel_name},{channel_address}".strip())

def get_speed_score(url, group_name):
    """深度测速逻辑 - 使用urllib替代requests"""
    is_deep = group_name in DEEP_SPEED_GROUPS
    
    try:
        start_time = time.time()
        
        # 创建请求对象
        req = urllib.request.Request(url, headers=HEADERS)
        
        # 打开URL连接
        response = urllib.request.urlopen(req, timeout=CHECK_TIMEOUT)
        
        ttfb = time.time() - start_time
        ttfb_ms = ttfb * 1000  # 转换为毫秒
        
        if is_deep:
            downloaded = 0
            test_start = time.time()
            
            # 读取数据块直到达到1MB或超时
            while downloaded < 1024 * 1024 and (time.time() - test_start) <= 1.2:
                chunk = response.read(1024 * 64)  # 读取64KB块
                if not chunk:
                    break
                downloaded += len(chunk)
            
            duration = time.time() - test_start
            
            if duration <= 0:
                return 0.0
            
            # 计算速度 (KB/s)
            speed = (downloaded / 1024) / (duration + 0.001)
            
            # 打印详细测速信息
            print(f"  ✓ {url[:50]:<50} | TTFB: {ttfb_ms:5.1f}ms | 下载: {downloaded/1024:6.1f}KB | 耗时: {duration:4.2f}s | 速度: {speed:7.1f}KB/s")
            return speed
        else:
            # 对于非深度测速，返回一个基于TTFB的分数
            speed = 1000.0 / (ttfb + 0.001)  # 转换为速度近似值
            print(f"  ✓ {url[:50]:<50} | TTFB: {ttfb_ms:5.1f}ms | 速度: {speed:7.1f}KB/s")
            return speed
            
    except urllib.error.URLError as e:
        print(f"  ✗ {url[:50]:<50} | 连接错误: {e.reason}")
        return 0.0
    except Exception as e:
        print(f"  ✗ {url[:50]:<50} | 测速失败: {str(e)[:30]}")
        return 0.0

# 批量速度测试函数
def batch_speed_test(channel_list, group_name="freetv"):
    """批量测试频道速度"""
    print(f"开始对 {len(channel_list)} 个频道进行速度测试...")
    print("-" * 100)
    
    fast_channels = []
    total_channels = len(channel_list)
    
    def test_single_channel(channel_info):
        """测试单个频道"""
        try:
            channel_name, channel_url = channel_info
            
            # 打印当前测试的频道名称
            print(f"测试: {channel_name[:30]:<30} | {channel_url[:50]:<50}")
            
            # 进行测速
            speed = get_speed_score(channel_url, group_name)
            
            # 记录结果
            speed_results[channel_name] = speed
            
            if speed >= SPEED_THRESHOLD:
                # 记录通过的频道
                result_str = f"  ✅ 通过 | 速度: {speed:7.1f}KB/s"
                print(result_str)
                return channel_info, speed, True
            else:
                result_str = f"  ❌ 失败 | 速度: {speed:7.1f}KB/s"
                print(result_str)
                return channel_info, speed, False
        except Exception as e:
            print(f"  ⚠ 异常: {str(e)[:30]}")
            speed_results[channel_name] = 0
            return channel_info, 0, False
    
    # 使用线程池进行并发测试
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 提交所有测试任务
        future_to_channel = {executor.submit(test_single_channel, channel_info): channel_info 
                           for channel_info in channel_list}
        
        # 处理完成的任务
        completed = 0
        for future in concurrent.futures.as_completed(future_to_channel):
            completed += 1
            try:
                channel_info, speed, passed = future.result()
                channel_name, channel_url = channel_info
                
                if passed:
                    # 保存通过的频道
                    fast_channels.append(f"{channel_name},{channel_url}")
                
                # 每完成10个或全部完成时显示总进度
                if completed % 10 == 0 or completed == total_channels:
                    print(f"\n进度: {completed}/{total_channels} 个频道已完成测试，通过: {len(fast_channels)} 个")
                    print("-" * 100)
                    
            except Exception as e:
                print(f"\n测试出错: {e}")
    
    print("\n" + "=" * 100)
    print(f"速度测试完成!")
    print(f"总计测试: {total_channels} 个频道")
    print(f"通过测试: {len(fast_channels)} 个 (速度 ≥ {SPEED_THRESHOLD} KB/s)")
    print(f"通过率: {(len(fast_channels)/total_channels*100 if total_channels > 0 else 0):.1f}%")
    print("=" * 100)
    
    return fast_channels

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

            # 逐行处理内容
            lines = text.split('\n')
            print(f"从URL获取到 {len(lines)} 行数据")
            
            for line in lines:
                line = line.strip()
                if "#genre#" not in line and "," in line and "://" in line:
                    # 拆分成频道名和URL部分
                    try:
                        channel_name, channel_address = line.split(',', 1)
                        # 检查是否在字典中
                        if channel_name in freetv_dictionary:
                            process_channel_line(line)
                    except ValueError:
                        continue  # 跳过格式错误的行
                        
            print(f"处理后得到 {len(freetv_lines)} 个有效频道")

    except Exception as e:
        print(f"处理URL时发生错误：{e}")

#读取文本
freetv_dictionary = read_txt_to_array('py/iptv源收集检测/assets/freetv/freetvlist.txt')  #all
freetv_dictionary_cctv = read_txt_to_array('py/iptv源收集检测/assets/freetv/freetvlist_cctv.txt')   #二次分发cctv，单独存
freetv_dictionary_ws = read_txt_to_array('py/iptv源收集检测/assets/freetv/freetvlist_ws.txt')   #二次分发卫视，单独存

# 初始化分类列表
freetv_cctv_lines = []
freetv_ws_lines = []
freetv_other_lines = []

# 定义
urls = ["https://freetv.fun/test_channels_original_new.txt"]

# 处理URL获取频道
for url in urls:
    print(f"处理URL: {url}")
    process_url(url)

# 检查是否获取到频道
if not freetv_lines:
    print("错误: 没有获取到任何频道，请检查网络连接或URL")
    exit(1)

print(f"成功获取 {len(freetv_lines)} 个频道")

# 获取当前的 UTC 时间
utc_time = datetime.now(timezone.utc)
# 北京时间
beijing_time = utc_time + timedelta(hours=8)
# 格式化为所需的格式
formatted_time = beijing_time.strftime("%Y%m%d %H:%M:%S")

# 重命名频道
freetv_lines_renamed = rename_channel(rename_dic, freetv_lines)
print(f"重命名后频道数: {len(freetv_lines_renamed)}")

# 准备速度测试的频道列表
channels_to_test = []
for line in freetv_lines_renamed:
    if "#genre#" not in line and "," in line and "://" in line:
        try:
            channel_name, channel_address = line.split(',', 1)
            # 确保URL格式正确
            if channel_address.startswith(('http://', 'https://')):
                channels_to_test.append((channel_name, channel_address))
        except:
            continue

print(f"准备对 {len(channels_to_test)} 个频道进行速度测试...")

# 进行速度测试
if channels_to_test:
    fast_channels = batch_speed_test(channels_to_test, "freetv")
    
    # 生成通过测速的频道列表
    version = f"更新时间,{formatted_time}"
    output_lines = ["#genre#"] + [version] + [''] + \
                   ["freetv,#genre#"] + sorted(set(fast_channels))
else:
    print("错误: 没有需要测试的频道")
    output_lines = ["#genre#"]

# 将合并后的文本写入文件：全集
output_file = "py/iptv源收集检测/assets/freetv/freetv_output.txt"
try:
    with open(output_file, 'w', encoding='utf-8') as f:
        for line in output_lines:
            f.write(line + '\n')
    print(f"已保存到文件: {output_file}")
    
    # 保存速度统计信息
    if speed_results:
        speed_stats_file = "py/iptv源收集检测/assets/freetv/freetv_speed_stats.txt"
        with open(speed_stats_file, 'w', encoding='utf-8') as f:
            f.write(f"速度测试统计 - 阈值: {SPEED_THRESHOLD} KB/s\n")
            f.write(f"测试时间: {formatted_time}\n")
            f.write(f"总频道数: {len(channels_to_test)}\n")
            f.write(f"通过测试数: {len(fast_channels)}\n")
            f.write(f"通过率: {(len(fast_channels)/len(channels_to_test)*100 if channels_to_test else 0):.2f}%\n\n")
            
            # 按速度排序
            sorted_speeds = sorted(speed_results.items(), key=lambda x: x[1], reverse=True)
            f.write("频道速度排名 (前100名):\n")
            for i, (name, speed) in enumerate(sorted_speeds[:100], 1):
                status = "✓" if speed >= SPEED_THRESHOLD else "✗"
                f.write(f"{i:3d}. [{status}] {name}: {speed:.2f} KB/s\n")
            
            # 添加详细的速度统计
            f.write(f"\n详细速度统计:\n")
            f.write(f"- 平均速度: {sum(speed_results.values())/len(speed_results):.2f} KB/s\n")
            
            # 统计不同速度区间的频道数量
            speed_ranges = [
                (0, 100, "0-100 KB/s"),
                (100, 300, "100-300 KB/s"),
                (300, 1000, "300-1000 KB/s"),
                (1000, float('inf'), "1000+ KB/s")
            ]
            
            for min_speed, max_speed, label in speed_ranges:
                count = len([s for s in speed_results.values() if min_speed <= s < max_speed])
                f.write(f"- {label}: {count} 个频道\n")
                
        print(f"速度统计已保存到: {speed_stats_file}")

except Exception as e:
    print(f"保存文件时发生错误：{e}")

# 对通过测速的频道进行分类
for line in fast_channels:
    if "#genre#" not in line and "," in line and "://" in line:
        try:
            channel_name = line.split(',')[0].strip()
            channel_address = line.split(',')[1].strip()
            
            if channel_name in freetv_dictionary_cctv:  # 央视频道
                freetv_cctv_lines.append(f"{channel_name},{channel_address}")
            elif channel_name in freetv_dictionary_ws:  # 卫视频道
                freetv_ws_lines.append(f"{channel_name},{channel_address}")
            else:
                freetv_other_lines.append(f"{channel_name},{channel_address}")
        except:
            continue

# 生成分类文件
version_line = f"更新时间,{formatted_time}"

# freetv_cctv
if freetv_cctv_lines:
    output_lines_cctv = ["#genre#"] + [version_line] + [''] + \
                       ["freetv_cctv,#genre#"] + sorted(set(freetv_cctv_lines))
else:
    output_lines_cctv = ["#genre#", version_line, '', "freetv_cctv,#genre#"]

# freetv_ws
if freetv_ws_lines:
    output_lines_ws = ["#genre#"] + [version_line] + [''] + \
                     ["freetv_ws,#genre#"] + sorted(set(freetv_ws_lines))
else:
    output_lines_ws = ["#genre#", version_line, '', "freetv_ws,#genre#"]

# freetv_other
if freetv_other_lines:
    output_lines_other = ["#genre#"] + [version_line] + [''] + \
                        ["freetv_other,#genre#"] + sorted(set(freetv_other_lines))
else:
    output_lines_other = ["#genre#", version_line, '', "freetv_other,#genre#"]

# 再次写入文件：分开
output_file_cctv = "py/iptv源收集检测/assets/freetv/freetv_output_cctv.txt"
output_file_ws = "py/iptv源收集检测/assets/freetv/freetv_output_ws.txt"
output_file_other = "py/iptv源收集检测/assets/freetv/freetv_output_other.txt"

try:
    with open(output_file_cctv, 'w', encoding='utf-8') as f:
        for line in output_lines_cctv:
            f.write(line + '\n')
    print(f"已保存CCTV频道到文件: {output_file_cctv}，共 {len(freetv_cctv_lines)} 个频道")

    with open(output_file_ws, 'w', encoding='utf-8') as f:
        for line in output_lines_ws:
            f.write(line + '\n')
    print(f"已保存卫视频道到文件: {output_file_ws}，共 {len(freetv_ws_lines)} 个频道")
    
    with open(output_file_other, 'w', encoding='utf-8') as f:
        for line in output_lines_other:
            f.write(line + '\n')
    print(f"已保存其他频道到文件: {output_file_other}，共 {len(freetv_other_lines)} 个频道")

except Exception as e:
    print(f"保存文件时发生错误：{e}")

print("\n" + "=" * 100)
print("=== 处理完成 ===")
print(f"总计获取频道: {len(freetv_lines)}")
print(f"通过测速的频道: {len(fast_channels)}")
print(f"CCTV频道: {len(freetv_cctv_lines)}")
print(f"卫视频道: {len(freetv_ws_lines)}")
print(f"其他频道: {len(freetv_other_lines)}")
print("=" * 100)
