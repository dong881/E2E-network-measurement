#!/bin/bash

# Global variables
source variable.sh

# Function to check and install sshpass if needed
check_sshpass_installed() {
    if ! command -v sshpass &> /dev/null; then
        echo "sshpass is not installed. Installing..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y sshpass
        elif command -v yum &> /dev/null; then
            sudo yum install -y sshpass
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y sshpass
        else
            echo "Error: Cannot install sshpass. Please install it manually."
            return 1
        fi
    fi
    return 0
}

# Check if sshpass is installed at script start
if ! check_sshpass_installed; then
    echo "Error: sshpass is required but could not be installed."
    exit 1
fi

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
# CONF_PNF="gnb-pnf.band78.fhi72.4x4-liteon_new.conf"
CONF_PNF="gnb-pnf.sa.band78.fhi72.nfapi.4x4-metanoia.conf"

# Commands for Single Machine Setup
CMD_VNF_100M_SINGLE="$COMMON_CMD $NFAPI_TRACE ./nr-softmodem -O $CONF_DIR/$CONF_VNF_100M $VNF_OPTS"
CMD_VNF_40M_SINGLE="$COMMON_CMD $NFAPI_TRACE ./nr-softmodem -O $CONF_DIR/$CONF_VNF_40M $VNF_OPTS"
CMD_MONO_100M_SINGLE="$COMMON_CMD rm -f gdb_script.txt && echo -e \"set confirm off\\nrun\\ndefine hook-stop\\nbt\\nend\" | sudo tee gdb_script.txt > /dev/null && sudo gdb --batch --command=gdb_script.txt --args ./nr-softmodem -O $CONF_DIR/$CONF_MONO_100M $MONO_OPTS"
CMD_MONO_40M_SINGLE="$COMMON_CMD ./nr-softmodem -O $CONF_DIR/$CONF_MONO_40M $MONO_OPTS"
CMD_MONO_100M_JURA_SINGLE="$COMMON_CMD rm -f gdb_script.txt && echo -e \"set confirm off\\nrun\\ndefine hook-stop\\nbt\\nend\" | sudo tee gdb_script.txt > /dev/null && sudo gdb --batch --command=gdb_script.txt --args ./nr-softmodem -O $CONF_DIR/$CONF_MONO_100M_JURA $MONO_OPTS"
CMD_PNF_SINGLE="$COMMON_CMD rm -f gdb_script.txt && echo -e \"set confirm off\\nrun\\ndefine hook-stop\\nbt\\nend\" | sudo tee gdb_script.txt > /dev/null && sudo gdb --batch --command=gdb_script.txt --args ./nr-softmodem -O $CONF_DIR/$CONF_PNF $PNF_OPTS"

# Additional config files
CONF_PNF_SPLIT="gnb-pnf.sa.band78.fhi72.nfapi.4x4-metanoia.conf"

# Common command prefixes for split setup
VNF_SPLIT_CMD_PREFIX="cd $VNF_BASE_PATH/$BUILD_DIR && echo '$SERVER_PASSWORD' | sudo -S $NFAPI_TRACE"
PNF_SPLIT_CMD_PREFIX="cd $PNF_BASE_PATH/$BUILD_DIR && echo '$SERVER_PASSWORD' | sudo -S"

# Commands for Split Machine Setup (Two Machines)
CMD_VNF_100M_SPLIT="$VNF_SPLIT_CMD_PREFIX ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/$CONF_VNF_100M $VNF_OPTS"
CMD_VNF_40M_SPLIT="$VNF_SPLIT_CMD_PREFIX ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/$CONF_VNF_40M $VNF_OPTS"
CMD_PNF_SPLIT="$PNF_SPLIT_CMD_PREFIX rm -f gdb_script.txt && echo -e \"set confirm off\\nrun\\ndefine hook-stop\\nbt\\nend\" | sudo tee gdb_script.txt > /dev/null && sudo gdb --batch --command=gdb_script.txt --args ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/$CONF_PNF_SPLIT $PNF_OPTS"



# Additional log files for single-machine mode
VNF_LOG_FILE_SINGLE="~/ming-vnf.log"
PNF_LOG_FILE_SINGLE="~/ming-pnf.log"

# Commands for Single Machine NFAPI Setup (both VNF and PNF on same server)
VNF_SINGLE_CMD_PREFIX="cd $PNF_BASE_PATH/$BUILD_DIR && echo '$SERVER_PASSWORD' | sudo -S $NFAPI_TRACE"
PNF_SINGLE_CMD_PREFIX="cd $PNF_BASE_PATH/$BUILD_DIR && echo '$SERVER_PASSWORD' | sudo -S"

