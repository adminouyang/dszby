pwd
if [ $# -eq 0 ]; then
  echo "开始测试······"
  echo "在5秒内输入1~5可选择城市"
  echo "1.广东电信"
  echo "2.北京联通"
  echo "3.湖南电信"
  echo "4.广东联通"
  echo "5.安徽电信"
  read -t 6 -p "超时未输入,将按默认设置测试" city_choice

  if [ -z "$city_choice" ]; then
      echo "未检测到输入,默认测试全部"
      city_choice=0
  fi

else
  city_choice=$1
fi
# 设置城市和相应的stream
case $city_choice in
    1)
        city="广东电信"
        stream="udp/239.77.1.19:5146"
        channel_key="广东电信"
        url_fofa="https://fofa.info/result?qbase64=InVkcHh5IiAmJiByZWdpb249Ikd1YW5nZG9uZyIgJiYgb3JnPSJDaGluYW5ldCIgJiYgcHJvdG9jb2w9Imh0dHAi&page=1&page_size=20"
        ;;
    2)
        city="北京联通"
        stream="rtp/239.3.1.241:8000"
        channel_key="北京联通"
        url_fofa="https://fofa.info/result?qbase64=InVkcHh5IiAmJiByZWdpb249IkJlaWppbmciICYmIG9yZz0iQ0hJTkEgVU5JQ09NIENoaW5hMTY5IEJhY2tib25lIiAmJiBwcm90b2NvbD0iaHR0cCI%3D&page=1&page_size=10"
        ;;
    3)
        city="湖南电信"
        stream="udp/239.76.246.101:1234"
        channel_key="湖南电信"
	url_fofa="https://fofa.info/result?qbase64=InVkcHh5IiAmJiByZWdpb249Ikh1bmFuIiAmJiBvcmc9IkNoaW5hbmV0IiAmJiBwcm90b2NvbD0iaHR0cCI%3D&page=1&page_size=10"
        ;;
    4)
        city="广东联通"
        stream="udp/239.0.1.1:5001"
        channel_key="广东联通"
        url_fofa="https://fofa.info/result?qbase64=InVkcHh5IiAmJiByZWdpb249Ikd1YW5nZG9uZyIgJiYgb3JnPSJDSElOQSBVTklDT00gQ2hpbmExNjkgQmFja2JvbmUiICYmIHByb3RvY29sPSJodHRwIg%3D%3D&page=1&page_size=20"
        ;;
    5)
        city="安徽电信"
        stream="rtp/238.1.79.27:4328"
        channel_key="安徽电信"
	url_fofa="https://fofa.info/result?qbase64=InVkcHh5IiAmJiByZWdpb249IkFuaHVpIiAmJiBvcmc9IkNoaW5hbmV0IiAmJiBwcm90b2NvbD0iaHR0cCI%3D&page=1&page_size=20"
        ;;	
    6)
        city="Zhejiang_120"
        stream="udp/233.50.201.63:5140"
        channel_key="浙江电信"
        ;;	
    7)
        city="Jiangsu"
        stream="udp/239.49.8.19:9614"
        channel_key="江苏电信"
	;;
    8)
        city="Shanghai_103"
        stream="udp/239.45.1.42:5140"
	channel_key="上海电信"
	;;
    9)
        city="Hubei_90"
        stream="rtp/239.69.1.249:11136"
        channel_key="湖北电信"
	;;
    0)
        # 逐个处理{ }内每个选项
        for option in {1..9}; do
          bash "$0" $option  # 假定fofa.sh是当前脚本的文件名，$option将递归调用
        done
        exit 0
        ;;
esac

# 使用城市名作为默认文件名，格式为 CityName.ip
time=$(date +%m%d%H%M)
ipfile=py/iptv源收集检测/主频道/专享频道/py/组播/ip/${city}_ip.txt
good_ip=py/iptv源收集检测/主频道/专享频道/py/组播/ip/good_${city}_ip.txt
result_ip=py/iptv源收集检测/主频道/专享频道/py/组播/ip/result_${city}_ip.txt
echo "======== 开始检索 ${city} ========"
echo "从 fofa 获取ip+端口"
curl -o test.html $url_fofa
grep -E '^\s*[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+$' test.html | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+' > tmp_ipfile
echo "从 '${ipfile}' 读取ip并添加到检测列表"
cat $ipfile >> tmp_ipfile
sort tmp_ipfile | uniq | sed '/^\s*$/d' > $ipfile
rm -f tmp_ipfile test.html

while IFS= read -r ip; do
    # 尝试连接 IP 地址和端口号，并将输出保存到变量中
    tmp_ip=$(echo -n "$ip" | sed 's/:/ /')
    output=$(nc -w 1 -v -z $tmp_ip 2>&1)
    # 如果连接成功，且输出包含 "succeeded"，则将结果保存到输出文件中
    if [[ $output == *"succeeded"* ]]; then
        # 使用 awk 提取 IP 地址和端口号对应的字符串，并保存到输出文件中
        echo "$output" | grep "succeeded" | awk -v ip="$ip" '{print ip}' >> $good_ip
    fi
done < $ipfile
lines=$(wc -l < $good_ip)
echo "连接成功 $lines 个,开始测速······"

i=0
while read line; do
    i=$((i + 1))
    ip=$line
    url="http://$ip/$stream"
    #echo $url
    curl $url --connect-timeout 3 --max-time 60 -o /dev/null >zubo.tmp 2>&1
    a=$(head -n 3 zubo.tmp | awk '{print $NF}' | tail -n 1)  
    echo "第$i/$lines个：$ip    $a"
    echo "$ip    $a" >> speedtest_${city}_$time.log
done < $good_ip
rm -f zubo.tmp $ipfile $good_ip

echo "测速结果排序"
awk '/M|k/{print $2"  "$1}' speedtest_${city}_$time.log | sort -n -r > $result_ip
awk '/M|k/{print $2}' $result_ip > $ipfile
cat $result_ip
ip1=$(awk 'NR==1{print $2}' $result_ip)
ip2=$(awk 'NR==2{print $2}' $result_ip)
ip3=$(awk 'NR==3{print $2}' $result_ip)
rm -f speedtest_${city}_$time.log     
# 用 3 个最快 ip 生成对应城市的 txt 文件
program=py/iptv源收集检测/主频道/专享频道/py/组播/template/template_${city}.txt
sed "s/ipipip/$ip1/g" $program > tmp_1.txt
sed "s/ipipip/$ip2/g" $program > tmp_2.txt
sed "s/ipipip/$ip3/g" $program > tmp_3.txt
echo "${city}-组播1,#genre#" > tmp_all.txt
cat tmp_1.txt >> tmp_all.txt
echo "${city}-组播2,#genre#" >> tmp_all.txt
cat tmp_2.txt >> tmp_all.txt
echo "${city}-组播3,#genre#" >> tmp_all.txt
cat tmp_3.txt >> tmp_all.txt
grep -vE '/{3}' tmp_all.txt > "py/iptv源收集检测/主频道/专享频道/py/组播/txt/${city}.txt"
rm -f tmp_1.txt tmp_2.txt tmp_3.txt tmp_all.txt
echo "${city} 测试完成，生成可用文件：'txt/${city}.txt'"
#--------合并所有城市的txt文件---------
