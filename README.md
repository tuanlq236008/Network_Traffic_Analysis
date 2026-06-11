# Network Traffic Analysis: iCloud Private Relay Classification

## 📋 Mô tả Dự án

Dự án này phân tích và phân loại lưu lượng mạng **iCloud Private Relay** bằng các phương pháp học sâu (Deep Learning) trên dữ liệu PCAP. Sử dụng các đặc trưng từ hướng gói tin, thời gian, và metadata để xây dựng mô hình dự đoán có khả năng nhận diện lớp lưu lượng riêu tư với độ chính xác cao.

### 🎯 Mục tiêu Chính

- Phát triển các mô hình học sâu để phân loại lưu lượng iCloud Private Relay
- So sánh hiệu suất giữa các kiến trúc khác nhau (Var-CNN vs Deep Fingerprinting)
- Đánh giá khả năng nhận diện thông qua các chỉ số TPR/FPR
- Xây dựng pipeline đầy đủ từ xử lý dữ liệu PCAP đến đánh giá mô hình

### 🏆 Kết Quả Chính

- **Ensemble Model Accuracy**: 65.50%
- **Length-Metadata Model**: 66.36%
- **Direction-Metadata Model**: 64.36%
- **Time-Metadata Model**: 63.93%

## 🏗️ Kiến Trúc Mô Hình

Dự án hỗ trợ hai kiến trúc chính:

- **`Var-CNN`** – Mô hình ResNet 1D kết hợp đa kênh (Multi-channel):
  - Kênh Direction (Hướng gói tin)
  - Kênh Time (Thời gian giữa các gói)
  - Kênh Metadata (Kích thước gói, cơ chế điều khiển, v.v.)
  - Các kênh kết hợp (Ensemble)

- **`Deep Fingerprinting (DF)`** – Mô hình chỉ sử dụng hướng gói tin để phân loại

## 📊 Workflow

1. **Chuyển đổi PCAP** → Tách dữ liệu từ file PCAP thành dạng `.npz`
2. **Tiền xử lý** → Chuẩn hóa và tạo bộ dữ liệu `.h5`
3. **Huấn luyện** → Đào tạo các mô hình với các cấu hình khác nhau
4. **Đánh giá** → Tính toán các chỉ số hiệu suất (Accuracy, TPR, FPR)
5. **Dự đoán** → Thực hiện dự đoán trên dữ liệu mới

## 🛠️ Công Nghệ & Dependencies

### Framework & Libraries
- **TensorFlow/Keras** – Xây dựng và huấn luyện mô hình học sâu
- **Scikit-learn** – Đánh giá mô hình (metrics, classification reports)
- **NumPy** – Xử lý dữ liệu số
- **H5py** – Lưu trữ dữ liệu HDF5
- **tqdm** – Progress bars
- **tshark** (Wireshark) – Phân tích file PCAP

### Yêu Cầu Hệ Thống

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**requirements.txt**:
```
h5py
tqdm
scikit-learn
tensorflow
keras
```

> **Lưu ý**: Để sử dụng `tshark`, cần cài đặt Wireshark trên hệ thống

## 📁 Cấu Trúc Dự án

### Core Modules

```
src/
├── pcap_to_npz.py           # Chuyển đổi PCAP → NPZ (closed/open world)
├── preprocess_data.py       # Tiền xử lý & chuẩn hóa dữ liệu
├── run_model.py             # Pipeline chính: huấn luyện & đánh giá
├── var_cnn.py               # Kiến trúc Var-CNN (ResNet 1D multi-channel)
├── df.py                    # Kiến trúc Deep Fingerprinting
├── evaluate.py              # Tính metrics (TPR, FPR, accuracy)
├── data_generator.py        # Batch generator (thread-safe)
├── inspect_npz.py           # Kiểm tra & phân tích file NPZ
├── wang_to_varcnn.py        # Chuyển đổi định dạng dữ liệu cũ
└── predic/
    ├── predict_single_pcap.py       # Dự đoán từ file PCAP đơn
    └── verify_test_predictions.py   # Xác minh kết quả dự đoán
```

### Tệp Cấu Hình & Kết Quả

- `config.json` – Cấu hình huấn luyện (batch size, epochs, hyperparameters)
- `job_result.json` – Kết quả đánh giá (accuracy của các mô hình)
- `model_weights.weights.h5` – Trọng số mô hình được lưu trữ

## 🚀 Hướng Dẫn Sử Dụng

### Step 1: Cài Đặt Môi Trường

```bash
# Clone repository
git clone https://github.com/tuanlq236008/Network_Traffic_Analysis.git
cd Network_Traffic_Analysis

# Cài đặt dependencies
pip install -r requirements.txt
```

**Cài đặt tshark (để phân tích PCAP)**:
- **macOS**: `brew install wireshark`
- **Linux**: `sudo apt-get install wireshark`
- **Windows**: Tải Wireshark từ https://www.wireshark.org

### Step 2: Cấu Hình Dự án (config.json)

Tạo file `config.json` tại thư mục gốc với cấu hình sau:

```json
{
  "data_dir": "./data/",
  "predictions_dir": "./predictions/",
  "model_name": "var-cnn",
  "mixture": [
    ["dir"],
    ["time"],
    ["length"],
    ["metadata"],
    ["dir", "time", "metadata"],
    ["dir", "length", "metadata"],
    ["time", "length", "metadata"],
    ["dir", "time", "length", "metadata"]
  ],
  "batch_size": 128,
  "var_cnn_max_epochs": 100,
  "df_epochs": 50,
  "num_mon_sites": 50,
  "num_mon_inst_train": 10,
  "num_mon_inst_test": 5,
  "num_unmon_sites_train": 10,
  "num_unmon_sites_test": 10,
  "seq_length": 5000,
  "inter_time": true,
  "scale_metadata": true,
  "dir_dilations": true,
  "time_dilations": true,
  "var_cnn_base_patience": 5
}
```

