#!/bin/bash

source variable.sh
source collect_data_fromCN.sh
source modify_UE.sh
source run_gNB.sh

# stop_split_setup "100M"
# start_split_setup "100M"
# toggle_airplane_mode "on"
# sleep 10
# toggle_airplane_mode "off"

if [ -z "$UE_IP" ]; then
    get_ue_ip
fi

ping-start $UE_IP
sleep 3
iperf-start

sleep 1
run_iperf "client" "10.45.0.1" "-u -b 200M -t 3 -J" "./data/iperf-client.json"

iperf-stop "iperf-server"
ping-stop "ping-value"
