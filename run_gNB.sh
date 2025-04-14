#!/bin/bash

# Global variables
USER="oai72"
HOST="192.168.8.43"
PASSWORD="bmwlab"

CMD_VNF_100M="cd ~/FH_7.2_dev/openairinterface5g/cmake_targets/ran_build/build && echo '$PASSWORD' | sudo -S NFAPI_TRACE_LEVEL=info ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb-vnf.sa.band78.273prb.nfapi.conf --nfapi VNF"
CMD_PNF="cd ~/FH_7.2_dev/openairinterface5g/cmake_targets/ran_build/build && echo '$PASSWORD' | sudo -S NFAPI_TRACE_LEVEL=info ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb-pnf.band78.fhi72.4x4-liteon_new.conf --nfapi PNF --reorder-thread-disable 1 --thread-pool 1,3,5,7,9,11,13,15"
CMD_Monolithic="cd ~/FH_7.2_dev/openairinterface5g/cmake_targets/ran_build/build && echo '$PASSWORD' | sudo -S ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb.sa.band78.273prb.fhi72.4x4-liteon_new.conf --thread-pool 1,3,5,7,9,11,13,15"

# Commands for 40MHz (106PRB)
CMD_VNF_40MHz="cd ~/FH_7.2_dev/openairinterface5g/cmake_targets/ran_build/build && echo '$PASSWORD' | sudo -S NFAPI_TRACE_LEVEL=info ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb-vnf.sa.band78.106prb.nfapi.conf --nfapi VNF"
CMD_Monolithic_40MHz="cd ~/FH_7.2_dev/openairinterface5g/cmake_targets/ran_build/build && echo '$PASSWORD' | sudo -S ./nr-softmodem -O ../../../targets/PROJECTS/GENERIC-NR-5GC/CONF/gnb.sa.band78.106prb.fhi72.4x4-liteon_new --thread-pool 1,3,5,7,9,11,13,15"

# Function to start a screen session
start_session() {
    local session_name=$1
    local command=$2
    sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no $USER@$HOST "screen -dmS $session_name bash -c '$command'"
}

# Function to stop a screen session
stop_session() {
    local session_name=$1
    sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no $USER@$HOST "screen -X -S $session_name quit"
}

# Start sessions
start_session "VNF" "$CMD_VNF_100M"
# start_session "PNF" "$CMD_PNF"
# start_session "Monolithic" "$CMD_Monolithic"

# Start sessions for 40MHz
# start_session "VNF_40MHz" "$CMD_VNF_40MHz"
start_session "PNF" "$CMD_PNF"
# start_session "Monolithic_40MHz" "$CMD_Monolithic_40MHz"

# Example to stop sessions (uncomment to use)
# stop_session "VNF"
# stop_session "PNF"
# stop_session "Monolithic"
# stop_session "VNF_40MHz"
# stop_session "PNF"
# stop_session "Monolithic_40MHz"
