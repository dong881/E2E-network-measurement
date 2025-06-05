#!/bin/bash

source variable.sh
source core_network_utils.sh
source user_equipment_utils.sh
source gnb_utils.sh

# Initialize variables
UE_IP=""
MANUAL_MODE_ENABLED=false
PASS=false
CURRENT_MODE="MONO"

# Parse input arguments (只允許四個參數: --manual-mode, --mode, --pass, 與 --shutdown)
SHUTDOWN_MODE=false
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --manual-mode) MANUAL_MODE_ENABLED=true ;;
        --mode) CURRENT_MODE="$2"; shift ;;
        --pass) PASS=true ;;
        --shutdown) SHUTDOWN_MODE=true ;;
        --ru-bw) 
            source radio_unit_utils.sh
            RU_BW="$2"
            echo "Setting LiteOn RU bandwidth to: $RU_BW"
            radio_unit_utils "$RU_BW"
            exit 1 ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

if [ "$SHUTDOWN_MODE" = true ]; then
    echo "Shutdown mode enabled. Stopping gNB and exiting."
    stop_gNB "MONO"
    stop_gNB "NFAPI"
    exit 0
fi

# Calculate total test combinations and estimated time
TOTAL_TESTS=0
if [ "$TEST_UDP" = true ]; then
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
fi
if [ "$TEST_TCP" = true ]; then
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
fi
if [ "$ENABLE_UL" = true ]; then
    TOTAL_TESTS=$((TOTAL_TESTS * 2))
fi

# Calculate number of bandwidth steps for DL and UL
DL_STEPS=$(( (DL_END - DL_START) / DL_STEP + 1 ))
UL_STEPS=0
if [ "$ENABLE_UL" = true ]; then
    UL_STEPS=$(( (UL_END - UL_START) / UL_STEP + 1 ))
fi

# Calculate total test iterations
TOTAL_ITERATIONS=$((TOTAL_TESTS * (DL_STEPS + UL_STEPS)))

# Calculate estimated time in seconds
# Each test includes: TEST_DURATION + 3 * SLEEP_WINDOW + 2 seconds
ESTIMATED_TIME=$((TOTAL_ITERATIONS * (TEST_DURATION + 3 * SLEEP_WINDOW + 2)))

# Convert to hours and minutes
ESTIMATED_HOURS=$((ESTIMATED_TIME / 3600))
ESTIMATED_MINUTES=$(( (ESTIMATED_TIME % 3600) / 60 ))

echo "📊 Test Configuration Summary:"
echo "  🔢 Total test combinations: $TOTAL_TESTS"
echo "  🔄 Total iterations: $TOTAL_ITERATIONS"
echo "  ⏱️  Estimated duration: ${ESTIMATED_HOURS}h ${ESTIMATED_MINUTES}m"

# Get current date and next day
CURRENT_DATE=$(date +"%Y%m%d")
NEXT_DATE=$(date -d "tomorrow" +"%Y%m%d")

# Create directory name based on mode and bandwidth range
DIR_NAME="${CURRENT_DATE}-${CURRENT_MODE}(${DL_START}-${DL_END}M)"
if [ "$ENABLE_UL" = true ]; then
    DIR_NAME="${DIR_NAME}-UL(${UL_START}-${UL_END}M)"
fi

# Check if estimated end time would be tomorrow
CURRENT_TIMESTAMP=$(date +%s)
ESTIMATED_END_TIMESTAMP=$((CURRENT_TIMESTAMP + ESTIMATED_TIME))
ESTIMATED_END_DATE=$(date -d "@$ESTIMATED_END_TIMESTAMP" +"%Y%m%d")

# Create appropriate directory
if [ "$ESTIMATED_END_DATE" != "$CURRENT_DATE" ]; then
    echo "⚠️  Warning: Tests will likely continue into tomorrow"
    echo "Creating directories for both today and tomorrow"
    mkdir -p "./data/${DIR_NAME}"
    mkdir -p "./data/${NEXT_DATE}-${CURRENT_MODE}(${DL_START}-${DL_END}M)"