> Điều chỉnh các tham số theo bộ dữ liệu và yêu cầu của bạn

### Step 3: Chuyển Đổi Dữ Liệu PCAP

```bash
cd src
python pcap_to_npz.py
```

**Mô tả**: Script này sử dụng `tshark` để giải mã các file PCAP và tạo ra:
- `all_closed_world.npz` – dữ liệu từ các trang web được giám sát
- `all_open_world.npz` – dữ liệu từ các trang web không được giám sát

> **Lưu ý**: Nếu `tshark` không ở đường dẫn mặc định, sửa `TSHARK_PATH` trong `src/pcap_to_npz.py`

### Step 4: Tiền Xử Lý Dữ Liệu

```bash
python preprocess_data.py
```

**Công việc**:
1. Đọc file NPZ từ bước trước
2. Chia dữ liệu thành training/test set (95%/5%)
3. Chuẩn hóa metadata
4. Lưu thành file `.h5`

### Step 5: Huấn Luyện & Đánh Giá Mô Hình

```bash
python run_model.py
```

**Quy trình**:
- Xây dựng các mô hình theo cấu hình `mixture`
- Huấn luyện từng mô hình
- Đánh giá trên test set
- Lưu trọng số tốt nhất
- Ghi kết quả vào `job_result.json`

### Step 6: Dự Đoán trên Dữ Liệu Mới

```bash
cd predic
python predict_single_pcap.py --pcap <đường_dẫn_file.pcap>
```

### Step 7: Xác Minh Kết Quả

```bash
python verify_test_predictions.py
```

## 📈 Kết Quả & Hiệu Suất

Mô hình ensemble đạt được **65.50% accuracy** trên tập test, so sánh:

| Model | Accuracy |
|-------|----------|
| Direction + Metadata | 64.36% |
| Length + Metadata | 66.36% |
| Time + Metadata | 63.93% |
| **Ensemble** | **65.50%** |

## 🔍 Phân Tích Chi Tiết

### Các Đặc Trưng Chính (Features)

1. **Direction (Hướng Gói Tin)**
   - Xác định hướng của mỗi gói (upstream/downstream)
   - Chuỗi direction có độ dài cố định (5000 gói)

2. **Inter-Arrival Time (Thời Gian Giữa Các Gói)**
   - Khoảng thời gian giữa các gói liên tiếp
   - Chuẩn hóa để loại bỏ các biến động vô ý

3. **Packet Size (Kích Thước Gói) & Metadata**
   - Kích thước payload của mỗi gói
   - Các thông tin khác như TCP flags, window size

### Kiến Trúc ResNet 1D

Model Var-CNN sử dụng:
- **Conv1D layers** với dilated convolutions
- **Batch Normalization** để ổn định huấn luyện
- **Residual connections** để cải thiện gradient flow
- **Global Average Pooling** để giảm kích thước đầu ra
- **Dropout** để chống overfitting

## 🐛 Xử Lý Sự Cố

### Lỗi: "tshark not found"
```bash
# macOS
brew install wireshark

# Linux (Debian/Ubuntu)
sudo apt-get install wireshark

# Xác minh
which tshark
tshark --version
```

### Lỗi: "Module not found"
```bash
# Cập nhật pip
python -m pip install --upgrade pip

# Cài lại dependencies
pip install -r requirements.txt --force-reinstall
```

### Lỗi: "Out of Memory" khi huấn luyện
- Giảm `batch_size` trong `config.json`
- Giảm `seq_length` (độ dài chuỗi gói)
- Giảm số lượng mô hình trong `mixture`

### Lỗi: Dữ liệu PCAP không được xử lý đúng
- Kiểm tra định dạng file: `file data/*.pcap`
- Kiểm tra nội dung: `python src/inspect_npz.py`
- Đảm bảo file PCAP có chứa dữ liệu hợp lệ

## 📚 Tham Khảo & Nguồn

### Các Nghiên Cứu Liên Quan

- **Deep Fingerprinting**: Phương pháp phân loại lưu lượng dựa trên chuỗi hướng gói
- **Var-CNN**: Mô hình multi-channel kết hợp nhiều loại đặc trưng
- **Website Fingerprinting**: Kỹ thuật xác định trang web từ lưu lượng mạng

### Dataset

- Dữ liệu thu thập từ các trang web được giám sát (monitored sites)
- Dữ liệu open-world từ các trang web ngẫu nhiên
- Định dạng: File PCAP → NPZ → HDF5

## 🤝 Đóng Góp

Chào mừng các đóng góp! Nếu bạn tìm thấy lỗi hoặc có gợi ý cải tiến:

1. Fork repository
2. Tạo branch tính năng: `git checkout -b feature/YourFeature`
3. Commit thay đổi: `git commit -m 'Add YourFeature'`
4. Push lên branch: `git push origin feature/YourFeature`
5. Mở Pull Request

## 📝 License

Dự án này có giấy phép theo MIT License. Xem file LICENSE để biết chi tiết.

## 👤 Tác Giả

- **Tuấn Lê** - [GitHub](https://github.com/tuanlq236008)

## 📧 Liên Hệ

Nếu bạn có bất kỳ câu hỏi, vui lòng tạo Issue hoặc liên hệ qua GitHub.

---

**Cập nhật lần cuối**: Tháng 6 năm 2024 