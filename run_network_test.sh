#!/bin/bash

# 配置參數（請根據實際環境修改）
RU_IP="192.168.8.77"
RU_USER="user"
RU_PASSWORD="user"
RU_ENABLE_PASSWORD="liteon168"
GNB_SERVER_USER="oai72"
GNB_SERVER_HOST="192.168.8.43"
PASSWORD="bmwlab"
CN_SERVER="open5gs"
CONTROL_PC_IP="192.168.8.118"
CONTROL_PC_USER="sshuser"
CONTROL_PC_PASSWORD="bmwlab"
SERVER_IP="192.168.70.135"
ADB_DEVICE="0123456789ABCDEF"
TEST_DURATION=5
WAIT_AFTER_REBOOT=60
WAIT_AFTER_GNB=30
OUTPUT_DIR="test_results_$(date +%Y%m%d_%H%M%S)"
CSV_FILE="$OUTPUT_DIR/results.csv"
LOG_FILE="$OUTPUT_DIR/test.log"
VENV_DIR="$OUTPUT_DIR/venv"

# SSH 選項設定
SSH_OPTIONS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"

# 確保必要的工具都已安裝
for cmd in expect ssh sshpass python3; do
    if ! command -v $cmd &> /dev/null; then
        echo "Error: $cmd is not installed. Please install it first." >&2
        exit 1
    fi
done

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

# 函數：SSH 到 RU 並設定帶寬，並檢查配置後是否需要重啟
set_ru_bandwidth() {
    local bw=$1
    echo "Setting RU bandwidth to $bw bps..." | tee -a "$LOG_FILE"
    
    # Remove any previous output file
    rm -f "$OUTPUT_DIR/set_bandwidth.out"
    
    cat << 'EOF' > "$OUTPUT_DIR/set_bandwidth.exp"
#!/usr/bin/expect
log_file -a "$env(OUTPUT_DIR)/set_bandwidth.out"
set timeout 60
spawn ssh $env(RU_USER)@$env(RU_IP)
expect "password:"
send "$env(RU_PASSWORD)\r"
expect ">"
send "enable\r"
expect "Password:"
send "$env(RU_ENABLE_PASSWORD)\r"
expect "#"
send "configure terminal\r"
expect "(config)#"
send "bandwidth $env(bw)\r"
expect "(config)#"
send "exit\r"
expect "#"
send "show running-config\r"
expect "#"
send "exit\r"
expect ">"
send "exit\r"
expect eof
EOF

    chmod +x "$OUTPUT_DIR/set_bandwidth.exp"
    
    # Export needed variables for expect
    export RU_USER RU_IP RU_PASSWORD RU_ENABLE_PASSWORD OUTPUT_DIR bw=$bw

    expect "$OUTPUT_DIR/set_bandwidth.exp" >> "$LOG_FILE" 2>&1
    check_status "SSH to RU and set bandwidth"
    
    # Extract Old and New Bandwidth values from the expect output log.
    local old_bw
    local new_bw
    old_bw=$(grep "Old Band Width" "$OUTPUT_DIR/set_bandwidth.out" | awk -F '=' '{print $2}' | tr -d ' ')
    new_bw=$(grep "New Band Width" "$OUTPUT_DIR/set_bandwidth.out" | awk -F '=' '{print $2}' | tr -d ' ')
    
    if [ "$old_bw" != "$new_bw" ]; then
        echo "Bandwidth changed from $old_bw to $new_bw. Reboot RU and waiting $WAIT_AFTER_REBOOT seconds..." | tee -a "$LOG_FILE"
        sleep $WAIT_AFTER_REBOOT
    else
        echo "Bandwidth not changed. Skipping reboot." | tee -a "$LOG_FILE"
    fi
}

# 函數：SSH 到 gNB 並啟動服務（使用 screen 啟動不同模式）
start_gnb() {
    local mode=$1
    echo "Starting gNB in $mode mode..." | tee -a "$LOG_FILE"
    export GNB_SERVER_USER GNB_SERVER_HOST PASSWORD

    local session_name
    local command

    if [ "$mode" == "nFAPI" ]; then
        # nFAPI VNF
        session_name="VNF"
        command="cd ~/FH_7.2_dev/openairinterface5g/cmake_targets/ran_build/build && echo '$PASSWORD' | sudo -S NFAPI_TRACE_LEVEL=info ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb-vnf.sa.band78.273prb.nfapi.conf --nfapi VNF"
        sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no $GNB_SERVER_USER@$GNB_SERVER_HOST "screen -dmS $session_name bash -c '$command'"
        check_status "Start gNB VNF"

        # nFAPI PNF
        session_name="PNF"
        command="cd ~/FH_7.2_dev/openairinterface5g/cmake_targets/ran_build/build && echo '$PASSWORD' | sudo -S NFAPI_TRACE_LEVEL=info ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb-pnf.band78.fhi72.4x4-liteon_new.conf --nfapi PNF --reorder-thread-disable 1 --thread-pool 1,3,5,7,9,11,13,15"
        sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no $GNB_SERVER_USER@$GNB_SERVER_HOST "screen -dmS $session_name bash -c '$command'"
        check_status "Start gNB PNF"
    else  # FAPI
        session_name="Monolithic"
        command="cd ~/FH_7.2_dev/openairinterface5g/cmake_targets/ran_build/build && echo '$PASSWORD' | sudo -S ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb.sa.band78.273prb.fhi72.4x4-liteon_new.conf --thread-pool 1,3,5,7,9,11,13,15"
        sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no $GNB_SERVER_USER@$GNB_SERVER_HOST "screen -dmS $session_name bash -c '$command'"
        check_status "Start gNB Monolithic"
    fi

    echo "Waiting $WAIT_AFTER_GNB seconds for gNB to initialize..." | tee -a "$LOG_FILE"
    sleep $WAIT_AFTER_GNB
}

