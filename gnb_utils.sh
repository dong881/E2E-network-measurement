#!/bin/bash

# Global variables
source variable.sh

# Commands for Single Machine Setup
# Define common paths and options
BUILD_DIR="cmake_targets/ran_build/build"
CONF_DIR="$PNF_BASE_PATH/targets/PROJECTS/GENERIC-NR-5GC/CONF"

# Common options
SUDO_PREFIX="echo '$SERVER_PASSWORD' | sudo -S"
THREAD_OPTS="--thread-pool 1,3,5,7,9,11,13,15"
NFAPI_TRACE="NFAPI_TRACE_LEVEL=info"
COMMON_CMD="cd $PNF_BASE_PATH/$BUILD_DIR && $SUDO_PREFIX"

# Mode-specific options
VNF_OPTS="--nfapi VNF"
PNF_OPTS="--nfapi PNF --reorder-thread-disable 1 $THREAD_OPTS"
MONO_OPTS="$THREAD_OPTS"

# Config files
CONF_VNF_100M="gnb-vnf.sa.band78.273prb.nfapi.conf"
CONF_VNF_40M="gnb-vnf.sa.band78.106prb.nfapi.conf"
CONF_MONO_100M="gnb.sa.band78.273prb.fhi72.4x4-liteon_new.conf"
CONF_MONO_100M_JURA="gnb.sa.band78.273prb.fhi72.4x4-metanoia.conf"
CONF_MONO_40M="gnb.sa.band78.106prb.fhi72.4x4-liteon_new.conf"
CONF_PNF="gnb-pnf.band78.fhi72.4x4-liteon_new.conf"
# CONF_PNF="gnb-pnf.sa.band78.fhi72.nfapi.4x4-metanoia.conf"

# Commands for Single Machine Setup
CMD_VNF_100M_SINGLE="$COMMON_CMD $NFAPI_TRACE ./nr-softmodem -O $CONF_DIR/$CONF_VNF_100M $VNF_OPTS"
CMD_VNF_40M_SINGLE="$COMMON_CMD $NFAPI_TRACE ./nr-softmodem -O $CONF_DIR/$CONF_VNF_40M $VNF_OPTS"
CMD_MONO_100M_SINGLE="$COMMON_CMD ./nr-softmodem -O $CONF_DIR/$CONF_MONO_100M $MONO_OPTS"
CMD_MONO_40M_SINGLE="$COMMON_CMD ./nr-softmodem -O $CONF_DIR/$CONF_MONO_40M $MONO_OPTS"
CMD_MONO_100M_JURA_SINGLE="$COMMON_CMD ./nr-softmodem -O $CONF_DIR/$CONF_MONO_100M_JURA $MONO_OPTS"
CMD_PNF_SINGLE="$COMMON_CMD $NFAPI_TRACE ./nr-softmodem -O $CONF_DIR/$CONF_PNF $PNF_OPTS"

# Additional config files
CONF_PNF_SPLIT="gnb-pnf.sa.band78.fhi72.nfapi.4x4-metanoia.conf"

# Common command prefixes for split setup
VNF_SPLIT_CMD_PREFIX="cd $VNF_BASE_PATH/$BUILD_DIR && echo '$SERVER_PASSWORD' | sudo -S $NFAPI_TRACE"
PNF_SPLIT_CMD_PREFIX="cd $PNF_BASE_PATH/$BUILD_DIR && echo '$SERVER_PASSWORD' | sudo -S $NFAPI_TRACE"

# Commands for Split Machine Setup (Two Machines)
CMD_VNF_100M_SPLIT="$VNF_SPLIT_CMD_PREFIX ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/$CONF_VNF_100M $VNF_OPTS"
CMD_VNF_40M_SPLIT="$VNF_SPLIT_CMD_PREFIX ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/$CONF_VNF_40M $VNF_OPTS"
CMD_PNF_SPLIT="$PNF_SPLIT_CMD_PREFIX ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/$CONF_PNF_SPLIT $PNF_OPTS"



