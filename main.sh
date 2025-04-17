#!/bin/bash

source variable.sh
source collect_data_fromCN.sh
source modify_UE.sh
source run_gNB.sh
source set_ru_bandwidth.sh

set_ru_bandwidth "100000000"  # Set RU bandwidth to 100M

# Stop and start split setup
stop_split_setup "100M"
start_split_setup "100M"

# stop_single_setup "100M" "MONO"     # Stop 100M bandwidth MONO setup
# start_single_setup "100M" "MONO"    # Start 100M bandwidth MONO setup

# Toggle airplane mode to reset UE
toggle_airplane_mode "on"
sleep 30
toggle_airplane_mode "off"

# Get UE IP if not already set
if [ -z "$UE_IP" ]; then
    get_ue_ip
fi

sleep 1
# Define parameters
DL_START=100
DL_END=200
DL_STEP=100
UL_START=10
UL_END=20
UL_STEP=10
TEST_DURATION=5  # Duration in seconds
SERVER_IP="10.45.0.1"

# Set to true to enable testing, false to disable
TEST_UDP=true
TEST_TCP=false
ENABLE_UL=false  # Enable uplink testing

# Create directory for results if it doesn't exist
mkdir -p "./data/$(date +"%Y%m%d")"

# Define test protocols
protocols=""
[ "$TEST_UDP" = true ] && protocols+=" udp"
[ "$TEST_TCP" = true ] && protocols+=" tcp"

# Define test directions
directions="dl"
[ "$ENABLE_UL" = true ] && directions+=" ul"

# Execute all test combinations
for direction in $directions; do
    # Set parameters based on direction
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
            
            # Set iperf parameters
            params="$reverse -b ${bw}M -t $TEST_DURATION -J"
            [ "$protocol" = "udp" ] && params="-u $params"
            
            # Set file base name
            file_base="${direction}-${protocol}-${bw}M"
            
            # Start ping and wait
            ping-start $UE_IP
            SLEEP_window=5
            sleep $SLEEP_window
            
            # Start iperf test
            iperf-start
            run_iperf "client" "$SERVER_IP" "$params" "iperf-${file_base}-UE"
            iperf-stop "iperf-${file_base}-CN"
            
            # Stop ping and save results
            sleep $SLEEP_window
            ping-stop "ping-${file_base}"
            sleep 2
        done
    done
done
