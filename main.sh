#!/bin/bash

source variable.sh
source core_network_utils.sh
source user_equipment_utils.sh
source gnb_utils.sh
source radio_unit_utils.sh
check_jura_ru_ptp_sync

# Initialize variables
UE_IP=""
MANUAL_MODE_ENABLED=false
PASS=false
CURRENT_MODE="Monolithic"
SINGLE_MACHINE_MODE=false

# Parse input arguments (只允許四個參數: --manual-mode, --mode, --pass, 與 --shutdown)
SHUTDOWN_MODE=false
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --help|-h) 
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --help, -h          Show this help message and exit"
            echo "  --manual-mode       Enable manual mode (skip automatic UE connection)"
            echo "  --mode NFAPI         Set gNB mode (default: Monolithic)"
            echo "  --single-machine    Run NFAPI mode on single machine (only valid with --mode NFAPI)"
            echo "  --pass              Skip reset and gNB restart (continue from current state)"
            echo "  --shutdown          Shutdown mode - stop gNB and exit"
            echo "  --ru-bw BANDWIDTH   Set LiteOn RU bandwidth and exit"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Run with default settings"
            echo "  $0 --manual-mode                     # Run in manual mode"
            echo "  $0 --mode Monolithic --pass          # Run in Monolithic mode, skip reset"
            echo "  $0 --mode NFAPI --single-machine     # Run NFAPI mode on single machine"
            echo "  $0 --shutdown                        # Stop gNB and exit"
            echo "  $0 --ru-bw 100000000                 # Set RU bandwidth to 100MHz and exit"
            exit 0 ;;
        --manual-mode) MANUAL_MODE_ENABLED=true ;;
        --mode) CURRENT_MODE="$2"; shift ;;
        --single-machine) SINGLE_MACHINE_MODE=true ;;
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

# Validate single-machine mode usage
if [ "$SINGLE_MACHINE_MODE" = true ] && [ "$CURRENT_MODE" == "Monolithic" ]; then
    echo "❌ Error: --single-machine can not be used with --mode Monolithic"
    exit 1
fi

# Export single-machine mode for use in other scripts
export SINGLE_MACHINE_MODE

if [ "$SHUTDOWN_MODE" = true ]; then
    echo "Shutdown mode enabled. Stopping gNB and exiting."
    reset_all
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
echo "  ⏱️  TEST_DURATION: $(($TEST_DURATION / 60))min"
echo "  🔢 Total test combinations: $TOTAL_TESTS"
echo "  🔄 Total iterations: $TOTAL_ITERATIONS"
echo "  ⏱️  Estimated duration: ${ESTIMATED_HOURS}h ${ESTIMATED_MINUTES}m"

# Get current date and next day
CURRENT_DATE=$(date +"%Y%m%d")
CURRENT_HOUR=$(date +"%H")
NEXT_DATE=$(date -d "tomorrow" +"%Y%m%d")

# Create directory name based on mode, bandwidth range, duration, and hour
TEST_DURATION_MIN=$((TEST_DURATION / 60))
if [ "$TEST_DURATION_MIN" -eq 0 ]; then
    DIR_NAME="${CURRENT_DATE}-${CURRENT_MODE}(${DL_START}-${DL_END}M)-${TEST_DURATION}sec-${CURRENT_HOUR}"
    if [ "$ENABLE_UL" = true ]; then
        DIR_NAME="${CURRENT_DATE}-${CURRENT_MODE}(${DL_START}-${DL_END}M)-UL(${UL_START}-${UL_END}M)-${TEST_DURATION}sec-${CURRENT_HOUR}"
    fi
else
    DIR_NAME="${CURRENT_DATE}-${CURRENT_MODE}(${DL_START}-${DL_END}M)-${TEST_DURATION_MIN}min-${CURRENT_HOUR}"
    if [ "$ENABLE_UL" = true ]; then
        DIR_NAME="${CURRENT_DATE}-${CURRENT_MODE}(${DL_START}-${DL_END}M)-UL(${UL_START}-${UL_END}M)-${TEST_DURATION_MIN}min-${CURRENT_HOUR}"
    fi
fi

# Check if estimated end time would be tomorrow
CURRENT_TIMESTAMP=$(date +%s)
ESTIMATED_END_TIMESTAMP=$((CURRENT_TIMESTAMP + ESTIMATED_TIME))
ESTIMATED_END_DATE=$(date -d "@$ESTIMATED_END_TIMESTAMP" +"%Y%m%d")
ESTIMATED_END_HOUR=$(date -d "@$ESTIMATED_END_TIMESTAMP" +"%H")