# Function to start a screen session
start_session() {
    local session_name=$1
    local command=$2
    local target_user=$3
    local target_host=$4
    
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $target_user@$target_host "screen -dmS $session_name bash -c '$command &> $GNB_LOG_FILE'"
}

# Function to stop a screen session
stop_session() {
    local session_name=$1
    local target_user=$2
    local target_host=$3
    
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $target_user@$target_host "screen -X -S $session_name quit" &>/dev/null
}

# Function to wait for UE parameters in log file
wait_for_ue_parameters() {
    local target_user=${1:-$GNB_SERVER_USER}
    local target_host=${2:-$GNB_SERVER_HOST}
    local search_pattern="Command line parameters for OAI UE:"
    
    echo "Waiting for gNB to fully start up and be ready for UE connection on $target_user@$target_host..."
    
    while true; do
        # Check if the pattern exists in the log file
        if sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $target_user@$target_host "grep -q '$search_pattern' $GNB_LOG_FILE 2>/dev/null"; then
            return 1
        fi
        
        # Wait 2 seconds before checking again
        sleep 2
    done
}

# Function to start split machine setup
start_split_setup() {
    local bandwidth=$1  # 100M or 40M
    
    if [ "$bandwidth" = "100M" ]; then
        start_session "VNF_100M" "$CMD_VNF_100M_SPLIT" "$VNF_GNB_SERVER_USER" "$VNF_GNB_SERVER_HOST"
        start_session "PNF" "$CMD_PNF_SPLIT" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
    elif [ "$bandwidth" = "40M" ]; then
        start_session "VNF_40M" "$CMD_VNF_40M_SPLIT" "$VNF_GNB_SERVER_USER" "$VNF_GNB_SERVER_HOST"
        start_session "PNF" "$CMD_PNF_SPLIT" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
    fi
}

# Function to start single machine setup
start_single_setup() {
    local bandwidth=$1  # 100M or 40M
    local mode=$2      # NFAPI or Monolithic
    
    if [ "$bandwidth" = "100M" ]; then
        if [ "$mode" = "Monolithic" ]; then
            # start_session "MONO_100M" "$CMD_MONO_100M_SINGLE" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
            start_session "MONO_100M" "$CMD_MONO_100M_JURA_SINGLE" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
        else
            start_session "VNF_100M" "$CMD_VNF_100M_SINGLE" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
            start_session "PNF" "$CMD_PNF_SINGLE" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
        fi
    elif [ "$bandwidth" = "40M" ]; then
        if [ "$mode" = "Monolithic" ]; then
            start_session "MONO_40M" "$CMD_MONO_40M_SINGLE" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
        else
            start_session "VNF_40M" "$CMD_VNF_40M_SINGLE" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
            start_session "PNF" "$CMD_PNF_SINGLE" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
        fi
    fi
}

### ------------------------------------------------------------------------------------------------

# Example usage of all possible function combinations

# Split machine setup (VNF + PNF)
# start_split_setup "100M"    # 100M bandwidth
# start_split_setup "40M"     # 40M bandwidth

# Single machine setup (NFAPI mode)
# start_single_setup "100M" "NFAPI"    # 100M bandwidth
# start_single_setup "40M" "NFAPI"     # 40M bandwidth

# Single machine setup (Monolithic mode)
# start_single_setup "100M" "Monolithic"    # 100M bandwidth
# start_single_setup "40M" "Monolithic"     # 40M bandwidth

# Stop sessions
# Function to stop split machine setup
stop_split_setup() {
    local bandwidth=$1  # 100M or 40M
    
    if [ "$bandwidth" = "100M" ]; then
        stop_session "VNF_100M" "$VNF_GNB_SERVER_USER" "$VNF_GNB_SERVER_HOST"
        stop_session "PNF" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
    elif [ "$bandwidth" = "40M" ]; then
        stop_session "VNF_40M" "$VNF_GNB_SERVER_USER" "$VNF_GNB_SERVER_HOST"
        stop_session "PNF" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
    fi
}

