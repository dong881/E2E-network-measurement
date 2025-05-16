import re
import matplotlib.pyplot as plt
import numpy as np
import os

# Function to parse report files
def parse_report(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Extract deployment model name from filename
    filename = os.path.basename(file_path)
    if 'monolithic' in filename.lower():
        model_name = 'Monolithic'
    elif '[rawSocket]' in filename:
        model_name = 'NFAPI (Raw Socket)'
    elif '[Socket]' in filename:
        model_name = 'NFAPI (Socket)'
    elif 'nfapi' in filename.lower():
        model_name = 'NFAPI'
    else:
        model_name = filename.replace('_report.txt', '')
    
    # Extract statistics using regex
    mean = float(re.search(r'Mean latency: ([\d.]+) ms', content).group(1))
    median = float(re.search(r'Median latency: ([\d.]+) ms', content).group(1))
    min_val = float(re.search(r'Min latency: ([\d.]+) ms', content).group(1))
    max_val = float(re.search(r'Max latency: ([\d.]+) ms', content).group(1))
    std_dev = float(re.search(r'Standard deviation: ([\d.]+) ms', content).group(1))
    
    return {
        'name': model_name,
        'mean': mean,
        'median': median,
        'min': min_val,
        'max': max_val,
        'std_dev': std_dev
    }

# Paths to the report files
report_files = [
    '/home/ming/E2E-network-measurement/Measure/result/monolithic-VNF_vs_monolithic-PNF_report.txt',
    '/home/ming/E2E-network-measurement/Measure/result/[rawSocket] nfapi-VNF_vs_nfapi-PNF_report.txt',
    '/home/ming/E2E-network-measurement/Measure/result/[Socket] nfapi-VNF_vs_nfapi-PNF_report.txt'
]

# Parse the reports
reports = [parse_report(file) for file in report_files]

# Create a figure for the comparison
plt.figure(figsize=(16, 14))

# 1. Bar chart comparing all metrics
plt.subplot(2, 2, 1)
bar_width = 0.25  # Narrower bars to fit three models
index = np.arange(5)
metrics = ['mean', 'median', 'min', 'max', 'std_dev']
metric_labels = ['Mean', 'Median', 'Min', 'Max', 'Std Dev']
colors = ['green', 'orange', 'blue']

for i, report in enumerate(reports):
    values = [report[metric] for metric in metrics]
    plt.bar(index + i*bar_width, values, bar_width, label=report['name'], color=colors[i])

plt.xlabel('Metrics')
plt.ylabel('Latency (ms)')
plt.title('Comparison of All Latency Metrics')
plt.xticks(index + bar_width, metric_labels)
plt.legend()

# 2. Log scale comparison for better visibility
plt.subplot(2, 2, 2)
for i, report in enumerate(reports):
    values = [report[metric] for metric in metrics]
    plt.bar(index + i*bar_width, values, bar_width, label=report['name'], color=colors[i])

plt.xlabel('Metrics')
plt.ylabel('Latency (ms) - Log Scale')
plt.title('Comparison of All Latency Metrics (Log Scale)')
plt.xticks(index + bar_width, metric_labels)
plt.yscale('log')
plt.legend()

# 3. Latency Comparison Bar Chart (Means only)
plt.subplot(2, 1, 2)
names = [report['name'] for report in reports]
means = [report['mean'] for report in reports]

# More comprehensive comparison for three models
min_latency_index = np.argmin(means)
max_latency_index = np.argmax(means)
min_model = names[min_latency_index]
max_model = names[max_latency_index]
improvement = (means[max_latency_index] / means[min_latency_index] - 1) * 100
comparison_text = f"{min_model} has the lowest latency\n{max_model} is {improvement:.1f}% higher than {min_model}"

plt.bar(names, means, color=colors[:len(names)])
plt.xlabel('Deployment Model')
plt.ylabel('Mean Latency (ms)')
plt.title(f'Mean Latency Comparison\n{comparison_text}')

# Add value labels on top of each bar
for i, v in enumerate(means):
    plt.text(i, v + max(means)*0.05, f"{v:.6f} ms", ha='center')

# Add pairwise comparison table
comparison_text = []
for i in range(len(names)):
    for j in range(i+1, len(names)):
        if means[i] > means[j]:
            pct_diff = (means[i] / means[j] - 1) * 100
            comparison_text.append(f"{names[i]} is {pct_diff:.1f}% higher than {names[j]}")
        else:
            pct_diff = (means[j] / means[i] - 1) * 100
            comparison_text.append(f"{names[j]} is {pct_diff:.1f}% higher than {names[i]}")

plt.figtext(0.5, 0.25, "\n".join(comparison_text), ha='center', bbox=dict(facecolor='white', alpha=0.5))

plt.tight_layout()

# Save the plot
output_path = '/home/ming/E2E-network-measurement/Measure/result/latency_comparison.png'
plt.savefig(output_path, dpi=300)

# Also create a table summary
fig, ax = plt.subplots(figsize=(12, 4))
ax.axis('off')
ax.axis('tight')

# Create the table data
table_data = []
for report in reports:
    row = [
        report['name'],
        f"{report['mean']:.6f}",
        f"{report['median']:.6f}",
        f"{report['min']:.6f}",
        f"{report['max']:.6f}",
        f"{report['std_dev']:.6f}"
    ]
    table_data.append(row)

table = ax.table(
    cellText=table_data,
    colLabels=['Deployment', 'Mean (ms)', 'Median (ms)', 'Min (ms)', 'Max (ms)', 'Std Dev (ms)'],
    loc='center',
    cellLoc='center'
)

table.auto_set_font_size(False)
table.set_fontsize(12)
table.scale(1.2, 2)

# Save the table
table_path = '/home/ming/E2E-network-measurement/Measure/result/latency_table.png'
plt.savefig(table_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"Comparison plot saved to: {output_path}")
print(f"Summary table saved to: {table_path}")
