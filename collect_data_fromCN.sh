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
    "screen -dmS ping-session bash -c 'ping -I ${INTERFACE} ${TARGET_IP} | while read line; do echo \"\$(date +\"%s\"): \$line\"; done > ~/ping_value.log'"
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
    # 創建處理腳本，無需 jq
    sshpass -p "$CN_SERVER_PASSWORD" ssh "$CN_SERVER_USER@$CN_SERVER_HOST" "cat > ~/process_iperf.sh" << 'EOF'
#!/bin/bash
current_time=$(date +"%s")
iperf3 -s -J > ~/temp_iperf.json
# 用 sed 插入 start_timestamp 欄位到 JSON 第一層
sed "1s|{|\{\"start_timestamp\": $current_time,|" ~/temp_iperf.json > ~/iperf-server.json
rm ~/temp_iperf.json
EOF

    # 設定腳本權限並在screen中啟動
    sshpass -p "$CN_SERVER_PASSWORD" ssh "$CN_SERVER_USER@$CN_SERVER_HOST" \
    "chmod +x ~/process_iperf.sh && screen -dmS iperf-server ~/process_iperf.sh"
    sleep 1
}

iperf-stop() {
    # 當測試完成後，從遠端複製日誌檔案到本機
    local output_file="$1"
    if [ -z "$output_file" ]; then
        output_file="~/iperf_results.json"
    fi
    sshpass -p "$CN_SERVER_PASSWORD" scp "$CN_SERVER_USER@$CN_SERVER_HOST:~/iperf-server.json" "$output_file"

    # 清理：關閉遠端的 screen session
    sshpass -p "$CN_SERVER_PASSWORD" ssh "$CN_SERVER_USER@$CN_SERVER_HOST" \
    "screen -X -S iperf-server quit"
}
