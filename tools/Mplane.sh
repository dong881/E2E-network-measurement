#!/usr/bin/expect -f
# filepath: /home/ming/E2E-network-measurement/configure_jura_ru.exp

# Set timeout
set timeout 30

#######################
# Suppress output (optional)
# This is useful to avoid cluttering the terminal with expect output
log_user 0
#######################

# Change to Summer directory
cd Summer

# Start netopeer2-cli
spawn netopeer2-cli
expect ">"

# Connect to the host
send "connect --host 192.168.8.93 --port 830 --login oranuser\r"
expect "*password:"
send "metanoia123\r"
expect "*> "

# Execute configuration commands
send "edit-config --target running --config=ietf-interface.xml\r"
expect "*> "
sleep 0.3
send "edit-config --target running --config=processing-element.xml\r"
expect "*> "
sleep 0.3
send "edit-config --target running --config=o-ran-uplane-conf_100M.xml\r"
expect "*> "
sleep 0.3
send "edit-config --target running --config=o-ran-uplane-conf_100M.xml\r"
expect "*> "
sleep 0.3
# Disconnect and exit
send "quit\r"
expect eof

# Exit the script
exit 0