# Function to stop single machine setup
stop_single_setup() {
    local bandwidth=$1  # 100M or 40M
    local mode=$2      # NFAPI or Monolithic
    
    if [ "$bandwidth" = "100M" ]; then
        if [ "$mode" = "Monolithic" ]; then
            stop_session "MONO_100M" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
        else
            stop_session "VNF_100M" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
            stop_session "PNF" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
        fi
    elif [ "$bandwidth" = "40M" ]; then
        if [ "$mode" = "Monolithic" ]; then
            stop_session "MONO_40M" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
        else
            stop_session "VNF_40M" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
            stop_session "PNF" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
        fi
    fi
}

start_gNB() {
    local mode=${1:-$CURRENT_MODE}  # Use provided mode or default to CURRENT_MODE
    if [ "$mode" = "Monolithic" ]; then
        start_single_setup "100M" "Monolithic"
    else
        start_split_setup "100M"
    fi
}

stop_gNB() {
    local mode=${1:-$CURRENT_MODE}  # Use provided mode or default to CURRENT_MODE
    if [ "$mode" = "Monolithic" ]; then
        stop_single_setup "100M" "Monolithic"
    else
        stop_split_setup "100M"
    fi
}

# Function to fetch log files and analyze them
fetch_and_analyze_logs() {
    local mode=$1  # "Monolithic" or "NFAPI"

    # Create measurement directory if it doesn't exist
    mkdir -p $LOCAL_MEASURE_DIR
    
    if [ "$mode" = "Monolithic" ]; then
        # For Monolithic mode
        local vnf_remote_log="$PNF_BASE_PATH/$BUILD_DIR/$VNF_LOG_FILE"
        local pnf_remote_log="$PNF_BASE_PATH/$BUILD_DIR/$PNF_LOG_FILE"
        local vnf_local_log="$LOCAL_MEASURE_DIR/monolithic-$VNF_LOG_FILE"
        local pnf_local_log="$LOCAL_MEASURE_DIR/monolithic-$PNF_LOG_FILE"
        
        echo "Fetching VNF logs from $GNB_SERVER_USER@$GNB_SERVER_HOST..."
        sshpass -p "$SERVER_PASSWORD" scp $SSH_OPTIONS "$GNB_SERVER_USER@$GNB_SERVER_HOST:$vnf_remote_log" "$vnf_local_log"
        
        echo "Fetching PVNF logs from $GNB_SERVER_USER@$GNB_SERVER_HOST..."
        sshpass -p "$SERVER_PASSWORD" scp $SSH_OPTIONS "$GNB_SERVER_USER@$GNB_SERVER_HOST:$pnf_remote_log" "$pnf_local_log"

        if [ -f "$vnf_local_log" ] && [ -f "$pnf_local_log" ]; then
            echo "Successfully copied VNF and PNF logs"
            python $LOG_ANALYSIS_SCRIPT "$vnf_local_log" "$pnf_local_log"
        else
            echo "Failed to copy one or more log files"
        fi
    else
        # For NFAPI mode (need both VNF and PNF logs)
        local vnf_remote_log="$VNF_BASE_PATH/$BUILD_DIR/$VNF_LOG_FILE"
        local pnf_remote_log="$PNF_BASE_PATH/$BUILD_DIR/$PNF_LOG_FILE"
        local vnf_local_log="$LOCAL_MEASURE_DIR/nfapi-$VNF_LOG_FILE"
        local pnf_local_log="$LOCAL_MEASURE_DIR/nfapi-$PNF_LOG_FILE"
        
        echo "Fetching VNF logs from $VNF_GNB_SERVER_USER@$VNF_GNB_SERVER_HOST..."
        sshpass -p "$SERVER_PASSWORD" scp $SSH_OPTIONS "$VNF_GNB_SERVER_USER@$VNF_GNB_SERVER_HOST:$vnf_remote_log" "$vnf_local_log"
        
        echo "Fetching PNF logs from $GNB_SERVER_USER@$GNB_SERVER_HOST..."
        sshpass -p "$SERVER_PASSWORD" scp $SSH_OPTIONS "$GNB_SERVER_USER@$GNB_SERVER_HOST:$pnf_remote_log" "$pnf_local_log"
        
        if [ -f "$vnf_local_log" ] && [ -f "$pnf_local_log" ]; then
            echo "Successfully copied VNF and PNF logs"
            python $LOG_ANALYSIS_SCRIPT "$vnf_local_log" "$pnf_local_log"
        else
            echo "Failed to copy one or more log files"
        fi
    fi
}

