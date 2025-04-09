#!/bin/bash

# 配置參數（請根據實際環境修改）
RU_IP="192.168.8.77"
RU_USER="user"
RU_PASSWORD="user"
RU_ENABLE_PASSWORD="liteon168"
GNB_SERVER="R750-OAI-BBU/CUDU"
CONTROL_PC_IP="192.168.8.118"  # Control PC 的 IP
CONTROL_PC_USER="sshuser"
CONTROL_PC_PASSWORD="bmwlab"
SERVER_IP="192.168.70.135"  # iPerf3 伺服器 IP
ADB_DEVICE="0123456789ABCDEF"  # ADB 設備序列號
TEST_DURATION=15  # 每個測試持續時間（秒）
WAIT_AFTER_REBOOT=60  # RU 重啟後等待時間（秒）
WAIT_AFTER_GNB=60  # gNB 啟動後等待時間（秒）
OUTPUT_DIR="test_results_$(date +%Y%m%d_%H%M%S)"
CSV_FILE="$OUTPUT_DIR/results.csv"
LOG_FILE="$OUTPUT_DIR/test.log"

# 確保 expect 已安裝
if ! command -v expect &> /dev/null; then
    echo "Error: expect is not installed. Please install it (e.g., sudo apt install expect)" >&2
    exit 1
fi

# 創建輸出目錄
mkdir -p "$OUTPUT_DIR"
echo "Test started at $(date)" > "$LOG_FILE"

# 函數：檢查命令是否成功
check_status() {
    if [ $? -ne 0 ]; then
        echo "Error: $1 failed. Check $LOG_FILE for details." >&2
        exit 1
    fi
}

# 函數：SSH 到 RU 並設定帶寬
set_ru_bandwidth() {
    local bw=$1
    echo "Setting RU bandwidth to $bw bps..." | tee -a "$LOG_FILE"
    cat << EOF > "$OUTPUT_DIR/set_bandwidth.exp"
#!/usr/bin/expect
set timeout 60
spawn ssh $RU_USER@$RU_IP
expect "password:"
send "$RU_PASSWORD\r"
expect "#"
send "enable\r"
expect "Password:"
send "$RU_ENABLE_PASSWORD\r"
expect "#"
send "configure terminal\r"
expect "#"
send "bandwidth $bw\r"
send "exit\r"
expect "#"
send "show running-config\r"
expect "#"
send "reboot\r"
expect eof
EOF
    chmod +x "$OUTPUT_DIR/set_bandwidth.exp"
    expect "$OUTPUT_DIR/set_bandwidth.exp" >> "$LOG_FILE" 2>&1
    check_status "SSH to RU and set bandwidth"
    echo "Waiting $WAIT_AFTER_REBOOT seconds for RU to reboot..." | tee -a "$LOG_FILE"
    sleep $WAIT_AFTER_REBOOT
}

# 函數：SSH 到 gNB 並啟動服務
start_gnb() {
    local mode=$1
    echo "Starting gNB in $mode mode..." | tee -a "$LOG_FILE"
    if [ "$mode" == "nFAPI" ]; then
        ssh $GNB_SERVER "cd ~/FH_7.2_dev/openairinterface5g/cmake_targets/ran_build/build && sudo NFAPI_TRACE_LEVEL=info ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb-vnf.sa.band78.273prb.nfapi.conf --nfapi VNF &" >> "$LOG_FILE" 2>&1
        sleep 5  # 確保 VNF 先啟動
        ssh $GNB_SERVER "cd ~/FH_7.2_dev/openairinterface5g/cmake_targets/ran_build/build && sudo NFAPI_TRACE_LEVEL=info ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb-pnf.band78.fhi72.4x4-liteon_new.conf --nfapi PNF --reorder-thread-disable 1 --thread-pool 1,3,5,7,9,11,13,15 &" >> "$LOG_FILE" 2>&1
    else  # FAPI
        ssh $GNB_SERVER "cd ~/FH_7.2_dev/openairinterface5g/cmake_targets/ran_build/build && sudo ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb.sa.band78.273prb.fhi72.4x4-liteon_new.conf --thread-pool 1,3,5,7,9,11,13,15 &" >> "$LOG_FILE" 2>&1
    fi
    check_status "Start gNB in $mode mode"
    echo "Waiting $WAIT_AFTER_GNB seconds for gNB to initialize..." | tee -a "$LOG_FILE"
    sleep $WAIT_AFTER_GNB
}

# 函數：控制 UE 飛航模式
toggle_airplane_mode() {
    local state=$1
    echo "Setting airplane mode to $state..." | tee -a "$LOG_FILE"
    if [ "$state" == "off" ]; then
        adb -s $ADB_DEVICE shell settings put global airplane_mode_on 0 >> "$LOG_FILE" 2>&1
        adb -s $ADB_DEVICE shell am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false >> "$LOG_FILE" 2>&1
    else
        adb -s $ADB_DEVICE shell settings put global airplane_mode_on 1 >> "$LOG_FILE" 2>&1
        adb -s $ADB_DEVICE shell am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true >> "$LOG_FILE" 2>&1
    fi
    check_status "Toggle airplane mode to $state"
    sleep 5  # 等待網絡穩定
}