# Single machine NFAPI commands (VNF and PNF both run on GNB_SERVER)
CMD_VNF_100M_SINGLE_MACHINE="$VNF_SINGLE_CMD_PREFIX ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/$CONF_VNF_100M $VNF_OPTS"
CMD_VNF_40M_SINGLE_MACHINE="$VNF_SINGLE_CMD_PREFIX ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/$CONF_VNF_40M $VNF_OPTS"
CMD_PNF_SINGLE_MACHINE="$PNF_SINGLE_CMD_PREFIX rm -f gdb_script.txt && echo -e \"set confirm off\\nrun\\ndefine hook-stop\\nbt\\nend\" | sudo tee gdb_script.txt > /dev/null && sudo gdb --batch --command=gdb_script.txt --args ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/$CONF_PNF_SPLIT $PNF_OPTS"

# Additional config files for single machine
CONF_VNF_100M_SINGLE="gnb-vnf.sa.band78.273prb.nfapi-samemachine.conf"
CONF_VNF_40M_SINGLE="gnb-vnf.sa.band78.106prb.nfapi-samemachine.conf"
CONF_PNF_SINGLE="gnb-pnf.sa.band78.fhi72.nfapi.4x4-metanoia-samemachine.conf"

# Update commands to use single-machine config files
CMD_VNF_100M_SINGLE_MACHINE="$VNF_SINGLE_CMD_PREFIX ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/$CONF_VNF_100M_SINGLE $VNF_OPTS"
CMD_VNF_40M_SINGLE_MACHINE="$VNF_SINGLE_CMD_PREFIX ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/$CONF_VNF_40M_SINGLE $VNF_OPTS"
CMD_PNF_SINGLE_MACHINE="$PNF_SINGLE_CMD_PREFIX rm -f gdb_script.txt && echo -e \"set confirm off\\nrun\\ndefine hook-stop\\nbt\\nend\" | sudo tee gdb_script.txt > /dev/null && sudo gdb --batch --command=gdb_script.txt --args ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/$CONF_PNF_SINGLE $PNF_OPTS"

