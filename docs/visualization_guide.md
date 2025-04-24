# Understanding Network Analysis Visualizations

This guide explains how to interpret the various charts and visualizations produced by the network analysis script.

## 1. Ping Latency Summary Plot

**Filename**: `ping_latency_<direction>_udp.png`

![Ping Latency Summary Plot](../assets/ping_latency_example.png)

This bar chart displays ping latency statistics across different target throughput values:

- **X-axis**: Target throughput values in Mbps
- **Y-axis**: Ping latency in milliseconds
- **Blue sections**: Range from minimum to average ping latency
- **Red sections**: Range from average to maximum ping latency
- **Black line with dots**: Average ping latency
- **Text labels**: Actual values for minimum, average, and maximum latency

**Interpretation**: 
- Look for upward trends as throughput increases, which indicate increased latency under load
- Note any sudden spikes in maximum latency, which may indicate network instability at certain bandwidths
- Compare downlink vs. uplink patterns to understand asymmetric performance characteristics

## 2. Limited Range Ping Latency Plot (100ms)

**Filename**: `ping_latency_<direction>_udp-max100ms.png`

![Limited Range Ping Latency Plot](../assets/ping_latency_max100ms_example.png)

This is a modified version of the summary plot with the y-axis limited to 100ms:

- **Y-axis limit**: Fixed at 100ms for better visibility of lower latency values
- **Values exceeding 100ms**: Displayed with upward arrows (↑) and exact values in small boxes
- **Color coding**: Blue boxes for minimum values, black for average, red for maximum

**Interpretation**:
- Provides better resolution for comparing latency in the normal operating range (under 100ms)
- Clearly indicates when values exceed the "good performance" threshold
- Helps identify subtle patterns that might be obscured in the full-scale plot

## 3. Detailed Test Results Plot

**Filename**: `<direction>_udp_<bandwidth>M_detailed.png`

![Detailed Test Results](../assets/detailed_test_example.png)

This dual-panel plot shows the correlation between ping latency and throughput over time:

**Top Panel (Ping Latency)**:
- **X-axis**: Time in seconds
- **Y-axis**: Ping latency in milliseconds
- **Blue dots**: Test period ping measurements
- **Red dots**: Buffer period ping measurements (excluded from statistics)
- **Vertical red lines**: Test start and end boundaries

**Bottom Panel (Throughput)**:
- **X-axis**: Time in seconds (aligned with top panel)
- **Y-axis**: Throughput in Mbps
- **Blue line**: UE throughput measurements
- **Green line**: CN throughput measurements (uplink mode only)
- **Horizontal red line**: Target throughput
- **Vertical red lines**: Test start and end boundaries

**Interpretation**:
- Observe how ping latency correlates with throughput fluctuations
- Identify any periodic patterns in either metric
- Look for isolated latency spikes and their relationship to throughput drops
- Assess how closely achieved throughput matches the target

## 4. Metrics Comparison Plot

**Filename**: `<direction>_udp_metrics_comparison.png`

![Metrics Comparison](../assets/metrics_comparison_example.png)

This four-panel plot provides comprehensive performance comparisons:

**Top Left (Throughput Comparison)**:
- **X-axis**: Target throughput values
- **Y-axis**: Achieved throughput in Mbps
- **Blue line**: UE throughput
- **Green line**: CN throughput (uplink mode only)
- **Red dashed line**: Target throughput (ideal performance)

**Top Right (Ping Latency vs Throughput)**:
- **X-axis**: Target throughput values
- **Y-axis**: Ping latency in milliseconds
- **Black line**: Average ping latency
- **Gray region**: Range between minimum and maximum ping latency

**Bottom Left (CPU Utilization)**:
- **X-axis**: Target throughput values
- **Y-axis**: CPU utilization percentage
- **Magenta line**: Host CPU utilization
- **Cyan line**: Remote CPU utilization

**Bottom Right (Throughput Efficiency)**:
- **X-axis**: Target throughput values
- **Y-axis**: Efficiency percentage (achieved/target × 100%)
- **Blue bars**: Efficiency percentage
- **Red dashed line**: 100% efficiency mark (ideal performance)
- **Text labels**: Actual efficiency percentage values

**Interpretation**:
- **Throughput Comparison**: Assess how well the achieved throughput tracks the target
- **Ping Latency**: Identify throughput values where latency begins to increase significantly
- **CPU Utilization**: Look for CPU bottlenecks that correlate with performance issues
- **Throughput Efficiency**: Quickly identify which bandwidth settings achieve the highest efficiency

## 5. CSV Comparison Table

**Filename**: `<direction>_udp_comparison.csv`

This CSV file contains all the numeric data used to generate the plots, allowing for further analysis in spreadsheet software.

**Columns**:
- **Target (Mbps)**: Target throughput value
- **UE Avg/Min/Max (Mbps)**: UE throughput statistics
- **CN Avg/Min/Max (Mbps)**: CN throughput statistics (uplink mode only)
- **Ping Avg/Min/Max (ms)**: Ping latency statistics
- **Remote CPU (%)**: UE CPU utilization
- **Host CPU (%)**: CN CPU utilization (uplink mode only)

**Interpretation**:
- Use for detailed numerical analysis
- Create custom visualizations
- Export to reports
- Calculate additional derived metrics

## Key Performance Indicators

When analyzing these visualizations, focus on these key performance indicators:

1. **Throughput Efficiency**: How close the achieved throughput gets to the target
2. **Latency Stability**: Consistency of ping times (small difference between min and max)
3. **Latency vs Throughput Curve**: How quickly latency increases with throughput
4. **CPU Utilization Impact**: Whether performance issues correlate with high CPU usage
5. **Maximum Stable Throughput**: Highest throughput before performance degrades significantly

## Comparing Uplink vs Downlink

The script generates separate sets of visualizations for uplink and downlink tests:

- **Downlink**: Data sent from network to UE (CN → UE)
- **Uplink**: Data sent from UE to network (UE → CN)

When comparing these visualizations, note:

- Uplink typically has lower maximum throughput
- Latency characteristics may differ between directions
- CPU utilization patterns are often asymmetric
- Buffer bloat effects may manifest differently
