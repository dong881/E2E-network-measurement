#!/bin/bash

# 在遠端伺服器上創建 screen session 並執行命令
# sshpass -p "$CN_SERVER_PASSWORD" ssh "$CN_SERVER_USER@$CN_SERVER_HOST" \
# "screen -dmS cn_collect-iperf ~/Ming-collect-data/collect_iperf.sh \"nFAPI-100M-UDP-DL-test\""

# 如果要關閉遠端的 screen session，可以使用以下命令：
# sshpass -p "$CN_SERVER_PASSWORD" ssh "$CN_SERVER_USER@$CN_SERVER_HOST" "screen -X -S cn_collect-iperf quit"

source variable.sh

ping-start() {
    local TARGET_IP="$1"
    # Start ping on remote server in a screen session
    sshpass -p "$CN_SERVER_PASSWORD" ssh "$CN_SERVER_USER@$CN_SERVER_HOST" \
    "screen -dmS ping-session bash -c 'ping -I ${INTERFACE} ${TARGET_IP} | while read line; do echo \"\$(date +\"%Y-%m-%d %H:%M:%S\"): \$line\"; done > ~/ping_value.log'"
}

ping-stop() {
    # Kill the ping screen session
    sshpass -p "$CN_SERVER_PASSWORD" ssh "$CN_SERVER_USER@$CN_SERVER_HOST" \
    "screen -X -S ping-session quit"
    
    # Copy the ping results back to local machine
    local output_file="$1"
    if [ -z "$output_file" ]; then
        output_file="ping_results"
    fi
    sshpass -p "$CN_SERVER_PASSWORD" scp "$CN_SERVER_USER@$CN_SERVER_HOST:~/ping_value.log" "./data/${output_file}.log"
}

iperf-start() {
    # 在遠端伺服器上啟動 iperf server 並將輸出導向到日誌檔案
    sshpass -p "$CN_SERVER_PASSWORD" ssh "$CN_SERVER_USER@$CN_SERVER_HOST" \
    "screen -dmS iperf-server bash -c 'iperf3 -s -J | tee ~/iperf-server.json'"
}

iperf-stop() {
    # 當測試完成後，從遠端複製日誌檔案到本機
    local output_file="$1"
    sshpass -p "$CN_SERVER_PASSWORD" scp "$CN_SERVER_USER@$CN_SERVER_HOST:~/iperf-server.json" "./data/${output_file}.json"

    # 清理：關閉遠端的 screen session
    sshpass -p "$CN_SERVER_PASSWORD" ssh "$CN_SERVER_USER@$CN_SERVER_HOST" \
    "screen -X -S iperf-server quit"
}