# Create appropriate directory
if [ "$ESTIMATED_END_DATE" != "$CURRENT_DATE" ]; then
    echo "⚠️  Warning: Tests will likely continue into tomorrow"
    echo "Creating directories for both today and tomorrow"
    mkdir -p "./data/${DIR_NAME}"
    if [ "$TEST_DURATION_MIN" -eq 0 ]; then
        NEXT_DIR_NAME="${NEXT_DATE}-${CURRENT_MODE}(${DL_START}-${DL_END}M)-${TEST_DURATION}sec-${ESTIMATED_END_HOUR}"
        if [ "$ENABLE_UL" = true ]; then
            NEXT_DIR_NAME="${NEXT_DATE}-${CURRENT_MODE}(${DL_START}-${DL_END}M)-UL(${UL_START}-${UL_END}M)-${TEST_DURATION}sec-${ESTIMATED_END_HOUR}"
        fi
    else
        NEXT_DIR_NAME="${NEXT_DATE}-${CURRENT_MODE}(${DL_START}-${DL_END}M)-${TEST_DURATION_MIN}min-${ESTIMATED_END_HOUR}"
        if [ "$ENABLE_UL" = true ]; then
            NEXT_DIR_NAME="${NEXT_DATE}-${CURRENT_MODE}(${DL_START}-${DL_END}M)-UL(${UL_START}-${UL_END}M)-${TEST_DURATION_MIN}min-${ESTIMATED_END_HOUR}"
        fi
    fi
    mkdir -p "./data/${NEXT_DIR_NAME}"
else
    mkdir -p "./data/${DIR_NAME}"
fi

echo "🔎 Current status:"
# echo "  🛠️  MANUAL_MODE_ENABLED = $([ "$MANUAL_MODE_ENABLED" = true ] && echo '✅' || echo '❌')"
echo "  🎛️  CURRENT_MODE        = $CURRENT_MODE"
echo "  🖥️  SINGLE_MACHINE_MODE = $([ "$SINGLE_MACHINE_MODE" = true ] && echo '✅' || echo '❌')"
echo "  📦 TEST_UDP            = $([ "$TEST_UDP" = true ] && echo '✅' || echo '❌')"
echo "  📦 TEST_TCP            = $([ "$TEST_TCP" = true ] && echo '✅' || echo '❌')"
echo "  ⬆️  ENABLE_UL           = $([ "$ENABLE_UL" = true ] && echo '✅' || echo '❌')"
echo "  ⬇️  DL Range            = ${DL_START}-${DL_END}M (step: ${DL_STEP}M)"
if [ "$ENABLE_UL" = true ]; then
    echo "  ⬆️  UL_START            = $UL_START"
    echo "  ⬆️  UL_END              = $UL_END"
    echo "  ⬆️  UL_STEP             = $UL_STEP"
fi

if [ "$MANUAL_MODE_ENABLED" = true ]; then
    if [ "$PASS" = false ]; then
        reset_all
        start_gNB "$CURRENT_MODE"
    fi
    wait_for_ue_parameters
    
    # Generate test environment report after gNB is ready
    generate_test_report "./data/${DIR_NAME}" "$CURRENT_MODE"
    
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
    reset_all
    start_gNB "$CURRENT_MODE"
    sleep 60
    
    # Check for gNB crash before proceeding
    if check_gnb_crash; then
        echo "❌ gNB crash detected during startup!"
        backup_crash_logs "./data/${DIR_NAME}" "$CURRENT_MODE"
        # exit 1
    fi
    
    # Generate test environment report after gNB is ready but before UE connection
    generate_test_report "./data/${DIR_NAME}" "$CURRENT_MODE"
    
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
        
        # Check for gNB crash during UE connection attempts
        if check_gnb_crash; then
            echo "❌ gNB crash detected during UE connection attempt!"
            backup_crash_logs "./data/${DIR_NAME}" "$CURRENT_MODE"
            # exit 1
        fi
        
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
            reset_all
            exit 1
        fi
        
        echo "Retrying..."
        sleep 5
    done
fi

sleep 1

# Global variables for monitoring
UE_MONITOR_PID=""
RESTART_FLAG_FILE="/tmp/e2e_restart_flag"

# Function to monitor UE IP status in background
monitor_ue_connection() {
    local check_interval=30  # Check every 30 seconds
    local max_failures=3     # Allow 3 consecutive failures before declaring crash
    local failure_count=0
    
    echo "🔍 Starting UE connection monitor (PID: $$)"
    
    while true; do
        sleep $check_interval
        
        # Try to get UE IP
        local current_ue_ip=""
        current_ue_ip=$(sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTIONS $CONTROL_PC_USER@$CONTROL_PC_IP \
                       "adb -s $ADB_DEVICE shell ip -f inet addr show" | awk '/inet/ && !/127\.0\.0\.1/ {print $2}' | cut -d/ -f1 | head -n1 2>/dev/null)
        
        if [ -z "$current_ue_ip" ]; then
            failure_count=$((failure_count + 1))
            echo "⚠️  UE IP check failed (attempt $failure_count/$max_failures)"
            
            if [ $failure_count -ge $max_failures ]; then
                echo "🚨 UE connection lost! Environment problem detected."
                echo "📝 Creating restart flag file..."
                echo "UE_CONNECTION_LOST" > "$RESTART_FLAG_FILE"
                break
            fi
        else
            # Reset failure count on successful check
            if [ $failure_count -gt 0 ]; then
                echo "✅ UE connection restored: $current_ue_ip"
            fi
            failure_count=0
        fi
    done
}

