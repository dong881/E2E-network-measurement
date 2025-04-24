#!/bin/bash

# Global variables
# ADB_DEVICE="0123456789ABCDEF"
source variable.sh

# 函數：控制 UE 飛航模式
toggle_airplane_mode() {
    local state=$1
    echo "Setting airplane mode to $state on $CONTROL_PC_USER@$CONTROL_PC_IP"
    sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTIONS $CONTROL_PC_USER@$CONTROL_PC_IP \
        "adb -s $ADB_DEVICE shell \"settings put global airplane_mode_on $([ \"$state\" = \"off\" ] && echo 0 || echo 1)\" \
         && adb -s $ADB_DEVICE shell \"am broadcast -a android.intent.action.AIRPLANE_MODE --ez state $([ \"$state\" = \"off\" ] && echo false || echo true)\""
    sleep 5
}

# 函數：獲取 UE IP
get_ue_ip() {
    UE_IP=$(sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTIONS $CONTROL_PC_USER@$CONTROL_PC_IP \
             "adb -s $ADB_DEVICE shell ip -f inet addr show ccmni0" | awk '/inet/ {print $2}' | cut -d/ -f1)
    UE_IP=${UE_IP:-$(sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTIONS $CONTROL_PC_USER@$CONTROL_PC_IP \
             "adb -s $ADB_DEVICE shell ip -f inet addr show ccmni1" | awk '/inet/ {print $2}' | cut -d/ -f1)}
    [ -z "$UE_IP" ] && { echo "Error: Unable to fetch UE IP." >&2; }
    echo "UE IP: $UE_IP"
}

# 函數：在 UE 上運行 iperf3 測試
run_iperf() {
    local mode=$1 server_ip=$2 options=$3 local_log=$4
    echo "Running iperf3 in $mode mode…"
    [ -z "$UE_IP" ] && get_ue_ip

    # 確保 iperf3 binary 存在
    if sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTIONS $CONTROL_PC_USER@$CONTROL_PC_IP \
         "adb -s $ADB_DEVICE shell ls /data/local/tmp/iperf3 2>/dev/null" | grep -q not_exists; then
        echo "Uploading iperf3…"
        sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTIONS $CONTROL_PC_USER@$CONTROL_PC_IP \
            "adb -s $ADB_DEVICE push \"$control_pc_iperf_path\" /data/local/tmp/iperf3"
    fi

    sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTIONS $CONTROL_PC_USER@$CONTROL_PC_IP \
        "adb -s $ADB_DEVICE shell chmod +x /data/local/tmp/iperf3"

    if [ "$mode" = "server" ]; then
        sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTIONS $CONTROL_PC_USER@$CONTROL_PC_IP \
            "adb -s $ADB_DEVICE shell /data/local/tmp/iperf3 -s $options" &
        echo "iperf3 server started"
    elif [ "$mode" = "client" ]; then
        [ -z "$server_ip" ] && { echo "Error: Server IP required"; return 1; }
        if [ -n "$local_log" ]; then
            local ts=$(date +%Y%m%d_%H%M%S)
            local ue_log="/data/local/tmp/iperf3_${ts}.log"
            local remote_log="C:/Data/iperf3-temp.log"
            
            # Run iperf directly on the UE and save output to UE's storage
            echo "Running iperf3 client on UE device..."
            sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTIONS $CONTROL_PC_USER@$CONTROL_PC_IP \
                "adb -s $ADB_DEVICE shell \"/data/local/tmp/iperf3 -c $server_ip -B $UE_IP $options > $ue_log\""
            
            # Pull the result from UE to Windows control PC
            sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTIONS $CONTROL_PC_USER@$CONTROL_PC_IP \
                "adb -s $ADB_DEVICE pull $ue_log \"$remote_log\""
            
            # Copy from Windows control PC to local Linux machine
            sshpass -p "$SERVER_PASSWORD" scp $SSH_OPTIONS "$CONTROL_PC_USER@$CONTROL_PC_IP:$remote_log" "$local_log"
            
            # Clean up on device
            sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTIONS $CONTROL_PC_USER@$CONTROL_PC_IP \
                "adb -s $ADB_DEVICE shell rm -f $ue_log"
            
            echo "Results saved to $local_log"
        else
            # Run iperf3 with JSON output and timestamp for display
            sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTIONS $CONTROL_PC_USER@$CONTROL_PC_IP \
                "adb -s $ADB_DEVICE shell \"current_time=\$(date +\\\"%s\\\"); echo \\\"Test started at: \$(date)\\\"; /data/local/tmp/iperf3 -c $server_ip -B $UE_IP $options\""
        fi
    else
        echo "Error: mode must be server or client"
        return 1
    fi
}

# # 示例：開啟飛航模式
# toggle_airplane_mode "on"

# # 示例：關閉飛航模式
# toggle_airplane_mode "off"

## 示：獲取 UE IP (可以透過是否順利取得UE IP判斷gNB是否能然順利運作)
# get_ue_ip

# 示例：在 UE 上運行 iperf3 服務器
# run_iperf "server" "" "-p 5201"

# 示例：在 UE 上運行 iperf3 客戶端
# run_iperf "client" "10.45.0.1" "-u -b 100M -t 10"

# 示例：在 UE 上運行 iperf3 客戶端並儲存日誌到本機
# run_iperf "client" "10.45.0.1" "-u -b 100M -t 3" "/home/ming/E2E-network-measurement/data/iperf3_results.log"

