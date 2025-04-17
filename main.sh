#!/bin/bash

source variable.sh
source collect_data_fromCN.sh
source modify_UE.sh
source run_gNB.sh

# stop_split_setup "100M"
# start_split_setup "100M"
# toggle_airplane_mode "on"
# sleep 10
# toggle_airplane_mode "off"

if [ -z "$UE_IP" ]; then
    get_ue_ip
fi

ping-start $UE_IP
sleep 10

sleep 1
# Define parameters
DL_START=100
DL_END=200
DL_STEP=100
UL_START=10
UL_END=20
UL_STEP=10
TEST_DURATION=3  # Duration in seconds
SERVER_IP="10.45.0.1"

# Set to true to enable testing, false to disable
TEST_UDP=true
TEST_TCP=false
ENABLE_UL=false  # 新增 uplink 開關

# Create directory for results if it doesn't exist
mkdir -p "./data/$(date +"%Y%m%d")"

# 不用函數而是直接執行，合併上行下行測試邏輯
# 定義測試類型
protocols=""
[ "$TEST_UDP" = true ] && protocols+=" udp"
[ "$TEST_TCP" = true ] && protocols+=" tcp"

# 定義測試方向和參數
directions="dl"
[ "$ENABLE_UL" = true ] && directions+=" ul"

# 執行所有測試組合
for direction in $directions; do
    # 根據方向設定開始值、結束值和步進值
    if [ "$direction" = "dl" ]; then
        start=$DL_START
        end=$DL_END
        step=$DL_STEP
        dir_name="Downlink"
        reverse=""
    else
        start=$UL_START
        end=$UL_END
        step=$UL_STEP
        dir_name="Uplink"
        reverse="-R"
    fi
    
    for protocol in $protocols; do
        echo "Running ${dir_name} ${protocol} tests (${start}M-${end}M)"
        
        for bw in $(seq $start $step $end); do
            echo "Testing ${dir_name} ${protocol} at ${bw}M"
            
            # 設定參數
            params="$reverse -b ${bw}M -t $TEST_DURATION -J"
            [ "$protocol" = "udp" ] && params="-u $params"
            
            # 設定檔案名稱
            file_base="iperf-${direction}-${protocol}-${bw}M"
            
            # 執行測試
            iperf-start
            run_iperf "client" "$SERVER_IP" "$params" "${file_base}-UE"
            iperf-stop "${file_base}-CN"
            sleep 2
        done
    done
done

ping-stop "ping-value"