# Function to clean log files on servers
clean_log_files() {
    local mode=$1  # "Monolithic" or "NFAPI"    
    if [ "$mode" = "Monolithic" ]; then
        # For Monolithic mode, both logs are on the same server
        local vnf_remote_log="$VNF_BASE_PATH/$BUILD_DIR/$VNF_LOG_FILE"
        local pnf_remote_log="$VNF_BASE_PATH/$BUILD_DIR/$PNF_LOG_FILE"
        
        # Execute with a direct command string that handles the password prompt
        sshpass -p "$SERVER_PASSWORD" ssh -t -o StrictHostKeyChecking=no $GNB_SERVER_USER@$GNB_SERVER_HOST "echo $SERVER_PASSWORD | sudo -S rm -f $vnf_remote_log $pnf_remote_log" &>/dev/null
        
    else
        # For NFAPI mode, logs are on different servers
        local vnf_remote_log="$VNF_BASE_PATH/$BUILD_DIR/$VNF_LOG_FILE"
        local pnf_remote_log="$PNF_BASE_PATH/$BUILD_DIR/$PNF_LOG_FILE"
        
        # Adding -t option to allocate a pseudo-terminal
        sshpass -p "$SERVER_PASSWORD" ssh -t -o StrictHostKeyChecking=no $VNF_GNB_SERVER_USER@$VNF_GNB_SERVER_HOST "echo $SERVER_PASSWORD | sudo -S rm -f $vnf_remote_log" &>/dev/null
        
        # Adding -t option to allocate a pseudo-terminal
        sshpass -p "$SERVER_PASSWORD" ssh -t -o StrictHostKeyChecking=no $GNB_SERVER_USER@$GNB_SERVER_HOST "echo $SERVER_PASSWORD | sudo -S rm -f $pnf_remote_log" &>/dev/null
    fi
}

# Function to reset all states and prepare for a clean start
reset_all() {

    stop_gNB "Monolithic"
    stop_gNB "NFAPI"
    clean_log_files "Monolithic"
    clean_log_files "NFAPI"
    clean_measurement_file

    # Stop sessions on CN server
    if [ -n "$CN_SERVER_USER" ] && [ -n "$CN_SERVER_HOST" ]; then
        sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$CN_SERVER_USER@$CN_SERVER_HOST" \
            "screen -X -S iperf-server quit 2>/dev/null || true" &>/dev/null
        sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$CN_SERVER_USER@$CN_SERVER_HOST" \
            "screen -X -S ping-session quit 2>/dev/null || true" &>/dev/null
    else
        echo "CN server information not set, skipping CN server reset."
    fi
    
    # Execute remote script on main host if needed
    if [ -n "$GNB_SERVER_USER" ] && [ -n "$GNB_SERVER_HOST" ]; then
        # sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $GNB_SERVER_USER@$GNB_SERVER_HOST \
        #     "screen -dmS oaiLONvf bash -c 'echo $SERVER_PASSWORD | sudo -S /oai72/Script/oaiLONvf.sh 2>/dev/null || true'"
        sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $GNB_SERVER_USER@$GNB_SERVER_HOST \
            "screen -dmS oaiLONvf bash -c 'echo $SERVER_PASSWORD | sudo -S source /home/oai72_su/juravf_demo.sh || true'" &>/dev/null
    else
        echo "gNB server information not set, skipping remote script execution."
    fi
    
    # Optional: Set RU bandwidth
    # if type radio_unit_utils &>/dev/null; then
    #     echo "Setting RU bandwidth to 100M..."
    #     radio_unit_utils "100000000"
    # fi

    # Optional: Reset Jura RU configuration
    source smo.sh
    configure_jura_ru
    
    echo "Reset complete."
}