# 函數：控制 UE 飛航模式
toggle_airplane_mode() {
    local state=$1
    echo "SSH to $CONTROL_PC_USER@$CONTROL_PC_IP. Setting airplane mode to $state..." | tee -a "$LOG_FILE"
    
    if [ "$state" == "off" ]; then
        ssh IA-PC "adb -s $ADB_DEVICE shell \"settings put global airplane_mode_on 0\" && adb -s $ADB_DEVICE shell \"am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false\"" >> "$LOG_FILE" 2>&1
    else
        ssh IA-PC "adb -s $ADB_DEVICE shell \"settings put global airplane_mode_on 1\" && adb -s $ADB_DEVICE shell \"am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true\"" >> "$LOG_FILE" 2>&1
    fi

    check_status "Toggle airplane mode to $state on remote CONTROL_PC"
    sleep 5  # 等待網絡穩定
}

# 函數：獲取 UE IP
get_ue_ip() {
    echo "Fetching UE IP from $CONTROL_PC_IP..." | tee -a "$LOG_FILE"
    UE_IP=$(ssh IA-PC "adb -s $ADB_DEVICE shell ip -f inet addr show ccmni0" | grep inet | awk '{print \$2}' | cut -d/ -f1)
    if [ -z "$UE_IP" ]; then
        UE_IP=$(ssh IA-PC "adb -s $ADB_DEVICE shell ip -f inet addr show ccmni1" | grep inet | awk '{print \$2}' | cut -d/ -f1)
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

    # 使用 SSH 進入 CN_SERVER，並在 CN_SERVER 上分別啟動 ping 與 iPerf3 測試
    ssh $CN_SERVER "bash -c 'ping -I ogstun $UE_IP'" > "$ping_log" 2>&1 &
    ping_pid=$!
    ssh $CN_SERVER "nohup iperf3 -s > /dev/null 2>&1 &"

    # 運行 iPerf3，先透過 SSH 到 $CONTROL_PC_USER@$CONTROL_PC_IP，再執行 adb 命令
    ssh IA-PC "adb -s $ADB_DEVICE shell \"$iperf_cmd\"" > "$iperf_log" 2>&1
    check_status "iPerf3 test for $test_id"

    # 停止 ping 測試
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

    # 遍歷 FAPI 和 nFAPI 模式
    for mode in "FAPI" "nFAPI"; do
        # 啟動 gNB
        start_gnb "$mode"

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
done

# 設置 Python 虛擬環境並生成圖表和 Markdown 文件
echo "Setting up Python virtual environment and generating report..." | tee -a "$LOG_FILE"

# 創建並啟用虛擬環境
python3 -m venv "$VENV_DIR" >> "$LOG_FILE" 2>&1
check_status "Create Python virtual environment"
source "$VENV_DIR/bin/activate" >> "$LOG_FILE" 2>&1
check_status "Activate Python virtual environment"

# 安裝依賴
pip install matplotlib pandas >> "$LOG_FILE" 2>&1
check_status "Install Python dependencies"

# 生成繪圖腳本
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

# 在虛擬環境中運行繪圖腳本
python "$OUTPUT_DIR/generate_plot.py" >> "$LOG_FILE" 2>&1
check_status "Generate plot"

# 生成 Markdown 報告
cat << EOF > "$OUTPUT_DIR/report.md"
# Network Test Report
Generated on: $(date)

## Test Results
![Scatter Plot]($OUTPUT_DIR/scatter_plot.png)

## Data
$(cat "$CSV_FILE" | column -t -s,)
EOF

# 退出虛擬環境
deactivate >> "$LOG_FILE" 2>&1

echo "Test completed at $(date). Results saved in $OUTPUT_DIR" | tee -a "$LOG_FILE"