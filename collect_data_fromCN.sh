#!/bin/bash

# 在遠端伺服器上創建 screen session 並執行命令
source variable.sh
sshpass -p "$CN_SERVER_PASSWORD" ssh "$CN_SERVER_USER@$CN_SERVER_HOST" \
"screen -dmS cn_collect-iperf ~/Ming-collect-data/collect_iperf.sh \"nFAPI-100M-UDP-DL-test\""

# 如果要關閉遠端的 screen session，可以使用以下命令：
# sshpass -p "$CN_SERVER_PASSWORD" ssh "$CN_SERVER_USER@$CN_SERVER_HOST" "screen -X -S cn_collect-iperf quit"
