# E2E Network Measurement - Installation Guide

This guide provides detailed instructions for installing and configuring the E2E Network Measurement framework.

## System Requirements

### Hardware Requirements
- **Control PC**: Linux machine to run the scripts
- **RU Device**: Radio Unit accessible via SSH
- **gNB Server(s)**: Can be configured for either:
  - Monolithic deployment (single server)
  - Split deployment (separate VNF and PNF servers)
- **CN Server**: Core Network server accessible via SSH
- **UE Device**: Android device connected via USB for ADB control

### Operating System Requirements
- **Control PC**: Ubuntu 18.04 LTS or later (recommended)
- **Server Environments**: Compatible with most Linux distributions

## Installation Process

### 1. Prerequisites

First, ensure you have the necessary base packages:

```bash
# Update package lists
sudo apt update

# Install base requirements
sudo apt install -y git python3 python3-pip sshpass screen expect curl
```

### 2. Install ADB (Android Debug Bridge)

```bash
# Install ADB package
sudo apt install -y android-tools-adb

# Verify installation
adb version
```

Alternative method (platform-tools):
```bash
# Download platform-tools
wget https://dl.google.com/android/repository/platform-tools-latest-linux.zip

# Extract archive
unzip platform-tools-latest-linux.zip -d ~/

# Add to PATH (add to your .bashrc for persistence)
export PATH="$PATH:$HOME/platform-tools"

# Verify installation
adb version
```

### 3. Install iPerf3

```bash
# Install iPerf3
sudo apt install -y iperf3

# Verify installation
iperf3 --version
```

### 4. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/E2E-network-measurement.git
cd E2E-network-measurement

