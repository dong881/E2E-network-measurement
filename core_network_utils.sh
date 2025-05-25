#!/bin/bash

# 在遠端伺服器上創建 screen session 並執行命令
# sshpass -p "$SERVER_PASSWORD" ssh "$CN_SERVER_USER@$CN_SERVER_HOST" \
# "screen -dmS cn_collect-iperf ~/Ming-collect-data/collect_iperf.sh \"nFAPI-100M-UDP-DL-test\""

# 如果要關閉遠端的 screen session，可以使用以下命令：
# sshpass -p "$SERVER_PASSWORD" ssh "$CN_SERVER_USER@$CN_SERVER_HOST" "screen -X -S cn_collect-iperf quit"

source variable.sh

ping-start() {
    local TARGET_IP="$1"
    # Start ping on remote server in a screen session
    sshpass -p "$SERVER_PASSWORD" ssh "$CN_SERVER_USER@$CN_SERVER_HOST" \
    "screen -dmS ping-session bash -c 'ping -I ${INTERFACE} ${TARGET_IP} | while read line; do echo \"\$(date +\"%s\"): \$line\"; done > ~/ping_value.log'"
}

ping-stop() {
    # Kill the ping screen session
    sshpass -p "$SERVER_PASSWORD" ssh "$CN_SERVER_USER@$CN_SERVER_HOST" \
    "screen -X -S ping-session quit"
    
    # Copy the ping results back to local machine
    local output_file="$1"
    if [ -z "$output_file" ]; then
        output_file="~/ping_results.log"
    fi
    sshpass -p "$SERVER_PASSWORD" scp "$CN_SERVER_USER@$CN_SERVER_HOST:~/ping_value.log" "$output_file"
}

iperf-start() {
    # 創建處理腳本，先寫入 timestamp 再接續儲存 log
    sshpass -p "$SERVER_PASSWORD" ssh "$CN_SERVER_USER@$CN_SERVER_HOST" "cat > ~/process_iperf.sh" << 'EOF'
#!/bin/bash
current_time=$(date +"%s")
echo "{\"start_timestamp\": $current_time," > ~/iperf-server.json
# 移除 iperf3 輸出的第一個 '{'
tail -n +2 <(iperf3 -s -J) >> ~/iperf-server.json
EOF

    # 設定腳本權限並在screen中啟動
    sshpass -p "$SERVER_PASSWORD" ssh "$CN_SERVER_USER@$CN_SERVER_HOST" \
    "chmod +x ~/process_iperf.sh && screen -dmS iperf-server ~/process_iperf.sh"
    sleep 1
}

iperf-stop() {
    # 清理：關閉遠端的 screen session
    sshpass -p "$SERVER_PASSWORD" ssh "$CN_SERVER_USER@$CN_SERVER_HOST" \
    "screen -X -S iperf-server quit"

    # 當測試完成後，從遠端複製日誌檔案到本機
    local output_file="$1"
    if [ ! -z "$output_file" ]; then
        sshpass -p "$SERVER_PASSWORD" scp "$CN_SERVER_USER@$CN_SERVER_HOST:~/iperf-server.json" "$output_file"
    fi
}
