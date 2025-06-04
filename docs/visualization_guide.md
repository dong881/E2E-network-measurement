# Understanding Network Analysis Visualizations

This guide explains how to interpret the various charts and visualizations produced by the network analysis scripts. All visualizations feature enhanced styling with professional value labels and improved readability.

## Enhanced Visualization Features

All plots now include:
- **Professional value labels**: Clear, readable labels with background boxes for better visibility
- **Enhanced styling**: Professional color schemes with consistent theming across all visualizations matching throughput_comparison
- **Better positioning**: Smart label positioning to avoid overlaps and layout issues
- **Consistent formatting**: Standardized styling with professional color palette (#2E86AB, #A23B72, #F8E71C)
- **High-resolution output**: 300 DPI for publication-quality images
- **No outliers display**: Clean visualizations without outlier points for better readability
- **Professional color theme**: Consistent use of throughput_comparison colors: Blue (#2E86AB), Pink (#A23B72), and Yellow (#F8E71C)
- **Meaningful color coding**: Colors represent data categories with logical progression and contrast

## 1. Ping Latency Analysis Plots

### 1.1 Raw Data Distribution
**Filename**: `ping_latency_raw_distribution_<direction>.png`

Complete data distribution with professional styling:
- **X-axis**: Bandwidth configurations in Mbps
- **Y-axis**: Ping latency in milliseconds
- **Features**: All data points included with no outliers displayed for cleaner visualization
- **Color scheme**: Professional blue gradient (#1565C0 to #64B5F6) with enhanced contrast
- **Enhanced features**: Professional statistical summary boxes with consistent theming

### 1.2 Core Performance Analysis  
**Filename**: `ping_latency_core_performance_<direction>.png`

Focuses on Q2-Q3 range with professional green theming:
- **Purpose**: Shows typical performance without outlier influence
- **Color scheme**: Professional green gradient (#1B5E20 to #A5D6A7) for stability indication
- **Use case**: Better for understanding normal operating conditions
- **Enhanced features**: Professional value labels with color-coordinated backgrounds
- **No outliers**: Clean visualization focusing on core performance data

### 1.3 Comprehensive Analysis
**Filename**: `ping_latency_comprehensive_analysis_<direction>.png`

Enhanced professional styling with comprehensive analysis:
- **Focus**: Complete statistical analysis with professional annotations
- **Color scheme**: Consistent professional theme with blue and green accents
- **Purpose**: Publication-ready analysis suitable for academic presentations
- **Enhanced features**: Professional background styling for all statistical elements
- **Clean design**: No outliers displayed for optimal readability

### 1.4 Quartile Box Plot
**Filename**: `ping_latency_quartile_boxplot_<direction>.png`

Traditional statistical box plot with quartile analysis:
- **Box components**: Q1 (25th percentile), median (Q2), Q3 (75th percentile)  
- **Whiskers**: Min/max values within 1.5×IQR
- **Color gradient**: Professional blue gradient representing different bandwidth levels
- **Features**: Automatically saved with high DPI (300) for publication quality
- **Purpose**: Statistical distribution analysis with quartile boundaries clearly marked
- **Enhanced features**: Comprehensive statistical annotations with professional styling

### 1.5 Q2-Q3 Range Analysis
**Filename**: `ping_latency_q2q3_analysis_<direction>.png`

Detailed analysis of the interquartile range (Q2-Q3):
- **Focus**: Core performance without outliers
- **Color scheme**: Green gradient for stability indication
- **Purpose**: Identifies stable performance characteristics
- **Enhanced features**: Enhanced trend analysis with professional value display

### 1.6 Outlier Analysis
**Filename**: `ping_latency_outlier_analysis_<direction>.png`

Shows the percentage of outlier measurements for each bandwidth:
- **Y-axis**: Percentage of measurements that are outliers
- **Definition**: Outliers are values beyond 1.5×IQR from Q1/Q3
- **Purpose**: Identifies bandwidth settings with unstable performance
- **Enhanced features**: Color-coded value labels matching the outlier severity

### 1.7 Statistical Summary Table
**Filename**: `ping_latency_statistical_summary_<direction>.png`

Comprehensive tabular view with key statistics for each bandwidth configuration.
- **Enhanced features**: Professional table styling with improved readability

### 1.8 Trend Analysis
**Filename**: `ping_latency_trend_analysis_<direction>.png`

Line plot showing how latency metrics change with bandwidth:
- **Red line**: Mean latency trend
- **Blue line**: Median (Q2) latency trend
- **Enhanced features**: Statistical summary boxes with professional background styling

## 2. Loss Rate Analysis Plots

### 2.1 Merged Loss Rate Analysis
**Filename**: `merged_loss_rate_analysis.png`

Comprehensive comparison combining bar charts and trend lines:
- **Blue bars/line**: CN (sender) loss rate measurements
- **Red bars/line**: UE (receiver) loss rate measurements
- **Features**: Combined bar and line visualization, precise data values (3 decimal places)
- **Purpose**: Complete sender-receiver comparison with trend identification
- **Layout**: Clean design without overlapping elements for optimal readability
- **Enhanced features**: Professional value labels with color-coordinated backgrounds, streamlined layout for better visibility

### 2.2 UE Packet Loss Analysis
**Filename**: `ue_packet_loss_analysis.png`

Publication-quality analysis of packet loss from receiver (UE) perspective:
- **Blue to Red gradient**: Quality-based color coding (Excellent to Critical)
- **Quality categories**: Six distinct quality levels with specific loss rate ranges
- **Bar chart**: Shows packet loss percentage for each bandwidth configuration
- **Trend line**: Overlaid line showing loss rate trends across bandwidths
- **Value labels**: Precise loss rate values (2 decimal places) with quality categories
- **Features**: Professional styling suitable for academic presentations
- **Purpose**: Receiver-side packet loss analysis with quality assessment
- **Enhanced features**: Color-coordinated value labels with matching background boxes for optimal visibility

**Quality Categories**:
- **Excellent (0%)**: Sea Green - Perfect transmission
- **Very Good (≤0.1%)**: Lime Green - Excellent quality
- **Good (≤0.5%)**: Gold - Good quality  
- **Acceptable (≤1.0%)**: Dark Orange - Acceptable for most applications
- **Poor (≤3.0%)**: Orange Red - Degraded performance
- **Critical (>3.0%)**: Crimson - Severe packet loss issues

### 2.3 VNF Packet Loss Analysis
**Filename**: `vnf_packet_loss_analysis.png`

Analyzes packet loss between VNF and PNF components:
- **Pie chart**: Distribution of received vs lost packets
- **Bar chart**: Absolute numbers of sent, received, and lost packets
- **Features**: Interactive data folder selection, SFN/Slot analysis
- **Purpose**: Component-level packet loss analysis for network debugging
- **Enhanced features**: Professional value labels with background styling for improved readability

### 2.4 Consecutive Loss Distribution
**Filename**: Generated during SFN/Slot analysis

Shows distribution of consecutive packet losses:
- **X-axis**: Length of consecutive packet loss (number of packets)
- **Y-axis**: Frequency of occurrence
- **Purpose**: Identifies patterns in packet loss behavior
- **Enhanced features**: Statistical annotations with professional background styling

## 3. CPU Utilization Analysis Plots

### 3.1 Total CPU Utilization Comparison
**Filename**: `cpu_total_utilization_comparison.png`

Compares total CPU usage between CN and UE across different bandwidths:
- **Blue bars**: CN CPU utilization (host_total from CN data)
- **Red bars**: UE CPU utilization (host_total from UE data)
- **Note**: Each device reports its own host CPU usage
- **Enhanced features**: Professional value labels with color-coordinated backgrounds

### 3.2 UE CPU: User vs System  
**Filename**: `ue_cpu_user_vs_system.png`

Shows the breakdown of UE CPU usage:
- **Orange bars**: UE user space CPU utilization
- **Red bars**: UE system space CPU utilization
- **Purpose**: Identifies whether CPU load is from user applications or system processes
- **Enhanced features**: Enhanced value display with professional background styling

### 3.3 CPU Utilization Summary Table
**Filename**: `cpu_utilization_summary_table.png`

Comprehensive tabular summary of all CPU metrics including:
- **CN Total CPU**: Overall CPU utilization on CN device
- **CN User CPU**: CN user space CPU utilization  
- **CN System CPU**: CN system space CPU utilization
- **UE Total CPU**: Overall CPU utilization on UE device
- **UE User CPU**: UE user space CPU utilization
- **UE System CPU**: UE system space CPU utilization

This table provides a complete breakdown of CPU usage patterns for both sender (CN) and receiver (UE) devices across all bandwidth configurations.
- **Enhanced features**: Professional table layout with improved typography and color scheme

## 4. Latency Comparison Plots (Deployment Models)

### 4.1 Latency Metrics Comparison
**Filename**: `latency_metrics_comparison.png`

Bar chart comparing all latency metrics across deployment models in normal scale.
- **Enhanced features**: Professional value labels with deployment-specific color coding

### 4.2 Latency Metrics Comparison (Log Scale)
**Filename**: `latency_metrics_comparison_log.png`

Same comparison but with logarithmic y-axis for better visibility of small differences.
- **Enhanced features**: Improved label positioning for log scale visualization

### 4.3 Mean Latency Comparison
**Filename**: `mean_latency_comparison.png`

Focused comparison of mean latency with percentage difference annotations.
- **Enhanced features**: Professional value labels with color-coordinated backgrounds matching deployment models

### 4.4 Latency Summary Table
**Filename**: `latency_summary_table.png`

Comprehensive table with all latency statistics for each deployment model.
- **Enhanced features**: Professional table styling with improved readability and color scheme

## 5. VNF vs PNF Analysis Plots

Generated by `Measure/analyze_logs.py`:

### 5.1 Raw Timestamp Differences
**Filename**: `*_VNF_vs_*_PNF_plot.png`

Shows raw timestamp differences between VNF and PNF logs.
- **Enhanced features**: Statistical summary box with professional background styling

### 5.2 Filtered Timestamp Differences  
**Filename**: `*_VNF_vs_*_PNF_filtered_plot.png`

Same data with outliers removed for clearer trend visibility.
- **Enhanced features**: Enhanced statistical annotations and improved trend visualization

### 5.3 Statistical Box Plot
**Filename**: `*_VNF_vs_*_PNF_box_plot.png`

Box plot showing the statistical distribution of timestamp differences.
- **Enhanced features**: Professional component annotations with background styling

## Key Improvements in Enhanced Plot Generation

1. **Professional Value Labels**: All plots feature value labels with professional background styling
2. **Consistent Professional Color Theme**: Unified color palette using professional blues, reds, and greens
3. **No Outliers Display**: All visualizations exclude outlier points for cleaner, more readable charts
4. **Enhanced Typography**: Improved font sizing, weighting, and professional styling
5. **Professional Statistical Annotations**: Statistical summary boxes with consistent background theming
6. **High-Resolution Output**: All plots saved at 300 DPI for publication quality
7. **Better Error Handling**: Enhanced error handling in data parsing and visualization generation
8. **Improved Professional Aesthetics**: Better contrast, readability, and professional appearance

## Data Source Corrections

The loss rate analysis now correctly uses:
- **Primary source**: `end.sum.lost_percent` from iPerf JSON output
- **Verification**: Manual calculation from packet counts
- **Separate metrics**: CN (sender) vs UE (receiver) perspectives
- **Comprehensive analysis**: Multiple visualization approaches for complete understanding

This ensures accurate loss rate measurements and provides multiple perspectives on packet loss behavior across different bandwidth configurations.
