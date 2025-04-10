#!/bin/bash

# Global variables
ADB_DEVICE="0123456789ABCDEF"
CONTROL_PC_USER="your_user"
CONTROL_PC_IP="your_control_pc_ip"
LOG_FILE="/path/to/your/logfile.log"

# 函數：檢查操作狀態
check_status() {
    local message=$1
    if [ $? -eq 0 ]; then
        echo "[SUCCESS] $message" | tee -a "$LOG_FILE"
    else
        echo "[ERROR] $message" | tee -a "$LOG_FILE"
    fi
}

# 函數：控制 UE 飛航模式
toggle_airplane_mode() {
    local state=$1
    echo "SSH to $CONTROL_PC_USER@$CONTROL_PC_IP. Setting airplane mode to $state..." | tee -a "$LOG_FILE"
    
    if [ "$state" == "off" ]; then
        ssh "$CONTROL_PC_USER@$CONTROL_PC_IP" "adb -s $ADB_DEVICE shell \"settings put global airplane_mode_on 0\" && adb -s $ADB_DEVICE shell \"am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false\"" >> "$LOG_FILE" 2>&1
    else
        ssh "$CONTROL_PC_USER@$CONTROL_PC_IP" "adb -s $ADB_DEVICE shell \"settings put global airplane_mode_on 1\" && adb -s $ADB_DEVICE shell \"am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true\"" >> "$LOG_FILE" 2>&1
    fi

    check_status "Toggle airplane mode to $state on remote CONTROL_PC"
    sleep 5  # 等待網絡穩定
}

# 示例：開啟飛航模式
toggle_airplane_mode "on"

# 示例：關閉飛航模式
toggle_airplane_mode "off"