# Function to start a screen session with custom log file
start_session() {
    local session_name=$1
    local command=$2
    local target_user=$3
    local target_host=$4
    local log_file=${5:-$GNB_LOG_FILE}  # Use custom log file if provided, default to GNB_LOG_FILE
    
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $target_user@$target_host "screen -dmS $session_name bash -c '$command &> $log_file'"
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

# Function to start single machine NFAPI setup
start_single_machine_nfapi_setup() {
    local bandwidth=$1  # 100M or 40M
    
    if [ "$bandwidth" = "100M" ]; then
        start_session "VNF_100M_SINGLE" "$CMD_VNF_100M_SINGLE_MACHINE" "$GNB_SERVER_USER" "$GNB_SERVER_HOST" "$VNF_LOG_FILE_SINGLE"
        start_session "PNF_SINGLE" "$CMD_PNF_SINGLE_MACHINE" "$GNB_SERVER_USER" "$GNB_SERVER_HOST" "$PNF_LOG_FILE_SINGLE"
    elif [ "$bandwidth" = "40M" ]; then
        start_session "VNF_40M_SINGLE" "$CMD_VNF_40M_SINGLE_MACHINE" "$GNB_SERVER_USER" "$GNB_SERVER_HOST" "$VNF_LOG_FILE_SINGLE"
        start_session "PNF_SINGLE" "$CMD_PNF_SINGLE_MACHINE" "$GNB_SERVER_USER" "$GNB_SERVER_HOST" "$PNF_LOG_FILE_SINGLE"
    fi
}

# Function to stop single machine NFAPI setup
stop_single_machine_nfapi_setup() {
    local bandwidth=$1  # 100M or 40M
    
    if [ "$bandwidth" = "100M" ]; then
        stop_session "VNF_100M_SINGLE" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
        stop_session "PNF_SINGLE" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
    elif [ "$bandwidth" = "40M" ]; then
        stop_session "VNF_40M_SINGLE" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
        stop_session "PNF_SINGLE" "$GNB_SERVER_USER" "$GNB_SERVER_HOST"
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

# Update start_gNB function to support single-machine mode
start_gNB() {
    local mode=${1:-$CURRENT_MODE}
    if [ "$mode" = "Monolithic" ]; then
        start_single_setup "100M" "Monolithic"
    elif [ "$SINGLE_MACHINE_MODE" = true ]; then
        start_single_machine_nfapi_setup "100M"
    else
        start_split_setup "100M"
    fi
}

# Update stop_gNB function to support single-machine mode
stop_gNB() {
    local mode=${1:-$CURRENT_MODE}
    if [ "$mode" = "Monolithic" ]; then
        stop_single_setup "100M" "Monolithic"
    elif [ "$SINGLE_MACHINE_MODE" = true ]; then
        stop_single_machine_nfapi_setup "100M"
    else
        stop_split_setup "100M"
    fi
}

# Function to reset all states and prepare for a clean start
reset_all() {
    local restart_scenario=${1:-"normal"}

    stop_gNB "Monolithic"
    if [ "$SINGLE_MACHINE_MODE" = true ]; then
        stop_single_machine_nfapi_setup "100M"
    else
        stop_gNB "NFAPI"
    fi

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
        # Enhanced reset for restart scenarios
        if [ "$restart_scenario" = "crash" ] || [ "$restart_scenario" = "ue_lost" ]; then
            echo "🔧 Performing enhanced reset for restart scenario: $restart_scenario"
            # Additional cleanup for crash scenarios
            sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $GNB_SERVER_USER@$GNB_SERVER_HOST \
                "screen -wipe 2>/dev/null || true" &>/dev/null
        fi
        
        sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no $GNB_SERVER_USER@$GNB_SERVER_HOST \
            "screen -dmS oaiLONvf bash -c 'echo $SERVER_PASSWORD | sudo -S source /home/oai72_su/juravf.sh || true'" &>/dev/null
    else
        echo "gNB server information not set, skipping remote script execution."
    fi
    
    # Optional: Reset Jura RU configuration
    source smo.sh
    configure_jura_ru
    
    echo "Reset complete for scenario: $restart_scenario"
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
        "Assertion"
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
    sleep 5
    
    # Create crash backup directory
    local crash_dir="$test_dir/crash_logs_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$crash_dir"
    
    # Backup main gNB log
    echo "Backing up main gNB log..."
    sshpass -p "$SERVER_PASSWORD" scp $SSH_OPTIONS "$GNB_SERVER_USER@$GNB_SERVER_HOST:$GNB_LOG_FILE" "$crash_dir/gnb_crash.log" 2>/dev/null || echo "Failed to backup main gNB log"
    echo "Backing up measurement files..."
    sshpass -p "$SERVER_PASSWORD" scp $SSH_OPTIONS "$GNB_SERVER_USER@$GNB_SERVER_HOST:$MEASURE_FILE_PATH" "$crash_dir/measure_crash.txt" 2>/dev/null || echo "Failed to backup measurement file"
    
    # Backup logs based on mode
    if [ "$mode" = "Monolithic" ]; then
        echo "Monolithic mode - single log file already backed up"
    elif [ "$SINGLE_MACHINE_MODE" = true ]; then
        echo "Backing up VNF log (single machine mode)..."
        sshpass -p "$SERVER_PASSWORD" scp $SSH_OPTIONS "$GNB_SERVER_USER@$GNB_SERVER_HOST:$VNF_LOG_FILE_SINGLE" "$crash_dir/vnf_crash_single.log" 2>/dev/null || echo "Failed to backup VNF log (single machine)"
        echo "Backing up PNF log (single machine mode)..."
        sshpass -p "$SERVER_PASSWORD" scp $SSH_OPTIONS "$GNB_SERVER_USER@$GNB_SERVER_HOST:$PNF_LOG_FILE_SINGLE" "$crash_dir/pnf_crash_single.log" 2>/dev/null || echo "Failed to backup PNF log (single machine)"
    else
        echo "Backing up VNF gNB log..."
        sshpass -p "$SERVER_PASSWORD" scp $SSH_OPTIONS "$VNF_GNB_SERVER_USER@$VNF_GNB_SERVER_HOST:$GNB_LOG_FILE" "$crash_dir/vnf_gnb_crash.log" 2>/dev/null || echo "Failed to backup VNF gNB log"
    fi
    
    echo "Crash logs backed up to: $crash_dir"
}

# Function to backup gNB logs after successful test completion
backup_gnb_logs() {
    local test_dir=$1
    local mode=${2:-$CURRENT_MODE}
    
    echo "📦 Backing up gNB logs to $test_dir..."
    
    # Create logs backup directory
    local logs_dir="$test_dir/logs"
    mkdir -p "$logs_dir"
    
    # Backup main gNB log file
    echo "Backing up main gNB log..."
    sshpass -p "$SERVER_PASSWORD" scp $SSH_OPTIONS "$GNB_SERVER_USER@$GNB_SERVER_HOST:$GNB_LOG_FILE" "$logs_dir/gnb.log" 2>/dev/null || echo "Failed to backup main gNB log"
    
    # Backup measurement file
    echo "Backing up measurement file..."
    sshpass -p "$SERVER_PASSWORD" scp $SSH_OPTIONS "$GNB_SERVER_USER@$GNB_SERVER_HOST:$MEASURE_FILE_PATH" "$logs_dir/measure.txt" 2>/dev/null || echo "Failed to backup measurement file"
    
    # Backup logs based on mode
    if [ "$mode" = "Monolithic" ]; then
        echo "Monolithic mode - single log file backed up"
    elif [ "$SINGLE_MACHINE_MODE" = true ]; then
        echo "Backing up VNF log (single machine mode)..."
        sshpass -p "$SERVER_PASSWORD" scp $SSH_OPTIONS "$GNB_SERVER_USER@$GNB_SERVER_HOST:$VNF_LOG_FILE_SINGLE" "$logs_dir/vnf_single.log" 2>/dev/null || echo "Failed to backup VNF log (single machine)"
        echo "Backing up PNF log (single machine mode)..."
        sshpass -p "$SERVER_PASSWORD" scp $SSH_OPTIONS "$GNB_SERVER_USER@$GNB_SERVER_HOST:$PNF_LOG_FILE_SINGLE" "$logs_dir/pnf_single.log" 2>/dev/null || echo "Failed to backup PNF log (single machine)"
    else
        echo "Backing up VNF gNB log..."
        sshpass -p "$SERVER_PASSWORD" scp $SSH_OPTIONS "$VNF_GNB_SERVER_USER@$VNF_GNB_SERVER_HOST:$GNB_LOG_FILE" "$logs_dir/vnf_gnb.log" 2>/dev/null || echo "Failed to backup VNF gNB log"
    fi
    
    # Backup additional system logs if available
    echo "Backing up system logs..."
    sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTIONS "$GNB_SERVER_USER@$GNB_SERVER_HOST" "sudo tail -1000 /var/log/syslog 2>/dev/null || echo 'No syslog available'" > "$logs_dir/syslog.log" 2>/dev/null || echo "Failed to backup syslog"
    sshpass -p "$SERVER_PASSWORD" ssh $SSH_OPTIONS "$GNB_SERVER_USER@$GNB_SERVER_HOST" "sudo dmesg 2>/dev/null || echo 'No dmesg available'" > "$logs_dir/dmesg.log" 2>/dev/null || echo "Failed to backup dmesg"
    
    echo "📦✅ gNB logs backed up to: $logs_dir"
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
    elif [ "$SINGLE_MACHINE_MODE" = true ]; then
        # Both VNF and PNF run on the same server in single-machine mode
        vnf_tag=$(get_git_tag "$GNB_SERVER_USER" "$GNB_SERVER_HOST" "$PNF_BASE_PATH")
        gnb_tag="$vnf_tag"  # Same as VNF since they're on the same server
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
**Test Mode:** $mode$([ "$SINGLE_MACHINE_MODE" = true ] && echo " (Single Machine)" || echo "")  
## 📊 Test Configuration

### Test Parameters
- **Protocols:** $([ "$TEST_UDP" = true ] && echo "UDP " || echo "")$([ "$TEST_TCP" = true ] && echo "TCP" || echo "")
- **Downlink Range:** ${DL_START}M - ${DL_END}M (Step: ${DL_STEP}M)
$([ "$ENABLE_UL" = true ] && echo "- **Uplink Range:** ${UL_START}M - ${UL_END}M (Step: ${UL_STEP}M)" || echo "- **Uplink:** Disabled")
- **Sleep Window:** $SLEEP_WINDOW seconds

## 🏗️ Software Versions

### gNB Software
- **Mode:** $mode$([ "$SINGLE_MACHINE_MODE" = true ] && echo " (Single Machine)" || echo "")
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

$([ "$mode" != "Monolithic" ] && [ "$SINGLE_MACHINE_MODE" = true ] && echo "### NFAPI Single Machine Configuration
- **VNF Server:** $GNB_SERVER_USER@$GNB_SERVER_HOST (Single Machine Mode)
- **PNF Server:** $GNB_SERVER_USER@$GNB_SERVER_HOST (Single Machine Mode)
- **VNF Base Path:** $PNF_BASE_PATH
- **PNF Base Path:** $PNF_BASE_PATH
- **VNF Log File:** $VNF_LOG_FILE_SINGLE
- **PNF Log File:** $PNF_LOG_FILE_SINGLE")

$([ "$mode" != "Monolithic" ] && [ "$SINGLE_MACHINE_MODE" != true ] && echo "### NFAPI Split Configuration
- **VNF Server:** $VNF_GNB_SERVER_USER@$VNF_GNB_SERVER_HOST
- **PNF Server:** $GNB_SERVER_USER@$GNB_SERVER_HOST
- **VNF Base Path:** $VNF_BASE_PATH
- **PNF Base Path:** $PNF_BASE_PATH")

*Report generated automatically by E2E Network Measurement System*
EOF

    echo "📋✅ Test environment report generated: $report_file"
}