# Function to get git tag from remote server
get_git_tag() {
    local user=$1
    local host=$2
    local path=$3
    
    # First check if the path exists and is a git repository
    local git_check=$(sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$user@$host" "
        if [ -d $path ]; then
            cd $path
            if [ -d '.git' ] || git rev-parse --git-dir >/dev/null 2>&1; then
                git describe --tags --always 2>/dev/null || git rev-parse --short HEAD 2>/dev/null || echo 'No git info'
            else
                echo 'Not a git repository'
            fi
        else
            echo 'Path not found'
        fi
    " 2>/dev/null)
    
    echo "${git_check:-Unknown}"
}

# Function to detect FH version and path
detect_fh_version() {
    local user=${1:-$GNB_SERVER_USER}
    local host=${2:-$GNB_SERVER_HOST}
    
    # Check if gNB log exists and extract FH version info in a single remote command
    local remote_result=$(sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$user@$host" "
        log_file=$GNB_LOG_FILE
        if [ ! -f \$log_file ]; then
            echo \"Unknown|Unknown|No logs file|\"
            exit 0
        fi
        
        # Extract FH version info - handle both f_release and e_maintenance_release patterns
        fh_info=\$(grep -o -E \"(oran_[ef]_.*release_v[0-9]+\\.[0-9]+[^[:space:][:punct:]]*|oran_e_maintenance_release_v[0-9]+\\.[0-9]+-[0-9]+-g[a-f0-9]+)\" \"\$log_file\" 2>/dev/null | head -1 || echo \"Unknown\")
        
        # Clean up any trailing punctuation from fh_info
        fh_info=\$(echo \"\$fh_info\" | sed 's/[[:punct:]]*\$//')
        
        # Determine version type by checking log content
        version_type=\"Unknown\"
        fh_path=\"\"
        
        # Check for O-RAN FH interface initialization message first
        if grep -q \"Initializing O-RAN 7.2 FH interface through xran library\" \"\$log_file\" 2>/dev/null; then
            # Extract version from either oran_f_release or oran_e_maintenance_release patterns
            oran_version=\$(grep -o -E \"(oran_[ef]_.*release_v[0-9]+\\.[0-9]+|oran_e_maintenance_release_v[0-9]+\\.[0-9]+-[0-9]+-g[a-f0-9]+)\" \"\$log_file\" 2>/dev/null | head -1)
            
            # Parse version information flexibly
            if [[ \"\$oran_version\" =~ oran_e_maintenance_release_v([0-9]+)\\.([0-9]+) ]] || [[ \"\$oran_version\" =~ oran_e_.*release_v([0-9]+)\\.([0-9]+) ]]; then
                # E release versions
                version_type=\"E\"
                fh_path=\"~/oai_mp_f_ming/phy_e\"
            elif [[ \"\$oran_version\" =~ oran_f_release_v([0-9]+)\\.([0-9]+) ]]; then
                # F release versions
                major_version=\${BASH_REMATCH[1]}
                minor_version=\${BASH_REMATCH[2]}
                
                # Version mapping logic - easily extensible for future versions
                if [ \"\$major_version\" -eq 1 ] && [ \"\$minor_version\" -le 3 ]; then
                    version_type=\"E\"
                    fh_path=\"~/oai_mp_f_ming/phy_e\"
                else
                    # Default to F for v1.4+ and v2.0+
                    version_type=\"F\"
                    fh_path=\"~/oai_mp_f_ming/phy\"
                fi
            else
                # Default fallback when version parsing fails
                version_type=\"F\"
                fh_path=\"~/oai_mp_f_ming/phy\"
            fi
        else
            # Fallback to directory existence check
            if [ -d ~/oai_mp_f_ming/phy_e ]; then
                version_type=\"E\"
                fh_path=\"~/oai_mp_f_ming/phy_e\"
            elif [ -d ~/oai_mp_f_ming/phy ]; then
                version_type=\"F\"
                fh_path=\"~/oai_mp_f_ming/phy\"
            fi
        fi
        
        # Get FH git tag if path exists
        fh_tag=\"No tags found\"
        if [ -n \"\$fh_path\" ]; then
            # Expand tilde and check if directory exists
            expanded_path=\$(eval echo \"\$fh_path\")
            if [ -d \"\$expanded_path\" ]; then
                fh_tag=\$(cd \"\$expanded_path\" && git describe --tags --always 2>/dev/null || echo \"No tags found\")
            fi
        fi
        
        echo \"\$version_type|\$fh_info|\$fh_tag|\$fh_path\"
    " 2>/dev/null)
    
    echo "$remote_result"
}

# Function to check if gNB has crashed
check_gnb_crash() {
    local user=${1:-$GNB_SERVER_USER}
    local host=${2:-$GNB_SERVER_HOST}
    
    # Check for common crash indicators in the log
    local crash_patterns=(
        "Segmentation fault"
        "segfault"
        "Aborted"
        "FATAL"
        "ERROR.*crash"
        "core dumped"
        "terminate called"
    )
    
    for pattern in "${crash_patterns[@]}"; do
        if sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$user@$host" "grep -i '$pattern' $GNB_LOG_FILE 2>/dev/null" >/dev/null; then
            return 0  # Crash detected
        fi
    done
    
    return 1  # No crash detected
}

# Function to backup crash logs
backup_crash_logs() {
    local test_dir=$1
    local mode=${2:-$CURRENT_MODE}
    
    echo "🚨 gNB crash detected! Backing up logs..."
    
    # Create crash backup directory
    local crash_dir="$test_dir/crash_logs_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$crash_dir"
    
    # Backup main gNB log
    echo "Backing up main gNB log..."
    sshpass -p "$SERVER_PASSWORD" scp $SSH_OPTIONS "$GNB_SERVER_USER@$GNB_SERVER_HOST:$GNB_LOG_FILE" "$crash_dir/gnb_crash.log" 2>/dev/null || echo "Failed to backup main gNB log"
    
    if [ "$mode" = "Monolithic" ]; then
        # Backup monolithic logs
        local vnf_log="$PNF_BASE_PATH/$BUILD_DIR/$VNF_LOG_FILE"
        local pnf_log="$PNF_BASE_PATH/$BUILD_DIR/$PNF_LOG_FILE"
        
        echo "Backing up monolithic VNF log..."
        sshpass -p "$SERVER_PASSWORD" scp $SSH_OPTIONS "$GNB_SERVER_USER@$GNB_SERVER_HOST:$vnf_log" "$crash_dir/mono_vnf_crash.log" 2>/dev/null || echo "Failed to backup monolithic VNF log"
        
        echo "Backing up monolithic PNF log..."
        sshpass -p "$SERVER_PASSWORD" scp $SSH_OPTIONS "$GNB_SERVER_USER@$GNB_SERVER_HOST:$pnf_log" "$crash_dir/mono_pnf_crash.log" 2>/dev/null || echo "Failed to backup monolithic PNF log"
    else
        # Backup VNF and PNF logs for NFAPI mode
        local vnf_log="$VNF_BASE_PATH/$BUILD_DIR/$VNF_LOG_FILE"
        local pnf_log="$PNF_BASE_PATH/$BUILD_DIR/$PNF_LOG_FILE"
        
        echo "Backing up VNF log..."
        sshpass -p "$SERVER_PASSWORD" scp $SSH_OPTIONS "$VNF_GNB_SERVER_USER@$VNF_GNB_SERVER_HOST:$vnf_log" "$crash_dir/vnf_crash.log" 2>/dev/null || echo "Failed to backup VNF log"
        
        echo "Backing up PNF log..."
        sshpass -p "$SERVER_PASSWORD" scp $SSH_OPTIONS "$GNB_SERVER_USER@$GNB_SERVER_HOST:$pnf_log" "$crash_dir/pnf_crash.log" 2>/dev/null || echo "Failed to backup PNF log"
    fi
    
    echo "Crash logs backed up to: $crash_dir"
}

# Function to generate comprehensive test environment report
generate_test_report() {
    local test_dir=$1
    local mode=${2:-$CURRENT_MODE}
    
    # echo "📋 Generating test environment report..."
    
    local report_file="$test_dir/environment_report.md"
    local current_time=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Get gNB version information
    local vnf_tag="Unknown"
    local gnb_tag="Unknown"
    if [ "$mode" = "Monolithic" ]; then
        gnb_tag=$(get_git_tag "$GNB_SERVER_USER" "$GNB_SERVER_HOST" "$PNF_BASE_PATH")
    else
        vnf_tag=$(get_git_tag "$VNF_GNB_SERVER_USER" "$VNF_GNB_SERVER_HOST" "$VNF_BASE_PATH")
        gnb_tag=$(get_git_tag "$GNB_SERVER_USER" "$GNB_SERVER_HOST" "$PNF_BASE_PATH")
    fi
    
    # Get FH version information
    local fh_info=$(detect_fh_version)
    IFS='|' read -r fh_version fh_release fh_tag fh_path <<< "$fh_info"
    
    # Calculate test parameters
    local dl_steps=$(( (DL_END - DL_START) / DL_STEP + 1 ))
    local ul_steps=0
    [ "$ENABLE_UL" = true ] && ul_steps=$(( (UL_END - UL_START) / UL_STEP + 1 ))
    
    local total_tests=0
    [ "$TEST_UDP" = true ] && total_tests=$((total_tests + 1))
    [ "$TEST_TCP" = true ] && total_tests=$((total_tests + 1))
    [ "$ENABLE_UL" = true ] && total_tests=$((total_tests * 2))
    
    local total_iterations=$((total_tests * (dl_steps + ul_steps)))
    local estimated_time=$((total_iterations * (TEST_DURATION + 3 * SLEEP_WINDOW + 2)))
    local estimated_hours=$((estimated_time / 3600))
    local estimated_minutes=$(( (estimated_time % 3600) / 60 ))
    
    # Generate the report
    cat > "$report_file" << EOF
# Test Environment Report

**Generated:** $current_time  
**Test Mode:** $mode  
## 📊 Test Configuration

### Test Parameters
- **Protocols:** $([ "$TEST_UDP" = true ] && echo "UDP " || echo "")$([ "$TEST_TCP" = true ] && echo "TCP" || echo "")
- **Downlink Range:** ${DL_START}M - ${DL_END}M (Step: ${DL_STEP}M)
$([ "$ENABLE_UL" = true ] && echo "- **Uplink Range:** ${UL_START}M - ${UL_END}M (Step: ${UL_STEP}M)" || echo "- **Uplink:** Disabled")
- **Sleep Window:** $SLEEP_WINDOW seconds

## 🏗️ Software Versions

### gNB Software
- **Mode:** $mode
$([ "$mode" != "Monolithic" ] && echo "- **VNF Version Tag:** $vnf_tag
- **PNF Version Tag:** $gnb_tag" || echo "- **gNB Version Tag:** $gnb_tag")

### Fronthaul (FH) Information
- **FH Version Type:** $fh_version Release
- **FH Library Version:** $fh_release
- **FH Git Tag:** $fh_tag
- **FH Path:** $fh_path

## 🔧 System Configuration

### Network Infrastructure
- **Core Network Server:** $CN_SERVER_USER@$CN_SERVER_HOST
- **gNB Server:** $GNB_SERVER_USER@$GNB_SERVER_HOST
- **Test Server IP:** $TEST_SERVER_IP
- **Network Interface:** $INTERFACE

$([ "$mode" != "Monolithic" ] && echo "### NFAPI Split Configuration
- **VNF Server:** $VNF_GNB_SERVER_USER@$VNF_GNB_SERVER_HOST
- **PNF Server:** $GNB_SERVER_USER@$GNB_SERVER_HOST
- **VNF Base Path:** $VNF_BASE_PATH
- **PNF Base Path:** $PNF_BASE_PATH")

*Report generated automatically by E2E Network Measurement System*
EOF

    echo "📋✅ Test environment report generated: $report_file"
}

# Example usage:
# clean_log_files "Monolithic"  # Clean log files in monolithic mode
# clean_log_files "NFAPI" # Clean log files in NFAPI mode

# Example usage:
# fetch_and_analyze_logs "Monolithic"  # For monolithic mode
# fetch_and_analyze_logs "NFAPI" # For NFAPI mode

# Split machine setup stop examples
# stop_split_setup "100M"    # Stop 100M bandwidth setup
# stop_split_setup "40M"     # Stop 40M bandwidth setup

# Single machine setup stop examples
# stop_single_setup "100M" "NFAPI"    # Stop 100M bandwidth NFAPI setup
# stop_single_setup "40M" "NFAPI"     # Stop 40M bandwidth NFAPI setup
# stop_single_setup "100M" "Monolithic"     # Stop 100M bandwidth Monolithic setup
# stop_single_setup "40M" "Monolithic"      # Stop 40M bandwidth Monolithic setup

# Function to clean measurement file on gNB server
clean_measurement_file() {
    local target_user=${1:-$GNB_SERVER_USER}
    local target_host=${2:-$GNB_SERVER_HOST}
    
    echo "Cleaning measurement file on $target_user@$target_host..."
    sshpass -p "$SERVER_PASSWORD" ssh -t -o StrictHostKeyChecking=no "$target_user@$target_host" \
        "echo $SERVER_PASSWORD | sudo -S rm -f $MEASURE_FILE_PATH" &>/dev/null
    
    # if [ $? -eq 0 ]; then
    #     echo "Successfully cleaned measurement file: $MEASURE_FILE_PATH"
    # else
    #     echo "Failed to clean measurement file: $MEASURE_FILE_PATH"
    # fi
}

# Function to process and fetch measurement file from gNB server
process_and_fetch_measurement() {
    local mode=${1:-$CURRENT_MODE}
    local target_user=${2:-$GNB_SERVER_USER}
    local target_host=${3:-$GNB_SERVER_HOST}
        
    # Execute reorganize_measure.py script remotely
    sshpass -p "$SERVER_PASSWORD" ssh -t -o StrictHostKeyChecking=no "$target_user@$target_host" \
        "echo $SERVER_PASSWORD | sudo -S python $REORGANIZE_SCRIPT_PATH" &>/dev/null
    
    if [ $? -ne 0 ]; then
        echo "Failed to execute reorganize_measure.py script"
        return 1
    fi
    
    # Expand LOCAL_MEASURE_DIR to handle ~ properly
    local expanded_measure_dir=$(eval echo $LOCAL_MEASURE_DIR)
    
    # Create the local directory if it doesn't exist
    mkdir -p "$expanded_measure_dir"
    
    # Define local filename with mode suffix
    local local_filename="$expanded_measure_dir/measure_filtered-${mode}-$(date +%Y%m%d).txt"

    sshpass -p "$SERVER_PASSWORD" scp $SSH_OPTIONS "$target_user@$target_host:$MEASURE_FILTERED_FILE_PATH" "$local_filename"
    
    if [ $? -eq 0 ]; then
        echo "Successfully fetched measurement file: $local_filename"
    else
        echo "Failed to fetch measurement file from $target_user@$target_host:$MEASURE_FILTERED_FILE_PATH"
        return 1
    fi
}

