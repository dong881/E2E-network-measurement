import matplotlib.pyplot as plt
from collections import Counter

def calculate_packet_loss_rate(input_text):
    # 從輸入文本中提取封包日誌
    packet_logs = []
    for line in input_text.strip().split('\n'):
        if "[MAC]   VNF SFN/Slot" in line:
            packet_logs.append(line)
    
    # 提取 SFN/Slot 資訊
    packets = []
    for log in packet_logs:
        if "SFN/Slot" in log:
            # 從日誌中提取 SFN 和 Slot 數值
            sfn_slot = log.split("SFN/Slot")[1].strip()
            sfn, slot = map(int, sfn_slot.split('.'))
            packets.append((sfn, slot))
    
    # 如果沒有有效封包，返回錯誤訊息
    if not packets:
        return {"錯誤": "未找到有效的封包資訊"}
    
    # 將封包按 SFN 和 Slot 排序
    packets.sort()
    
    # 找出最小和最大的 SFN 和 Slot
    min_sfn, min_slot = packets[0]
    max_sfn, max_slot = packets[-1]
    
    # 建立一個集合來存儲實際收到的封包位置
    received_packets = set((sfn, slot) for sfn, slot in packets)
    
    # 計算理論上應該收到的所有封包位置
    expected_packets = set()
    current_sfn = min_sfn
    current_slot = min_slot
    
    while (current_sfn < max_sfn) or (current_sfn == max_sfn and current_slot <= max_slot):
        expected_packets.add((current_sfn, current_slot))
        
        # Slot 在 0~19 之間循環
        current_slot += 1
        if current_slot > 19:
            current_slot = 0
            current_sfn += 1
    
    # 找出丟失的封包
    lost_packets = expected_packets - received_packets
    
    # 計算掉包率
    expected_packet_count = len(expected_packets)
    actual_packet_count = len(received_packets)
    lost_packet_count = len(lost_packets)
    packet_loss_rate = lost_packet_count / expected_packet_count if expected_packet_count > 0 else 0
    
    # 計算連續掉包的情況
    consecutive_losses = find_consecutive_losses(lost_packets)
    
    return {
        "掉包率": packet_loss_rate,
        "掉包數量": lost_packet_count,
        "預期封包數": expected_packet_count,
        "實際封包數": actual_packet_count,
        "最小 SFN/Slot": f"{min_sfn}.{min_slot}",
        "最大 SFN/Slot": f"{max_sfn}.{max_slot}",
        "丟失的封包數量": len(lost_packets),
        "最長連續掉包": max(consecutive_losses) if consecutive_losses else 0,
        "連續掉包分布": consecutive_losses
    }

def find_consecutive_losses(lost_packets):
    """找出連續掉包的長度分布"""
    if not lost_packets:
        return []
    
    # 將丟失的封包轉換為列表並排序
    lost_list = sorted(list(lost_packets))
    
    # 計算連續掉包的長度
    consecutive_lengths = []
    current_length = 1
    
    for i in range(1, len(lost_list)):
        prev_sfn, prev_slot = lost_list[i-1]
        curr_sfn, curr_slot = lost_list[i]
        
        # 計算下一個預期的封包
        next_slot = prev_slot + 1
        next_sfn = prev_sfn
        if next_slot > 19:
            next_slot = 0
            next_sfn += 1
        
        # 檢查是否連續
        if next_sfn == curr_sfn and next_slot == curr_slot:
            current_length += 1
        else:
            consecutive_lengths.append(current_length)
            current_length = 1
    
    consecutive_lengths.append(current_length)
    return consecutive_lengths

def plot_consecutive_loss_distribution(consecutive_losses):
    """繪製連續掉包長度分布統計圖"""
    if not consecutive_losses:
        print("沒有連續掉包資料可供繪圖。")
        return
    
    # 統計連續掉包長度的頻率
    counter = Counter(consecutive_losses)
    lengths = list(counter.keys())
    frequencies = list(counter.values())
    
    # 繪製長條圖
    plt.figure(figsize=(12, 9))
    plt.bar(lengths, frequencies, color='skyblue')
    plt.xlabel('連續掉包長度')
    plt.ylabel('頻率')
    plt.title('連續掉包長度分布統計')
    plt.xticks(lengths)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.show()

def main():
    print("請輸入日誌內容（輸入'END'單獨一行來結束輸入）：")
    input_lines = []
    
    while True:
        line = input()
        if line.strip() == "END":
            break
        input_lines.append(line)
    
    input_text = '\n'.join(input_lines)
    
    result = calculate_packet_loss_rate(input_text)
    
    # 輸出結果
    for key, value in result.items():
        if key == "掉包率":
            print(f"{key}: {value:.2%}")
        elif key == "連續掉包分布":
            # 繪製連續掉包分布圖
            plot_consecutive_loss_distribution(value)
        else:
            print(f"{key}: {value}")

if __name__ == "__main__":
    main()