else
    mkdir -p "./data/${DIR_NAME}"
fi

echo "🔎 Current status:"
echo "  🛠️  MANUAL_MODE_ENABLED = $([ "$MANUAL_MODE_ENABLED" = true ] && echo '✅' || echo '❌')"
echo "  🎛️  CURRENT_MODE        = $CURRENT_MODE"
echo "  📦 TEST_UDP            = $([ "$TEST_UDP" = true ] && echo '✅' || echo '❌')"
echo "  📦 TEST_TCP            = $([ "$TEST_TCP" = true ] && echo '✅' || echo '❌')"
echo "  ⬆️  ENABLE_UL           = $([ "$ENABLE_UL" = true ] && echo '✅' || echo '❌')"
echo "  🔁 MAX_RETRIES         = $MAX_RETRIES"
echo "  ⏱️  TEST_DURATION       = $TEST_DURATION"
echo "  ⬇️  DL_START            = $DL_START"
echo "  ⬇️  DL_END              = $DL_END"
echo "  ⬇️  DL_STEP             = $DL_STEP"
if [ "$ENABLE_UL" = true ]; then
    echo "  ⬆️  UL_START            = $UL_START"
    echo "  ⬆️  UL_END              = $UL_END"
    echo "  ⬆️  UL_STEP             = $UL_STEP"
fi

if [ "$MANUAL_MODE_ENABLED" = true ]; then
    if [ "$PASS" = false ]; then
        reset_all "$CURRENT_MODE"
        start_gNB "$CURRENT_MODE"
    fi
    wait_for_ue_parameters
    echo "gNB is fully started. You can manually turn off UE airplane mode now~"
    while true; do
        get_ue_ip
        if [ -n "$UE_IP" ]; then
            echo "Successfully obtained UE IP: $UE_IP"
            break
        fi
        sleep 1
    done
else
    reset_all "$CURRENT_MODE"
    start_gNB "$CURRENT_MODE"
    sleep 60
    # Toggle airplane mode to reset UE with retry logic
    RETRY_COUNT=0

    toggle_airplane_mode "on"
    sleep 15
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
            stop_gNB "$CURRENT_MODE"
            exit 1
        fi
        
        echo "Retrying..."
        sleep 5
    done
fi

sleep 1

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
        reverse="-R"
    else
        start=$UL_START
        end=$UL_END
        step=$UL_STEP
        dir_name="Uplink"
        reverse=""
    fi
    
    for protocol in $protocols; do
        echo "Running ${dir_name} ${protocol} tests (${start}M-${end}M)"
        # Check if UE_IP exists and is not empty, if not get it
        [ -z "$UE_IP" ] && get_ue_ip
        ping-start $UE_IP
        sleep $SLEEP_WINDOW
        ping-stop "./data/${DIR_NAME}/ping-${direction}-${protocol}-idle.log"

        for bw in $(seq $start $step $end); do
            echo "Testing ${dir_name} ${protocol} at ${bw}M"

            # Set iperf parameters - TEST_DURATION is sourced
            params="-b ${bw}M -t $TEST_DURATION -p 5201 $reverse -J"
            [ "$protocol" = "udp" ] && params="-u $params"
            
            # Set file base name
            file_base="${direction}-${protocol}-${bw}M"
            sleep $SLEEP_WINDOW
            # Start ping and wait
            ping-start $UE_IP
            sleep $SLEEP_WINDOW
            
            # Start iperf test
            iperf-start
            run_iperf "client" "$TEST_SERVER_IP" "$params" "./data/${DIR_NAME}/iperf-${file_base}-UE.json"
            iperf-stop "./data/${DIR_NAME}/iperf-${file_base}-CN.json"
            
            # Stop ping and save results
            sleep $SLEEP_WINDOW
            ping-stop "./data/${DIR_NAME}/ping-${file_base}.log"
            sleep 2
        done
    done
done

stop_gNB "$CURRENT_MODE"
sleep 5
fetch_and_analyze_logs "$CURRENT_MODE"
# toggle_airplane_mode "on"