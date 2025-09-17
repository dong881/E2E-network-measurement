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

## 2. Individual Analysis Scripts

### 2.1 `scripts/analyze_throughput.py`

**Purpose**: Analyzes network throughput performance between CN (sender) and UE (receiver) with professional styling.

**Key Features**:
- Extracts throughput data from both CN and UE iPerf files
- Creates comparative bar charts with professional color scheme matching throughput_comparison
- Calculates throughput efficiency and displays percentage values with background styling
- Professional value labeling with meaningful colors: Blue (#2E86AB) for CN, Pink (#A23B72) for UE, Yellow (#F8E71C) for efficiency
- Outputs to `output/throughput_analysis/` directory

### 2.2 `scripts/analyze_packet_loss.py`

**Purpose**: Analyzes packet loss rates from the receiver (UE) perspective with publication-quality visualizations.

**Key Features**:
- Extracts UE-measured loss rates from `sum_received.lost_percent` (preferred) or fallback to `sum.lost_percent`
- Publication-quality color scheme with six distinct loss rate ranges
- Professional styling suitable for academic papers and presentations
- Legend positioned at top-left showing loss rate ranges without quality classifications
- Precise value labels (2 decimal places) for accurate data representation
- Enhanced grid and professional typography
- **Output**: PNG image file (`ue_packet_loss_analysis.png`), not log files
- Generates visualizations directly to the output directory without creating logs subdirectory

**Generated Files**:
- `ue_packet_loss_analysis.png`: Comprehensive UE packet loss analysis with rate range categorization

**Usage**:
```bash
# Interactive mode (recommended)
python3 scripts/analyze_packet_loss.py

# Command line mode with specific directory
python3 scripts/analyze_packet_loss.py /path/to/data/directory
```

### 2.3 `tools/VNF-lossPacket.py`

**Purpose**: Analyzes packet loss between VNF and PNF components with interactive data selection.

**Key Features**:
- Interactive data folder selection using the data_selector module
- Automatic discovery of VNF and PNF log files in selected directories
- Packet ID-based loss analysis between network components
- SFN/Slot specific packet loss analysis for cellular networks
- Consecutive packet loss pattern analysis with visualization
- Supports both command-line arguments and interactive mode
- Enhanced error handling for file I/O operations
- Outputs comprehensive packet loss statistics and visualizations

**Usage**:
```bash
# Interactive mode (recommended)
python3 tools/VNF-lossPacket.py -i

# Command line mode
python3 tools/VNF-lossPacket.py /path/to/vnf.log /path/to/pnf.log

# With custom output file
python3 tools/VNF-lossPacket.py -i -o custom_analysis.png
```

### 2.4 `scripts/analyze_loss_rate.py`

**Purpose**: Advanced loss rate analysis comparing CN (sender) and UE (receiver) perspectives with merged visualization and enhanced output organization.

**Key Features**:
- Merged bar chart and trend line analysis in a single comprehensive plot
- Precise data values displayed with 2 decimal places
- CN vs UE comparison with distinct colors and markers
- Trend lines overlaid on bar charts for pattern identification
- Professional styling with enhanced legends and grid
- Removes manual calculation redundancy, focuses on CN and UE measurements
- Enhanced output organization with dedicated `loss_rate_analysis/` subdirectory
- Proper file verification and error handling
- Outputs to `output/loss_rate_analysis/` directory with merged analysis

**Generated Files**:
- `merged_loss_rate_analysis.png`: Comprehensive CN vs UE loss rate comparison with trends and clean layout

### 2.5 `scripts/analyze_jitter.py`

**Purpose**: Analyzes network jitter (timing variation) from UE measurements.

**Key Features**:
- Extracts jitter data from UE iPerf files
- Color-codes results based on jitter quality levels (Excellent ≤1ms, Good 1-3ms, Fair 3-5ms, Poor 5-10ms, Very Poor >10ms)
- Shows jitter trends across bandwidth configurations with directional trend indicators
- Includes enhanced aesthetics with meaningful color scheme and quality legend
- Outputs to `output/jitter_analysis/` directory

### 2.6 `scripts/analyze_cpu_utilization.py`

**Purpose**: Analyzes CPU utilization for both CN and UE devices with enhanced visualizations.

**Key Features**:
- Creates stacked bar charts showing User + System CPU breakdown for both CN and UE
- Displays user CPU values within the user sections and total values above bars for clear visibility
- Smart label positioning to avoid layout overflow while maintaining readability
- Generates comprehensive statistical summary tables with CPU difference analysis
- Enhanced styling with professional color schemes and detailed labeling
- Outputs to `output/cpu_analysis/` directory

**Generated Plots**:
- `cpu_total_utilization_stacked_comparison.png`: Enhanced stacked comparison of CN vs UE with user values displayed
- `cpu_utilization_enhanced_summary_table.png`: Comprehensive statistical summary

### 2.7 `scripts/analyze_ping_latency.py`

**Purpose**: Analyzes ping latency with comprehensive statistical analysis and organized output.

**Key Features**:
- Creates comprehensive analysis plots combining all bandwidth configurations
- Generates individual detailed analysis plots for each bandwidth configuration
- Provides quartile analysis, outlier detection, and trend analysis
- Enhanced styling with professional color schemes and improved readability
- Outputs to centralized directory with organized structure

**Generated Plots**:
- `ping_latency_comprehensive_analysis_{direction}.png`: Overall analysis across all bandwidth configurations with professional styling and trend analysis
- `ping_latency_comprehensive_analysis_{direction}_{bandwidth}M.png`: Individual detailed analysis for each bandwidth configuration with enhanced professional theming
- Enhanced statistical summaries with professional color schemes suitable for academic papers
- **Professional Theme**: Consistent color palette with no outliers displayed for cleaner visualizations
- **Enhanced Readability**: Professional background styling for all statistical annotations and value labels

## 3. Updated Analysis Workflow

The improved analysis workflow now separates different metrics into individual scripts:

1. **Data Collection**: Run tests using `main.sh`
2. **Data Cleaning**: Use `clean_iperf_json.py` if needed
3. **Individual Analysis**:
   ```bash
   python3 scripts/analyze_throughput.py
   python3 scripts/analyze_packet_loss.py
   python3 scripts/analyze_jitter.py
   python3 scripts/analyze_cpu_utilization.py
   python3 scripts/analyze_packet_count.py
   ```
4. **Comprehensive Analysis**: Use `network_analysis.py` for overall performance
5. **Log Analysis**: Use `Measure/analyze_logs.py` for VNF-PNF timing
6. **Comparison**: Use `Measure/compare_latency.py` for deployment model comparison

## 4. Output Organization

Each analysis script creates its own output directory structure with enhanced organization under `Analysis/analysis-<folder_name>/`:
```
Analysis/
└── analysis-20250528-nFAPI(100-500M)/
    ├── throughput_analysis/
    │   └── throughput_comparison.png
    ├── packet_loss_analysis/
    │   └── ue_packet_loss_analysis.png
    ├── jitter_analysis/
    │   └── ue_jitter_analysis.png
    ├── cpu_analysis/
    │   ├── cpu_total_utilization_stacked_comparison.png
    │   ├── cn_cpu_user_vs_system.png
    │   ├── ue_cpu_user_vs_system.png
    │   └── cpu_utilization_enhanced_summary_table.png
    ├── packet_count_analysis/
    │   └── packet_count_comparison.png
    ├── ping_latency/
    │   ├── ping_latency_raw_distribution_dl.png
    │   ├── ping_latency_core_performance_dl.png
    │   ├── ping_latency_quartile_boxplot_dl.png
    │   ├── ping_latency_q2q3_analysis_dl.png
    │   ├── ping_latency_outlier_analysis_dl.png
    │   ├── ping_latency_statistical_summary_dl.png
    │   ├── ping_latency_trend_analysis_dl.png
    │   └── [similar files for ul direction]
    └── network_analysis/
        └── comprehensive_analysis_results.png
```

This organization makes it easy to find specific types of analysis and ensures each metric gets proper attention and visualization.

## Orchestrated Python Workflow (run_analysis.py)

- Modular collectors (SSH/ADB):
  - iperf3 server on CN with JSON logging and start timestamp
  - UE iperf3 client JSON capture
  - CN→UE ping with per-line epoch timestamps
  - mpstat CPU sampling on CN, gNB (Monolithic), VNF/PNF (NFAPI), fetched as logs
- Independent analyses (no cross-script dependency):
  - Throughput comparison: CN sent vs UE received; efficiency annotation
  - Packet count comparison: CN Tx vs UE Rx
  - Loss rate: merged CN vs UE bars with trends
  - Ping latency: box plots with Q2 trend and throughput background bars
  - CPU utilization: uses iperf JSON CPU if present; otherwise falls back to mpstat logs
- Each figure is self-contained and labeled for paper-quality presentation

Usage:
```bash
# Collect + analyze
python3 run_analysis.py --collect --mode Monolithic --dl 100:500:100 --duration 15

# Analyze only
python3 run_analysis.py --data ./data/20250101-NFAPI(100-500M)-15sec-12
```

Notes:
- mpstat logs are named: cpu-<role>-<direction>-<proto>-<bw>M.log (roles: cn, gnb, vnf, pnf)
- Loss/throughput/ping files follow iperf-*, ping-* patterns already supported by scripts