# 函數：獲取 UE IP
get_ue_ip() {
    echo "Fetching UE IP..." | tee -a "$LOG_FILE"
    UE_IP=$(adb -s $ADB_DEVICE shell ip -f inet addr show ccmni0 | grep inet | awk '{print $2}' | cut -d/ -f1)
    if [ -z "$UE_IP" ]; then
        UE_IP=$(adb -s $ADB_DEVICE shell ip -f inet addr show ccmni1 | grep inet | awk '{print $2}' | cut -d/ -f1)
    fi
    if [ -z "$UE_IP" ]; then
        echo "Error: Unable to fetch UE IP." >&2
        exit 1
    fi
    echo "UE IP: $UE_IP" | tee -a "$LOG_FILE"
}

# 函數：運行測試並收集數據
run_test() {
    local bw=$1
    local protocol=$2
    local direction=$3
    local settings=$4
    local test_id="${bw}_${protocol}_${direction}_${settings// /_}"
    local iperf_log="$OUTPUT_DIR/iperf_${test_id}.log"
    local ping_log="$OUTPUT_DIR/ping_${test_id}.log"

    echo "Running test: Bandwidth=$bw, Protocol=$protocol, Direction=$direction, Settings=$settings" | tee -a "$LOG_FILE"

    # 構建 iPerf3 命令
    local iperf_cmd="/data/local/tmp/iperf3 -c $SERVER_IP -t $TEST_DURATION -B $UE_IP"
    if [ "$protocol" == "UDP" ]; then
        iperf_cmd="$iperf_cmd -u"
    fi
    if [ "$direction" == "DL" ]; then
        iperf_cmd="$iperf_cmd -R"
    fi
    iperf_cmd="$iperf_cmd $settings"

    # 啟動 ping
    ping $UE_IP > "$ping_log" 2>&1 &
    ping_pid=$!

    # 運行 iPerf3
    adb -s $ADB_DEVICE shell "$iperf_cmd" > "$iperf_log" 2>&1
    check_status "iPerf3 test for $test_id"

    # 停止 ping
    kill $ping_pid
    sleep 1  # 確保 ping 日誌寫入完成

    # 提取數據
    throughput=$(grep "sender" "$iperf_log" | tail -n 1 | awk '{print $7}' | grep -o '[0-9.]*')
    if [ -z "$throughput" ]; then
        throughput=$(grep "receiver" "$iperf_log" | tail -n 1 | awk '{print $7}' | grep -o '[0-9.]*')
    fi
    rtt=$(tail -n 1 "$ping_log" | grep -o "rtt min/avg/max/mdev = [0-9./]*" | awk '{print $4}' | cut -d/ -f2)

    # 檢查數據是否有效
    if [ -z "$throughput" ] || [ -z "$rtt" ]; then
        echo "Warning: Invalid data for $test_id. Throughput=$throughput, RTT=$rtt" | tee -a "$LOG_FILE"
        return
    fi

    # 寫入 CSV
    echo "$test_id,$bw,$protocol,$direction,$settings,$throughput,$rtt" >> "$CSV_FILE"
    echo "Test $test_id completed: Throughput=$throughput Mbps, RTT=$rtt ms" | tee -a "$LOG_FILE"
}

# 初始化 CSV 文件
echo "Test_ID,Bandwidth,Protocol,Direction,Settings,Throughput,RTT" > "$CSV_FILE"

# 主流程
for bw in 40000000 100000000; do
    # 設定 RU 帶寬並重啟
    set_ru_bandwidth $bw

    # 啟動 gNB（這裡使用 nFAPI，可根據需要切換為 FAPI）
    start_gnb "nFAPI"

    # 關閉飛航模式並獲取 UE IP
    toggle_airplane_mode "off"
    get_ue_ip

    # 測試組合
    run_test $bw "TCP" "DL" ""  # TCP 下行全速
    run_test $bw "TCP" "UL" ""  # TCP 上行全速
    run_test $bw "UDP" "DL" "-l 256 -b 1G"  # UDP 下行小封包低帶寬
    run_test $bw "UDP" "DL" "-l 1470 -b 1G"  # UDP 下行大封包低帶寬
    run_test $bw "UDP" "UL" "-l 256 -b 1G"  # UDP 上行小封包低帶寬
    run_test $bw "UDP" "UL" "-l 1470 -b 1G"  # UDP 上行大封包低帶寬

    # 測試完成後開啟飛航模式
    toggle_airplane_mode "on"
done

# 生成圖表和 Markdown 文件
echo "Generating plot and Markdown report..." | tee -a "$LOG_FILE"
cat << EOF > "$OUTPUT_DIR/generate_plot.py"
import matplotlib.pyplot as plt
import pandas as pd
data = pd.read_csv("$CSV_FILE")
plt.figure(figsize=(10, 6))
for protocol in data['Protocol'].unique():
    for direction in data['Direction'].unique():
        subset = data[(data['Protocol'] == protocol) & (data['Direction'] == direction)]
        plt.scatter(subset['Throughput'], subset['RTT'], label=f"{protocol} {direction}")
plt.xlabel('Throughput (Mbps)')
plt.ylabel('RTT (ms)')
plt.title('Throughput vs RTT')
plt.legend()
plt.grid(True)
plt.savefig("$OUTPUT_DIR/scatter_plot.png")
plt.close()
EOF

python3 "$OUTPUT_DIR/generate_plot.py" >> "$LOG_FILE" 2>&1
check_status "Generate plot"

cat << EOF > "$OUTPUT_DIR/report.md"
# Network Test Report
Generated on: $(date)

## Test Results
![Scatter Plot]($OUTPUT_DIR/scatter_plot.png)

## Data
$(cat "$CSV_FILE" | column -t -s,)
EOF

echo "Test completed at $(date). Results saved in $OUTPUT_DIR" | tee -a "$LOG_FILE"
