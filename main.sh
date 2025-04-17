#!/bin/bash

source variable.sh
source collect_data_fromCN.sh
source modify_UE.sh
source run_gNB.sh
source set_ru_bandwidth.sh

# Execute remote script on main host
sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no $GNB_SERVER_USER@$GNB_SERVER_HOST "screen -dmS oaiLONvf bash -c 'echo $PASSWORD | sudo -S /home/oai72/Script/oaiLONvf.sh'"

# set_ru_bandwidth "100000000"  # Set RU bandwidth to 100M

# Stop and start split setup
stop_split_setup "100M"
start_split_setup "100M"

# stop_single_setup "100M" "MONO"     # Stop 100M bandwidth MONO setup
# start_single_setup "100M" "MONO"    # Start 100M bandwidth MONO setup

# Toggle airplane mode to reset UE with retry logic
MAX_RETRIES=6
RETRY_COUNT=0
UE_IP=""

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo "Attempt $(($RETRY_COUNT + 1)) of $MAX_RETRIES to reset UE connection"
    toggle_airplane_mode "on"
    sleep 3
    toggle_airplane_mode "off"
    sleep 3
    
    # Get UE IP
    get_ue_ip
    
    # Check if UE IP was successfully obtained
    if [ -n "$UE_IP" ]; then
        echo "Successfully connected UE with IP: $UE_IP"
        break
    fi
    
    echo "Failed to get UE IP on attempt $(($RETRY_COUNT + 1))"
    RETRY_COUNT=$((RETRY_COUNT + 1))
    
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "ERROR: Failed to get UE IP after $MAX_RETRIES attempts. Exiting script."
        stop_split_setup "100M"
        exit 1
    fi
    
    echo "Retrying..."
    sleep 5
done

sleep 1
# Define parameters
TEST_DURATION=5  # Duration in seconds

# Set to true to enable testing, false to disable
TEST_UDP=true
TEST_TCP=false

DL_START=100
DL_END=200
DL_STEP=100

ENABLE_UL=false  # Enable uplink testing
UL_START=10
UL_END=20
UL_STEP=10

SERVER_IP="10.45.0.1"
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
            run_iperf "client" "$SERVER_IP" "$params" "./data/$(date +"%Y%m%d")/iperf-${file_base}-UE"
            iperf-stop "./data/$(date +"%Y%m%d")/iperf-${file_base}-CN"
            
            # Stop ping and save results
            sleep $SLEEP_window
            ping-stop "./data/$(date +"%Y%m%d")/ping-${file_base}"
            sleep 2
        done
    done
done

stop_split_setup "100M"
toggle_airplane_mode "on"