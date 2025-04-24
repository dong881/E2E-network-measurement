# Network Analysis Python Script Documentation

## Overview

The `network_analysis.py` script provides comprehensive analysis of network performance data collected during testing. It processes iPerf3 JSON files and ping logs to extract meaningful metrics, correlate data points, and generate visualizations that help understand network behavior.

## Script Features

### 1. Data Selection and Organization

- **Directory-based analysis**: Allows users to select specific test directories from a command-line menu
- **Automatic test group detection**: Intelligently discovers and groups related test files by bandwidth, direction, and protocol
- **Flexible file pattern matching**: Handles various naming conventions with fallback strategies

### 2. Data Processing Capabilities

- **iPerf3 JSON parsing**: Extracts throughput, jitter, packet loss statistics, and CPU utilization
- **Ping log parsing**: Supports multiple timestamp formats and calculates latency statistics
- **Test correlation**: Synchronizes ping and throughput measurements based on timestamps
- **Statistical analysis**: Calculates min/max/average metrics for throughput and latency

### 3. Visualization Generation

- **Summary plots**: Overall ping latency vs. throughput for all tested bandwidths
- **Limited-range plots**: Special plots with y-axis limited to 100ms for better visibility of lower latency details
- **Detailed per-test plots**: Individual throughput and ping graphs for each bandwidth setting
- **Comparison tables**: CSV files with comprehensive metrics for further analysis

## Key Functions

### Data Parsing Functions

- `parse_iperf_json(file_path)`: Processes iPerf3 JSON output files to extract performance metrics
- `parse_ping_log(file_path)`: Processes ping logs to extract latency information
- `extract_target_throughput(filename)`: Determines target bandwidth from filenames
- `correlate_throughput_ping(throughput_data, ping_data, ping_file)`: Synchronizes ping and throughput data

### Test Group Management

- `get_test_groups(data_dir)`: Identifies related test files and groups them by bandwidth and direction
- `analyze_test_group(cn_file, ue_file, ping_file)`: Processes a group of related test files

### Visualization Functions

- `plot_detailed_test_results(result, direction, output_dir)`: Creates detailed plots for a single test
- `plot_results(groups, direction, output_dir)`: Creates summary plots and individual test plots
- `create_comparison_table(results, direction, output_dir)`: Creates comparison tables and plots

## Usage

1. Run the script: `python3 network_analysis.py`
2. Select a test directory from the menu
3. The script will:
   - Identify test groups
   - Process the data
   - Generate all visualizations
   - Save results to the corresponding output directory

## Downlink vs Uplink Mode

The script handles downlink and uplink modes differently:

- **Downlink mode**: Only UE throughput is relevant and displayed in plots
- **Uplink mode**: Both CN and UE throughput are displayed and compared

## Error Handling

The script includes robust error handling throughout:
- Gracefully handles missing data files
- Reports parsing errors with helpful debug information
- Provides fallback strategies when expected patterns aren't found

## Output Files

All outputs are saved to the `/home/ming/E2E-network-measurement/results/<directory_name>/` path:

- **CSV files**: `<direction>_udp_comparison.csv` (detailed metrics tables)
- **Summary plot**: `ping_latency_<direction>_udp.png` (full-scale summary plot)
- **Limited range plot**: `ping_latency_<direction>_udp-max100ms.png` (plot with 100ms limit)
- **Detailed plots**: `<direction>_udp_<bandwidth>M_detailed.png` (one per test)
- **Metrics comparison**: `<direction>_udp_metrics_comparison.png` (four-panel detailed metrics)

## Dependencies

- `matplotlib`: For plotting
- `numpy`: For numerical calculations
- `pandas`: For data manipulation
- `glob`: For file pattern matching
- `re`: For regular expression parsing
