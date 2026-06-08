import numpy as np

# Đọc file npz
data = np.load('data/all_closed_world.npz')

# Lấy các mảng dữ liệu ra
dir_seq = data['dir_seq']
time_seq = data['time_seq']
length_seq = data['length_seq']
metadata = data['metadata']
labels = data['labels']

print("=== THỐNG KÊ CHUNG BỘ DỮ LIỆU ===")
print(f"Tổng số mẫu (PCAP files): {len(labels)}")
print(f"Kích thước mảng Hướng (dir_seq): {dir_seq.shape}")
print(f"Kích thước mảng Thời gian (time_seq): {time_seq.shape}")
print(f"Kích thước mảng Độ dài gói tin (length_seq): {length_seq.shape}")
print(f"Kích thước mảng Metadata: {metadata.shape}")

# In chi tiết mẫu dữ liệu đầu tiên (Index 0) để kiểm tra
print("\n=== KIỂM TRA MẪU ĐẦU TIÊN (INDEX 0) ===")
print(f"Nhãn (Label): {labels[0]}")
print(f"Metadata (7 thông số): {metadata[0]}")
print(f"Chuỗi hướng (20 gói tin đầu tiên): {dir_seq[0][:20]}")
print(f"Chuỗi thời gian (20 gói tin đầu tiên): {time_seq[0][:20]}")
print(f"Chuỗi độ dài (20 gói tin đầu tiên): {length_seq[0][:20]}")

print("\n=== CÁCH ĐỐI CHIẾU VỚI WIRESHARK ===")
print("1. Mở file PCAP đầu tiên của lớp mạng (Label) này bằng Wireshark.")
print("2. Cột Time trong Wireshark sẽ tương ứng với 'Chuỗi thời gian'.")
print("3. Địa chỉ IP Nguồn (Source IP):")
print("   - Nếu IP nguồn trùng với IP của máy Client -> Gói tin gửi đi (Hướng +1)")
print("   - Nếu IP nguồn là của Server -> Gói tin nhận về (Hướng -1)")
print("4. Cột Length trong Wireshark sẽ tương ứng với 'Chuỗi độ dài'.")
