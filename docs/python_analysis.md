# Network Analysis Python Scripts Documentation

## Overview

The project includes several Python scripts for analyzing different aspects of network performance:

1. **`network_analysis.py`**: Comprehensive analysis of iPerf and ping data
2. **`VNF-lossPacket.py`**: Analysis of packet loss from network logs
3. **`Measure/analyze_logs.py`**: Timestamp difference analysis between VNF and PNF logs
4. **`Measure/compare_latency.py`**: Comparison of latency across deployment models
5. **`clean_iperf_json.py`**: Utility to clean and fix iPerf JSON output files

## 1. `network_analysis.py`

### Purpose
Provides comprehensive analysis of network performance data collected during testing. It processes iPerf3 JSON files and ping logs to extract meaningful metrics, correlate data points, and generate visualizations.

### Installation Requirements
```bash
pip install matplotlib numpy pandas seaborn
```

### Features

#### Data Selection and Organization

- **Directory-based analysis**: Allows users to select specific test directories from a command-line menu
- **Automatic test group detection**: Intelligently discovers and groups related test files by bandwidth, direction, and protocol
- **Flexible file pattern matching**: Handles various naming conventions with fallback strategies

#### Data Processing Capabilities

- **iPerf3 JSON parsing**: Extracts throughput, jitter, packet loss statistics, and CPU utilization
- **Ping log parsing**: Supports multiple timestamp formats and calculates latency statistics
- **Test correlation**: Synchronizes ping and throughput measurements based on timestamps
- **Statistical analysis**: Calculates min/max/average metrics for throughput and latency

#### Visualization Generation

- **Summary plots**: Overall ping latency vs. throughput for all tested bandwidths
- **Limited-range plots**: Special plots with y-axis limited to 100ms for better visibility of lower latency details
- **Detailed per-test plots**: Individual throughput and ping graphs for each bandwidth setting
- **Comparison tables**: CSV files with comprehensive metrics for further analysis

### Key Functions

#### Data Parsing Functions

- `parse_iperf_json(file_path)`: Processes iPerf3 JSON output files to extract performance metrics
- `parse_ping_log(file_path)`: Processes ping logs to extract latency information
- `extract_target_throughput(filename)`: Determines target bandwidth from filenames
- `correlate_throughput_ping(throughput_data, ping_data, ping_file)`: Synchronizes ping and throughput data

#### Test Group Management

- `get_test_groups(data_dir)`: Identifies related test files and groups them by bandwidth and direction
- `analyze_test_group(cn_file, ue_file, ping_file)`: Processes a group of related test files

#### Visualization Functions

- `plot_detailed_test_results(result, direction, output_dir)`: Creates detailed plots for a single test
- `plot_results(groups, direction, output_dir)`: Creates summary plots and individual test plots
- `create_comparison_table(results, direction, output_dir)`: Creates comparison tables and plots

### Usage

```bash
python3 network_analysis.py
```

When prompted, select a test directory from the menu. The script will automatically process all files and generate visualizations.

### Output Files

All outputs are saved to the `/home/ming/E2E-network-measurement/results/<directory_name>/` path:

- **CSV files**: `<direction>_udp_comparison.csv` (detailed metrics tables)
- **Summary plot**: `ping_latency_<direction>_udp.png` (full-scale summary plot)
- **Limited range plot**: `ping_latency_<direction>_udp-max100ms.png` (plot with 100ms limit)
- **Detailed plots**: `<direction>_udp_<bandwidth>M_detailed.png` (one per test)
- **Metrics comparison**: `<direction>_udp_metrics_comparison.png` (four-panel detailed metrics)

## 2. `VNF-lossPacket.py`

### Purpose
Analyzes packet loss patterns from network logs, particularly focusing on VNF/gNB packet timing.

### Features
- Extracts packet information from log files
- Calculates packet loss rate based on sequence numbers
- Identifies patterns of consecutive packet losses
- Generates statistical reports on packet loss characteristics
- Produces visualizations of consecutive packet loss distribution

### Key Functions
- `calculate_packet_loss_rate(input_text)`: Analyzes text logs to determine packet loss metrics
- `find_consecutive_losses(lost_packets)`: Identifies patterns of consecutive packet losses
- `plot_consecutive_loss_distribution(consecutive_losses)`: Creates visualizations of loss patterns

### Usage
```bash
python3 VNF-lossPacket.py
```

Follow the prompts to input log content. Enter "END" on a new line when finished.

## 3. `Measure/analyze_logs.py`

### Purpose
Analyzes timestamp differences between VNF and PNF logs to measure communication latency and synchronization.

### Features
- Extracts timestamps from VNF and PNF log files
- Calculates time differences between corresponding log entries
- Provides comprehensive statistical analysis of timestamp differences
- Generates visualizations showing raw differences, filtered data, and box plots
- Creates detailed reports with min/max/mean/median/standard deviation metrics

### Key Functions
- `calculate_timestamp_differences(vnf_path, pnf_path)`: Extracts and calculates timestamp differences
- `generate_report(vnf_path, pnf_path, differences, report_path)`: Creates a comprehensive report
- `plot_timestamp_differences(differences, output_filename)`: Visualizes raw timestamp differences
- `plot_filtered_differences(differences, output_filename)`: Creates filtered visualizations
- `create_box_plot(data_dict, output_filename)`: Generates statistical box plots

### Usage
```bash
python3 Measure/analyze_logs.py /path/to/vnf_log /path/to/pnf_log
```

### Output Files
Results are saved to `Measure/result/` with filenames based on the input files:
- `*_report.txt`: Detailed statistical report
- `*_plot.png`: Raw timestamp difference plot
- `*_filtered_plot.png`: Filtered timestamp difference plot (outliers removed)
- `*_box_plot.png`: Statistical box plot

## 4. `Measure/compare_latency.py`

### Purpose
Compares latency metrics across different deployment models (Monolithic, NFAPI with socket, NFAPI with raw socket).

### Features
- Parses latency report files from different deployment models
- Extracts key metrics (mean, median, min, max, standard deviation)
- Creates comparative visualizations showing relative performance
- Provides statistical analysis of performance differences
- Generates both graphical and tabular representations of results

### Usage
```bash
python3 Measure/compare_latency.py
```

### Output Files
- `Measure/result/latency_comparison.png`: Multi-panel comparison of all metrics
- `Measure/result/latency_table.png`: Tabular summary of all metrics

## 5. `clean_iperf_json.py`

### Purpose
Cleans and fixes iPerf JSON output files that may contain errors or multiple JSON objects.

### Features
- Identifies and removes error blocks from iPerf JSON files
- Handles cases with multiple JSON objects in a single file
- Preserves valid data while cleaning problematic sections
- Automatically processes all JSON files in the target directory

### Usage
```bash
# Edit the DATA_DIR variable in the script if necessary
python3 clean_iperf_json.py
```

## Workflow and Integration

These scripts form a comprehensive analysis pipeline:

1. Run tests using `main.sh` to collect raw data
2. Use `clean_iperf_json.py` to fix any problematic JSON files
3. Use `network_analysis.py` to analyze throughput and latency performance
4. Use `Measure/analyze_logs.py` to analyze VNF-PNF synchronization
5. Use `Measure/compare_latency.py` to compare different deployment models
6. Use `VNF-lossPacket.py` to investigate packet loss issues if needed

The modular design allows focusing on specific aspects of network performance while maintaining a consistent analysis methodology.

## Installation and Dependencies

Install all required dependencies with:
```bash
pip install matplotlib numpy pandas seaborn
```

Ensure the correct directory structure exists:
```bash
mkdir -p data results Measure/log Measure/result
```
