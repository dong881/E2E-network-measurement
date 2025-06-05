#!/bin/bash

# Source the variable file to get SERVER_PASSWORD
source ./variable.sh

# Function to SSH to ksmo and execute Mplane.sh
configure_jura_ru() {
    # echo "Uploading Mplane.sh to K-releaseSMO..."
    sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no ~/E2E-network-measurement/tools/Mplane.sh $KSMO_USER@$KSMO_HOST:$KSMO_HOME/
    
    if [ $? -ne 0 ]; then
        echo "Failed to upload Mplane.sh to K-releaseSMO"
        return 1
    fi
    
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no -o LogLevel=ERROR $KSMO_USER@$KSMO_HOST "cd $KSMO_HOME && TERM=dumb expect -f ./Mplane.sh" < /dev/null
    
    if [ $? -eq 0 ]; then
        echo "Successfully configured Jura RU from K-releaseSMO via Mplane"
    else
        echo "Failed to configure Jura RU from K-releaseSMO via Mplane"
        return 1
    fi
}