# Make scripts executable
chmod +x *.sh
chmod +x Measure/result/*.sh
```

### 5. Install Python Dependencies

```bash
# Install required Python packages
pip3 install matplotlib numpy pandas seaborn
```

### 6. Prepare UE Device

1. Connect your Android device to the Control PC via USB
2. Enable Developer Options and USB Debugging on the device
3. Verify ADB can detect the device:
   ```bash
   adb devices
   ```
4. Install iPerf3 on the UE:
   ```bash
   # Push the iPerf3 binary to the device
   # Option 1: Using pre-compiled binary for Android
   wget https://iperf.fr/download/android/iperf3.8.1
   adb push iperf3.8.1 /data/local/tmp/iperf3
   
   # Option 2: Push from your PC (if you have it already)
   # adb push /path/to/iperf3 /data/local/tmp/iperf3
   
   # Set executable permissions
   adb shell chmod +x /data/local/tmp/iperf3
   
   # Verify installation
   adb shell /data/local/tmp/iperf3 -v
   ```

### 7. Create Required Directories

```bash
# Create data directories
mkdir -p data results Measure/log Measure/result
```

## Configuration Setup

### 1. Configure Environment Variables

Create or edit `variable.sh` to set your network configuration:

```bash
cp variable.sh.example variable.sh  # If example exists
nano variable.sh
```

Essential variables to configure:

```bash
# RU Configuration
RU_IP="192.168.x.x"
RU_USERNAME="username"
RU_PASSWORD="password"

# gNB Configuration
GNB_IP="192.168.x.x"
GNB_USERNAME="username"
GNB_PASSWORD="password"

# For split setup (if applicable)
VNF_IP="192.168.x.x"
VNF_USERNAME="username"
VNF_PASSWORD="password"

PNF_IP="192.168.x.x"
PNF_USERNAME="username"
PNF_PASSWORD="password"

# CN Configuration
CN_IP="192.168.x.x"
CN_USERNAME="username"
CN_PASSWORD="password"
INTERFACE="ogstun"  # Network interface for testing

# Server IP
SERVER_IP="192.168.x.x"  # Control PC's IP on test network
TEST_SERVER_IP="192.168.x.x"  # IP for iPerf/ping tests (often CN server)
```

### 2. Configure Test Parameters

Create or edit `run_config.sh` to set test parameters:

```bash
cp run_config.sh.example run_config.sh  # If example exists
nano run_config.sh
```

Essential parameters to configure:

```bash
# ADB Settings
ADB_DEVICE="0123456789ABCDEF"  # Your UE's serial number (from 'adb devices')

# Test Settings
TEST_DURATION=15  # Duration in seconds
MAX_RETRIES=5     # UE connection retry count

# Protocol Selection
TEST_UDP=true
TEST_TCP=true
ENABLE_UL=true    # Enable uplink tests

# Downlink Bandwidth Range (in Mbps)
DL_START=10
DL_END=100
DL_STEP=10

# Uplink Bandwidth Range (in Mbps)
UL_START=10
UL_END=100
UL_STEP=10

# Wait Times (in seconds)
WAIT_AFTER_REBOOT=60
WAIT_AFTER_GNB=30
SLEEP_WINDOW=5
```

## Verification Steps

### 1. Check Dependencies

Use this script to verify all dependencies are correctly installed:

```bash
#!/bin/bash
echo "Checking dependencies for E2E Network Measurement..."

# Check commands
command -v sshpass >/dev/null 2>&1 && echo "✅ sshpass installed" || echo "❌ sshpass missing"
command -v screen >/dev/null 2>&1 && echo "✅ screen installed" || echo "❌ screen missing"
command -v expect >/dev/null 2>&1 && echo "✅ expect installed" || echo "❌ expect missing"
command -v adb >/dev/null 2>&1 && echo "✅ adb installed" || echo "❌ adb missing"
command -v iperf3 >/dev/null 2>&1 && echo "✅ iperf3 installed" || echo "❌ iperf3 missing"

# Check Python dependencies
python3 -c "import matplotlib; print('✅ matplotlib installed')" 2>/dev/null || echo "❌ matplotlib missing"
python3 -c "import numpy; print('✅ numpy installed')" 2>/dev/null || echo "❌ numpy missing"
python3 -c "import pandas; print('✅ pandas installed')" 2>/dev/null || echo "❌ pandas missing"
python3 -c "import seaborn; print('✅ seaborn installed')" 2>/dev/null || echo "❌ seaborn missing"

# Check UE connection
adb devices | grep -q "device$" && echo "✅ ADB device connected" || echo "❌ No ADB device connected"

# Check configuration files
[ -f variable.sh ] && echo "✅ variable.sh exists" || echo "❌ variable.sh missing"
[ -f run_config.sh ] && echo "✅ run_config.sh exists" || echo "❌ run_config.sh missing"

# Check directories
[ -d data ] && echo "✅ data directory exists" || echo "❌ data directory missing"
[ -d results ] && echo "✅ results directory exists" || echo "❌ results directory missing"
[ -d Measure/log ] && echo "✅ Measure/log directory exists" || echo "❌ Measure/log directory missing"
[ -d Measure/result ] && echo "✅ Measure/result directory exists" || echo "❌ Measure/result directory missing"

echo "Dependency check complete!"
```

Save this as `check_dependencies.sh`, make it executable with `chmod +x check_dependencies.sh`, and run it to verify your setup.

### 2. Test SSH Connectivity

Test SSH connections to each server:

```bash
# Source your variables file to access credentials
source variable.sh

# Test RU connection
sshpass -p "$RU_PASSWORD" ssh -o StrictHostKeyChecking=no "$RU_USERNAME@$RU_IP" echo "RU SSH connection successful"

# Test gNB connection
sshpass -p "$GNB_PASSWORD" ssh -o StrictHostKeyChecking=no "$GNB_USERNAME@$GNB_IP" echo "gNB SSH connection successful"

# Test CN connection
sshpass -p "$CN_PASSWORD" ssh -o StrictHostKeyChecking=no "$CN_USERNAME@$CN_IP" echo "CN SSH connection successful"

# For split setup (if applicable)
sshpass -p "$VNF_PASSWORD" ssh -o StrictHostKeyChecking=no "$VNF_USERNAME@$VNF_IP" echo "VNF SSH connection successful"
sshpass -p "$PNF_PASSWORD" ssh -o StrictHostKeyChecking=no "$PNF_USERNAME@$PNF_IP" echo "PNF SSH connection successful"
```

### 3. Test ADB Connection and iPerf3 on UE

```bash
# Check ADB connection
adb -s $ADB_DEVICE shell echo "ADB connection successful"

# Check iPerf3 on UE
adb -s $ADB_DEVICE shell "/data/local/tmp/iperf3 -v"
```

## Troubleshooting

### SSH Connection Issues
- **Problem**: "ssh: connect to host X port 22: Connection refused" or timeouts
- **Solutions**:
  - Verify the server's SSH service is running: `sudo systemctl status ssh`
  - Check firewall settings: `sudo ufw status` and allow SSH if needed
  - Confirm the IP address is correct and reachable (ping test)
  - Try connecting with verbose output: `ssh -v username@ip_address`

### ADB Connection Issues
- **Problem**: Device not showing in `adb devices` or showing as "unauthorized"
- **Solutions**:
  - Check USB connection and try different cables or ports
  - Restart the ADB server: `adb kill-server && adb start-server`
  - On the device, revoke USB debugging authorizations and re-authorize
  - Check ADB device serial in `run_config.sh` matches output from `adb devices`

### Permission Issues
- **Problem**: Permission denied errors when running scripts
- **Solutions**:
  - Ensure all scripts are executable: `chmod +x *.sh`
  - Check file ownership: `ls -la *.sh`
  - Run scripts with sudo if necessary (not recommended for regular use)

### Python Package Issues
- **Problem**: Missing Python dependencies or import errors
- **Solutions**:
  - Reinstall dependencies with pip: `pip3 install -U matplotlib numpy pandas seaborn`
  - Check Python version: `python3 --version` (should be 3.6+)
  - Install packages system-wide if needed: `sudo pip3 install matplotlib numpy pandas seaborn`

### iPerf3 Issues on UE
- **Problem**: Cannot run iPerf3 on the UE
- **Solutions**:
  - Verify binary is in place: `adb shell ls -la /data/local/tmp/iperf3`
  - Check permissions: `adb shell chmod +x /data/local/tmp/iperf3`
  - Use a compatible binary for your device architecture
  - Try installing via termux if available

## Next Steps

After successful installation and configuration:

1. Run a basic test to verify the setup:
   ```bash
   ./main.sh --manual-mode  # For interactive mode
   # OR
   ./main.sh --mode MONO    # For automatic mode
   ```

2. Check the generated test data in the `data/` directory

3. Proceed to the full README for advanced usage instructions and analysis procedures

## Additional Resources

- [Official iPerf3 Documentation](https://iperf.fr/iperf-doc.php)
- [ADB Documentation](https://developer.android.com/studio/command-line/adb)
- [Project Visualization Guide](docs/visualization_guide.md)
