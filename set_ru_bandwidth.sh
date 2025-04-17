#!/bin/bash

# Function: set_ru_bandwidth
# Description: Sets the bandwidth for a Remote Unit (RU) device via SSH
#
# This function performs the following operations:
# 1. Creates an expect script to handle SSH interaction
# 2. Logs into the RU using provided credentials
# 3. Checks current bandwidth
# 4. Sets new bandwidth value
# 5. Verifies the change
# 6. Reboots the RU if bandwidth was changed
#
# Arguments:
#   $1 - bandwidth value in bps (bits per second)
#
# Environment variables required:
#   RU_USER - Username for RU SSH login
#   RU_IP - IP address of the RU
#   RU_PASSWORD - Password for RU SSH login
#   RU_ENABLE_PASSWORD - Enable password for privileged mode
#   OUTPUT_DIR - Directory for output files
#   LOG_FILE - Path to log file
#   WAIT_AFTER_REBOOT - Time to wait after reboot in seconds
#
# Returns:
#   0 on success, non-zero on failure
#
# Outputs:
#   - Creates expect script at $OUTPUT_DIR/set_bandwidth.exp
#   - Creates output log at $OUTPUT_DIR/set_bandwidth.out

source variable.sh
# Check if expect is installed
if ! command -v expect &> /dev/null; then
    echo "expect could not be found. Please install it to proceed."
    exit 1
fi
# Check if the required environment variables are set
if [ -z "$RU_USER" ] || [ -z "$RU_IP" ] || [ -z "$RU_PASSWORD" ] || [ -z "$RU_ENABLE_PASSWORD" ]; then
    echo "Error: Required environment variables are not set." >&2
    exit 1
fi
# Check if the bandwidth argument is provided
if [ -z "$1" ]; then
    echo "Error: Bandwidth argument is missing." >&2
    exit 1
fi
# Check if the bandwidth argument is a valid number
if ! [[ "$1" =~ ^[0-9]+$ ]]; then
    echo "Error: Bandwidth argument must be a valid number." >&2
    exit 1
fi
# Check if the bandwidth argument is within a valid range
if [ "$1" -lt 1000000 ] || [ "$1" -gt 1000000000 ]; then
    echo "Error: Bandwidth argument must be between 1Mbps and 1Gbps." >&2
    exit 1
fi

# 創建輸出目錄
mkdir -p "$OUTPUT_DIR"

set_ru_bandwidth() {
    local bw=$1
    echo "Setting RU bandwidth to $bw bps..."

    cat << 'EOF' > "$OUTPUT_DIR/set_bandwidth.exp"
#!/usr/bin/expect
set timeout 60
spawn ssh $env(RU_USER)@$env(RU_IP)
expect "password:"
send "$env(RU_PASSWORD)\r"
expect ">"
send "enable\r"
expect "Password:"
send "$env(RU_ENABLE_PASSWORD)\r"
expect "#"
send "show running-config\r"
expect "#"
send "configure terminal\r"
expect "(config)#"
send "bandwidth $env(bw)\r"
expect "(config)#"
send "exit\r"
expect "#"
send "show running-config\r"
expect "#"
if {[catch {set old_bw [exec grep "Band Width = " $env(OUTPUT_DIR)/set_bandwidth.out | head -1 | cut -d= -f2 | tr -d " "]}]} {
    set old_bw "unknown"
}
if {$old_bw != $env(bw)} {
    send "reboot\r"
    expect "system is going down"
}
expect eof
EOF

    chmod +x "$OUTPUT_DIR/set_bandwidth.exp"
    export RU_USER RU_IP RU_PASSWORD RU_ENABLE_PASSWORD OUTPUT_DIR bw
    expect "$OUTPUT_DIR/set_bandwidth.exp"

    if grep -q "system is going down" "$OUTPUT_DIR/set_bandwidth.out"; then
        echo "Bandwidth changed to $bw. RU is rebooting..."
        echo "Waiting $WAIT_AFTER_REBOOT seconds for RU to reboot..."
        sleep $WAIT_AFTER_REBOOT
    else
        echo "Bandwidth unchanged. No reboot needed."
    fi
}

set_ru_bandwidth "$1"