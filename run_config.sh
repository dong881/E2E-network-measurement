#!/bin/bash
export ADB_DEVICE="0123456789ABCDEF"
export TEST_DURATION=5 # Duration in seconds (updated from main.sh)
export WAIT_AFTER_REBOOT=60
export WAIT_AFTER_GNB=18

# Test execution parameters from main.sh
export MAX_RETRIES=6
export TEST_UDP=true
export TEST_TCP=false
export DL_START=100
export DL_END=1000
export DL_STEP=100
export ENABLE_UL=true
export UL_START=10
export UL_END=120
export UL_STEP=10
export SLEEP_WINDOW=5 # Renamed from SLEEP_window