# Function to start UE monitoring in background
start_ue_monitoring() {
    if [ -n "$UE_MONITOR_PID" ]; then
        echo "UE monitoring already running (PID: $UE_MONITOR_PID)"
        return
    fi
    
    # Remove any existing restart flag
    rm -f "$RESTART_FLAG_FILE"
    
    # Start monitoring in background
    monitor_ue_connection &
    UE_MONITOR_PID=$!
    echo "🚀 Started UE monitoring (PID: $UE_MONITOR_PID)"
}

# Function to stop UE monitoring
stop_ue_monitoring() {
    if [ -n "$UE_MONITOR_PID" ]; then
        echo "🛑 Stopping UE monitoring (PID: $UE_MONITOR_PID)"
        kill $UE_MONITOR_PID 2>/dev/null || true
        UE_MONITOR_PID=""
    fi
}

# Function to check for restart flag and handle restart
check_restart_flag() {
    if [ -f "$RESTART_FLAG_FILE" ]; then
        local restart_reason=$(cat "$RESTART_FLAG_FILE")
        echo "🔄 Restart flag detected: $restart_reason"
        
        # Stop monitoring
        stop_ue_monitoring
        
        # Backup crash logs
        echo "📦 Backing up crash logs due to: $restart_reason"
        backup_crash_logs "./data/${DIR_NAME}" "$CURRENT_MODE"
        
        # Reset environment
        echo "🔧 Resetting environment..."
        reset_all
        
        # Clean up restart flag
        rm -f "$RESTART_FLAG_FILE"
        
        # Restart script with same parameters
        echo "🚀 Restarting script with same parameters..."
        exec "$0" "$@"
    fi
}

# Function to periodically check restart flag during tests
periodic_restart_check() {
    local check_interval=10  # Check every 10 seconds during tests
    
    while true; do
        sleep $check_interval
        check_restart_flag "$@"
    done
}

# Add this after UE connection is established and before starting tests
if [ "$MANUAL_MODE_ENABLED" = false ]; then
    # Start UE monitoring after successful connection
    start_ue_monitoring
    
    # Start periodic restart checking in background
    periodic_restart_check "$@" &
    RESTART_CHECK_PID=$!
fi

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
        
        # Check restart flag before starting protocol tests
        check_restart_flag "$@"
        
        # Check if UE_IP exists and is not empty, if not get it
        [ -z "$UE_IP" ] && get_ue_ip
        ping-start $UE_IP
        sleep $SLEEP_WINDOW
        ping-stop "./data/${DIR_NAME}/ping-${direction}-${protocol}-idle.log"

        for bw in $(seq $start $step $end); do
            echo "Testing ${dir_name} ${protocol} at ${bw}M"
            
            # Check restart flag before each bandwidth test
            check_restart_flag "$@"
            
            # Check for gNB crash before each test
            if check_gnb_crash; then
                echo "❌ gNB crash detected during testing!"
                backup_crash_logs "./data/${DIR_NAME}" "$CURRENT_MODE"
                # Create restart flag for gNB crash
                echo "GNB_CRASH" > "$RESTART_FLAG_FILE"
                check_restart_flag "$@"
            fi

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

# Stop monitoring when tests complete successfully
stop_ue_monitoring
if [ -n "$RESTART_CHECK_PID" ]; then
    kill $RESTART_CHECK_PID 2>/dev/null || true
fi

# Capture the measure file path from process_and_fetch_measurement
run_analysis_suite "$(process_and_fetch_measurement $CURRENT_MODE)" "./data/${DIR_NAME}"

sleep 5
reset_all
sleep 5

# toggle_airplane_mode "on"

# Signal handling for clean shutdown
cleanup_and_exit() {
    echo "🛑 Received termination signal. Cleaning up..."
    stop_ue_monitoring
    if [ -n "$RESTART_CHECK_PID" ]; then
        kill $RESTART_CHECK_PID 2>/dev/null || true
    fi
    rm -f "$RESTART_FLAG_FILE"
    reset_all
    exit 1
}

# Set up signal traps
trap cleanup_and_exit SIGINT SIGTERM