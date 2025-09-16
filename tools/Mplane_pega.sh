#!/usr/bin/expect -f
# filepath: /home/ming/E2E-network-measurement/configure_jura_ru.exp
cd ~/PEGA_Mplane
# Set timeout
set timeout 30

#######################
# Suppress output (optional)
# This is useful to avoid cluttering the terminal with expect output
log_user 1
#######################

# Start netopeer2-cli
spawn netopeer2-cli
expect ">"

# Connect to the host (PEGA RU)
send "connect --host 192.168.10.9 --port 830 --login padmin\r"
expect "Password:"
send "Pega@2025\r"
expect "*> "

# Execute configuration commands
send "edit-config --target running --config=ietf-interface-processing-element.xml\r"
expect "*> "
sleep 0.3
send "edit-config --target running --config=o-ran-uplane-conf_100M_4x4.xml\r"
expect "*> "
sleep 0.3
send "edit-config --target running --config=o-ran-uplane-conf_100M_4x4.xml\r"
expect "*> "
sleep 0.3
# Disconnect and exit
send "quit\r"
expect eof

# Exit the script
exit 0
