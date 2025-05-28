#!/bin/bash

# Function: radio_unit_utils
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
#   WAIT_AFTER_REBOOT - Time to wait after reboot in seconds
#
# Returns:
#   0 on success, non-zero on failure
#
# Outputs:
#   - Creates expect script at $OUTPUT_DIR/set_bandwidth.exp
#   - Creates output log at $OUTPUT_DIR/set_bandwidth.out

source variable.sh
export OUTPUT_DIR="test_results_$(date +%Y%m%d)"
if [ -f "$(dirname "$0")/run_config.sh" ]; then
	source "$(dirname "$0")/run_config.sh"
fi
mkdir -p "$OUTPUT_DIR"
radio_unit_utils() {
    local bw=$1
    echo "Setting RU bandwidth to $bw bps..."

    # Ensure the output directory exists
    mkdir -p "$OUTPUT_DIR"

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

    # Ensure the script is executable
    chmod +x "$OUTPUT_DIR/set_bandwidth.exp"

    # Export required variables for the expect script
    export RU_USER RU_IP RU_PASSWORD RU_ENABLE_PASSWORD OUTPUT_DIR bw

    # Run the expect script and redirect output to .out file
    expect "$OUTPUT_DIR/set_bandwidth.exp" > "$OUTPUT_DIR/set_bandwidth.out" 2>&1

    # Check if the RU is rebooting
    if grep -q "system is going down" "$OUTPUT_DIR/set_bandwidth.out"; then
        echo "Bandwidth changed to $bw. RU is rebooting..."
        echo "Waiting $WAIT_AFTER_REBOOT seconds for RU to reboot..."
        sleep $WAIT_AFTER_REBOOT
    else
        echo "Bandwidth unchanged. No reboot needed."
    fi
}

# radio_unit_utils "$1"