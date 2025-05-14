import re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse
import matplotlib
from datetime import datetime
import os
import sys

# Remove font settings that reference unavailable fonts
# We're using English labels now, so DejaVu Sans will work fine
matplotlib.rcParams['font.family'] = ['DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False  # Correctly display minus sign

# 解析命令行參數 - 修改為接受兩個文件路徑
parser = argparse.ArgumentParser(description='分析 VNF/PNF 時間戳記錄')
parser.add_argument('vnf_file_path', type=str, help='VNF日誌檔案的路徑')
parser.add_argument('pnf_file_path', type=str, help='PNF日誌檔案的路徑')
args = parser.parse_args()

# 讀取VNF檔案內容
try:
    with open(args.vnf_file_path, 'r') as file:
        vnf_lines = file.readlines()
except FileNotFoundError:
    print(f"錯誤: 找不到VNF檔案 '{args.vnf_file_path}'")
    exit(1)
except Exception as e:
    print(f"錯誤: 讀取VNF檔案時發生問題: {e}")
    exit(1)

# 讀取PNF檔案內容
try:
    with open(args.pnf_file_path, 'r') as file:
        pnf_lines = file.readlines()
except FileNotFoundError:
    print(f"錯誤: 找不到PNF檔案 '{args.pnf_file_path}'")
    exit(1)
except Exception as e:
    print(f"錯誤: 讀取PNF檔案時發生問題: {e}")
    exit(1)

# 解析每行資料，格式為: [timestamp] frame=x slot=y
pattern = re.compile(r"\[(\d+\.\d+)\] frame=(\d+) slot=(\d+)")

# 解析VNF數據
vnf_data = {}
vnf_entries = []  # Store all entries for debugging
for line in vnf_lines:
    match = pattern.search(line.strip())
    if match:
        timestamp = float(match.group(1))
        frame = int(match.group(2))
        slot = int(match.group(3))
        vnf_entries.append((timestamp, frame, slot))
        
        # 計算在循環內的相對位置
        frame_mod = frame % 1024
        slot_mod = slot % 20
        
        key = (frame_mod, slot_mod)
        vnf_data[key] = timestamp

# 解析PNF數據
pnf_data = {}
pnf_entries = []  # Store all entries for debugging
for line in pnf_lines:
    match = pattern.search(line.strip())
    if match:
        timestamp = float(match.group(1))
        frame = int(match.group(2))
        slot = int(match.group(3))
        pnf_entries.append((timestamp, frame, slot))
        
        # 計算在循環內的相對位置
        frame_mod = frame % 1024
        slot_mod = slot % 20
        
        key = (frame_mod, slot_mod)
        pnf_data[key] = timestamp

# 打印數據點數量用於調試
print(f"找到 VNF 數據點: {len(vnf_data)}")
print(f"找到 PNF 數據點: {len(pnf_data)}")

# 獲取兩個文件的第一個條目來計算偏移量
vnf_first_entry = None
pnf_first_entry = None

# 確保有數據可用
if vnf_entries:
    _, frame, slot = vnf_entries[0]
    vnf_first_entry = {'frame': frame, 'slot': slot}
    print(f"VNF 第一條記錄: frame={frame}, slot={slot}")

if pnf_entries:
    _, frame, slot = pnf_entries[0]
    pnf_first_entry = {'frame': frame, 'slot': slot}
    print(f"PNF 第一條記錄: frame={frame}, slot={slot}")

# 計算偏移量 - 修正以處理循環邊界
if vnf_first_entry and pnf_first_entry:
    # 將frame和slot轉換為絕對位置（總slot數）
    total_slots_per_cycle = 1024 * 20  # frame循環 * slot循環
    
    vnf_absolute_slot = (vnf_first_entry['frame'] * 20 + vnf_first_entry['slot'])
    pnf_absolute_slot = (pnf_first_entry['frame'] * 20 + pnf_first_entry['slot'])
    
    # 計算絕對差異，考慮可能的環繞
    absolute_diff = (vnf_absolute_slot - pnf_absolute_slot) % total_slots_per_cycle
    
    # 轉換回frame和slot
    frame_shift = absolute_diff // 20
    slot_shift = absolute_diff % 20
    
    print(f"VNF 絕對位置: {vnf_absolute_slot} slots")
    print(f"PNF 絕對位置: {pnf_absolute_slot} slots")
    print(f"絕對差異: {absolute_diff} slots")
    print(f"計算出的偏移量: frame_shift={frame_shift}, slot_shift={slot_shift}")
else:
    print("錯誤: 無法計算偏移量，檔案中可能沒有有效數據")
    print("原始數據:")
    if vnf_entries:
        print(f"VNF 第一條: {vnf_entries[0]}")
    else:
        print("沒有VNF數據")
    
    if pnf_entries:
        print(f"PNF 第一條: {pnf_entries[0]}")
    else:
        print("沒有PNF數據")
    
    if len(sys.argv) > 2:
        print(f"使用的文件: {sys.argv[1]} 和 {sys.argv[2]}")
    
    exit(1)

# 計算VNF - PNF的時間差
differences = []
for key in set(vnf_data.keys()).intersection(set(pnf_data.keys())):
    vnf_timestamp = vnf_data[key]
    pnf_timestamp = pnf_data[key]
    diff = vnf_timestamp - pnf_timestamp
    differences.append({
        'frame': key[0], 
        'slot': key[1], 
        'diff': diff, 
        'timestamp': vnf_timestamp  # 使用VNF時間作為參考時間點
    })

# 將結果整理成DataFrame
df = pd.DataFrame(differences)

# 按照timestamp排序，以時間順序顯示
df = df.sort_values('timestamp')

# 計算統計資訊
stats = df['diff'].describe()
mean_latency = df['diff'].mean()
min_latency = df['diff'].min()
max_latency = df['diff'].max()
median_latency = df['diff'].median()
std_latency = df['diff'].std()

# 將統計資訊輸出到LOG (單位轉為毫秒ms)
log_file = 'latency_analysis.log'
with open(log_file, 'w') as f:
    f.write(f"=== Latency Analysis Report ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===\n\n")
    f.write(f"VNF File: {args.vnf_file_path}\n")
    f.write(f"PNF File: {args.pnf_file_path}\n\n")
    f.write(f"VNF First Entry: frame={vnf_first_entry['frame']}, slot={vnf_first_entry['slot']}\n")
    f.write(f"PNF First Entry: frame={pnf_first_entry['frame']}, slot={pnf_first_entry['slot']}\n")
    f.write(f"Detected Shift: frame_shift={frame_shift}, slot_shift={slot_shift}\n")
    f.write(f"(Absolute difference: {absolute_diff} slots)\n\n")
    f.write("Statistical Analysis:\n")
    f.write(f"- Mean latency: {mean_latency*1000:.4f} ms\n")
    f.write(f"- Median latency: {median_latency*1000:.4f} ms\n")
    f.write(f"- Min latency: {min_latency*1000:.4f} ms\n")
    f.write(f"- Max latency: {max_latency*1000:.4f} ms\n")
    f.write(f"- Standard deviation: {std_latency*1000:.4f} ms\n")
    f.write("\nFull Statistics (in ms):\n")
    f.write(str(stats * 1000))
    
    f.write("\n\nLatency by Slot (Average, in ms):\n")
    slot_avg = df.groupby('slot')['diff'].mean() * 1000
    f.write(str(slot_avg))
    
    f.write("\n\nExtreme Values:\n")
    f.write(f"Highest latency - Frame: {df.loc[df['diff'].idxmax()]['frame']}, ")
    f.write(f"Slot: {df.loc[df['diff'].idxmax()]['slot']}, ")
    f.write(f"Value: {max_latency*1000:.4f} ms\n")
    
    f.write(f"Lowest latency - Frame: {df.loc[df['diff'].idxmin()]['frame']}, ")
    f.write(f"Slot: {df.loc[df['diff'].idxmin()]['slot']}, ")
    f.write(f"Value: {min_latency*1000:.4f} ms\n")

# 顯示統計資訊到控制台 (單位轉為毫秒ms)
print(f"=== Latency Analysis Report ===")
print(f"VNF File: {args.vnf_file_path}")
print(f"PNF File: {args.pnf_file_path}")
print(f"VNF First Entry: frame={vnf_first_entry['frame']}, slot={vnf_first_entry['slot']}")
print(f"PNF First Entry: frame={pnf_first_entry['frame']}, slot={pnf_first_entry['slot']}")
print(f"Detected Shift: frame_shift={frame_shift}, slot_shift={slot_shift} (Absolute: {absolute_diff} slots)")
print(f"Mean: {mean_latency*1000:.4f} ms")
print(f"Median: {median_latency*1000:.4f} ms")
print(f"Min: {min_latency*1000:.4f} ms")
print(f"Max: {max_latency*1000:.4f} ms")
print(f"Std Dev: {std_latency*1000:.4f} ms")
print(f"\nDetailed statistics written to {log_file}")

# 繪製latency隨時間變化的折線圖 (單位轉為毫秒ms)
plt.figure(figsize=(14, 8))

# 創建索引序列作為X軸
x_seq = range(len(df))

# 主圖 - 折線圖顯示latency隨時間變化
plt.plot(x_seq, df['diff'] * 1000, 'b-', linewidth=1, alpha=0.7)
plt.ylabel('Latency (milliseconds)')
plt.xlabel('Measurement Sequence')
plt.title(f'VNF to PNF Latency (Frame Shift: {frame_shift}, Slot Shift: {slot_shift})')
plt.grid(True, alpha=0.3)

# 添加統計資訊標記線
plt.axhline(y=mean_latency * 1000, color='r', linestyle='-', label=f'Mean: {mean_latency*1000:.4f} ms')
plt.axhline(y=median_latency * 1000, color='g', linestyle='--', label=f'Median: {median_latency*1000:.4f} ms')
plt.axhline(y=min_latency * 1000, color='c', linestyle='-.', label=f'Min: {min_latency*1000:.4f} ms')
plt.axhline(y=max_latency * 1000, color='m', linestyle='-.', label=f'Max: {max_latency*1000:.4f} ms')

# 添加標準差範圍
plt.fill_between(x_seq, 
                (mean_latency - std_latency) * 1000,
                (mean_latency + std_latency) * 1000,
                color='gray', alpha=0.2, label=f'Std Dev: {std_latency*1000:.4f} ms')

plt.legend(loc='best')

# 儲存圖表
# Create output filename based on input files
vnf_basename = os.path.splitext(os.path.basename(args.vnf_file_path))[0]
pnf_basename = os.path.splitext(os.path.basename(args.pnf_file_path))[0]
output_file = f'Measure/latency_{vnf_basename}_vs_{pnf_basename}.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.show()

print(f"Graph saved as {output_file}")
